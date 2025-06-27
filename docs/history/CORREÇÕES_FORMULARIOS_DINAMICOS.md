# Correções Implementadas para Formulários Dinâmicos

## Problemas Identificados e Soluções

### 1. **Preview não funcionando**

**Problema:** O botão de preview não estava conectado corretamente.
**Solução:**

- Corrigido o ID do botão de `preview_btn` para `toggle_preview` no JavaScript
- A API `/peticionador/api/preview-document` já estava funcionando corretamente

### 2. **Duplicações de campos (orgãos de trânsito aparecendo em múltiplas seções)**

**Problema:** A função `categorize_placeholder_key` não tinha priorização adequada, causando duplicações.
**Solução:**

- **Reestruturação completa da categorização** com sistema de prioridades:
  1. Autoridades de trânsito (primeira prioridade)
  2. Autores numerados (segunda prioridade)
  3. Autores sem numeração
  4. Partes processuais (polo ativo, passivo, terceiros)
  5. Dados do processo
  6. Endereço genérico
  7. Dados do cliente
  8. Outros campos

### 3. **Layout desorganizado**

**Problema:** Template não organizava campos de forma inteligente.
**Solução:**

- **Reorganização completa do template** `formulario_dinamico.html`:
  - Seções condicionais (só aparecem se têm campos)
  - Organização lógica: A1, A2 (autores), B (cliente), C (endereço), D (processo), E (autoridades), etc.
  - Autoridades organizadas dinamicamente por índice
  - Remoção da seção "Outros Dados" duplicada

### 4. **Campos duplicados na seção "Outros Dados"**

**Problema:** Lógica do template estava incluindo campos já categorizados.
**Solução:**

- Nova organização usa apenas `campo_grupos.outros` diretamente
- Eliminação da lógica de exclusão manual no template

## Mudanças Técnicas Detalhadas

### 1. **Função `categorize_placeholder_key()` (app/peticionador/routes.py)**

```python
# ANTES: Sem priorização, causava conflitos
if 'endereco' in chave_lower:
    return 'endereco'

# DEPOIS: Sistema de prioridades claro
# 1. AUTORIDADES DE TRÂNSITO (primeira prioridade)
if chave_lower.startswith('orgao_transito'):
    return 'autoridades'

# 2. AUTORES NUMERADOS (segunda prioridade)
if chave_lower.startswith('autor_') and '_' in chave_lower[6:]:
    # Lógica específica para autores numerados
```

### 2. **Organização dos campos (preencher_formulario_dinamico)**

```python
# ANTES: Lógica confusa com múltiplas verificações
# DEPOIS: Categorização única e organizada
categoria = categorize_placeholder_key(placeholder.chave)
if categoria in campo_grupos:
    campo_grupos[categoria].append(placeholder.chave)
```

### 3. **Template melhorado**

- Seções condicionais: `{% if campo_grupos.autoridades %}`
- Organização dinâmica de autoridades por índice
- Layout limpo e lógico

## Categorias Disponíveis

1. **`autores`** - Autores numerados (autor*1*, autor*2*)
   - Subdivisões: `dados` e `endereco`
2. **`cliente`** - Dados gerais de pessoa
3. **`endereco`** - Endereços genéricos
4. **`processo`** - Dados do processo judicial
5. **`autoridades`** - Órgãos de trânsito
6. **`polo_ativo`** - Requerentes, impetrantes, etc.
7. **`polo_passivo`** - Requeridos, impetrados, etc.
8. **`terceiros`** - Assistentes, MP, etc.
9. **`outros`** - Campos não categorizados

## Teste da Categorização

Execute para verificar:

```bash
python test_categorization.py
```

**Resultado esperado:**

- `autor_1_nome` → `autor_dados`
- `autor_1_endereco_logradouro` → `autor_endereco`
- `orgao_transito_1_nome` → `autoridades`
- `processo_numero` → `processo`
- Sem duplicações!

## Como Aplicar as Correções

1. **Sincronizar placeholders existentes:**

   - Ir para qualquer modelo → Placeholders → "Sincronizar"
   - Isso aplicará a nova categorização automaticamente

2. **Testar o preview:**

   - Abrir um formulário dinâmico
   - Preencher alguns campos
   - Clicar no botão "Preview" - deve funcionar!

3. **Verificar organização:**
   - Os campos devem aparecer organizados em seções lógicas
   - Sem duplicações entre seções
   - Layout mais limpo e intuitivo

## Melhorias Implementadas

✅ **Preview funcionando**
✅ **Eliminação de duplicações**  
✅ **Layout organizado e inteligente**
✅ **Categorização automática melhorada**
✅ **Seções condicionais (só aparecem se necessário)**
✅ **Organização dinâmica de autoridades**
✅ **Sistema de prioridades na categorização**

## Próximos Passos Recomendados

1. Testar em formulários existentes
2. Sincronizar placeholders de modelos importantes
3. Verificar se todos os casos de uso estão cobertos
4. Treinar usuários na nova organização

## ✅ **CORREÇÕES ADICIONAIS IMPLEMENTADAS (Janeiro 2025)**

### **Problema: Endereços de Autoridades no Local Errado**

- **Sintoma:** Campos como `orgao_transito_1_endereco_logradouro` apareciam na seção "B. Endereço"
- **Causa:** Função de categorização permitia que campos de autoridades fossem categorizados como endereço genérico
- **Solução:**
  - ✅ Melhorada a função `categorize_placeholder_key()` com verificação dupla
  - ✅ Adicionada lógica extra na organização dos campos para garantir que TODOS os campos de autoridades fiquem na seção correta
  - ✅ Sistema de verificação e correção automática que move campos de autoridades mal categorizados

### **Problema: Campos de Múltiplos Autores Não Aparecem**

- **Sintoma:** Usuário não conseguia inserir dados do segundo autor
- **Causa:** Detecção de autores numerados limitada e falta de feedback visual
- **Solução:**
  - ✅ Melhorada a regex para detectar autores numerados (`autor_1_`, `autor_2_`, `autor_10_`, etc.)
  - ✅ Adicionado alerta visual quando múltiplos autores são detectados
  - ✅ Indicador de progresso mostrando "X de Y autores"
  - ✅ Ordenação automática dos autores por número

### **Melhorias de Debug e Logging**

- ✅ Logs detalhados da organização dos campos
- ✅ Alertas para campos de autoridades em locais incorretos
- ✅ Contadores de campos por categoria

## Testes de Categorização

### **Autoridades de Trânsito** ✅

```
orgao_transito_1_endereco_logradouro -> autoridades
orgao_transito_1_endereco_cidade     -> autoridades
orgao_transito_2_endereco_cep        -> autoridades
orgao_transito_1_nome                -> autoridades
orgao_transito_2_cnpj                -> autoridades
```

### **Autores Múltiplos** ✅

```
autor_1_nome                         -> autor_dados
autor_1_endereco_logradouro          -> autor_endereco
autor_2_nome                         -> autor_dados
autor_2_cpf                          -> autor_dados
autor_2_endereco_cidade              -> autor_endereco
autor_3_nome                         -> autor_dados
autor_3_endereco_logradouro          -> autor_endereco
```

### **Endereços Genéricos** ✅

```
endereco_logradouro                  -> endereco
endereco_cidade                      -> endereco
```

## Estrutura de Organização Melhorada

### Autores

- **Detecção automática** de quantidade de autores
- **Agrupamento por número** (autor_1, autor_2, autor_3...)
- **Separação clara** entre dados pessoais e endereço
- **Feedback visual** para múltiplos autores

### Autoridades

- **Todos os campos** de autoridades (incluindo endereços) ficam na seção "Autoridades de Trânsito"
- **Organização por índice** (Autoridade 1, Autoridade 2, etc.)
- **Funcionalidade drag & drop** mantida

---

_Correções implementadas em: Janeiro 2025_
_Status: ✅ Concluído e testado_
