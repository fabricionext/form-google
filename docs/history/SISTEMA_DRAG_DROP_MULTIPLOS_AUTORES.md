# 🎯 Sistema Drag & Drop para Múltiplos Autores

## 📅 Data: 25/06/2025 - 13:22

---

## 🎯 Objetivo

Resolver o problema de UX onde arrastar um cliente preenchía todos os autores simultaneamente, criando confusão no formulário. Implementar zonas de drop específicas para cada autor individualmente.

## ⚠️ Problema Original

### **Comportamento Anterior:**

```
🔄 Arrastar cliente → Todos os autores preenchidos
✅ Campo [autor_1_nome] preenchido com: Karina
✅ Campo [autor_2_nome] preenchido com: Karina
✅ Campo [autor_1_cpf] preenchido com: 10133041956
✅ Campo [autor_2_cpf] preenchido com: 10133041956
```

**Causa:** Sistema usava `data-map-key` global, preenchendo qualquer campo com a mesma chave.

## ✅ Solução Implementada

### **1. Função `fillField` Aprimorada**

```javascript
fillField(fieldName, value, overwrite = false) {
  const field = document.querySelector(`#peticao_form [name="${fieldName}"]`);

  // Não existe ou valor inválido
  if (!field || value === undefined || value === null) {
    return false;
  }

  // Não sobrescrever campos preenchidos (exceto se forçado)
  if (!overwrite && field.value) {
    return false;
  }

  // Não preencher strings vazias em campos vazios
  if (value === '' && !field.value) {
    return false;
  }

  field.value = value;
  field.dispatchEvent(new Event('input', { bubbles: true }));
  field.dispatchEvent(new Event('change', { bubbles: true }));

  console.log(`✅ Campo [${fieldName}] preenchido com: ${value}`);
  return true;
}
```

### **2. Sistema de Mapeamento Inteligente**

```javascript
loadClienteData(cliente, autorIndex) {
  // Carregamento inicial (sem índice)
  if (!autorIndex) {
    this.cliente = cliente;
    this.clienteId = cliente.id;
    this.clienteCarregado = true;
    this.loadClienteData(cliente, 1); // Preenche autor 1
    this.fillField('data_atual', new Date().toISOString().split('T')[0]);
    return;
  }

  // Mapeamento específico por autor
  const mapeamento = {
    primeiro_nome: `_nome`,
    sobrenome: `_sobrenome`,
    cpf: `_cpf`,
    rg: `_rg`,
    // ... etc
  };

  Object.keys(mapeamento).forEach(clienteKey => {
    const valor = cliente[clienteKey];
    const nomeCampo = `autor_${autorIndex}${mapeamento[clienteKey]}`;

    if (this.fillField(nomeCampo, valor, true)) { // força sobrescrita
      camposPreenchidos++;
    }
  });
}
```

### **3. Zonas de Drop Específicas**

```javascript
// Drop zone principal (carregamento inicial)
interact('#drop_placeholder').dropzone({
  accept: '[data-type="cliente"]',
  ondrop: event => {
    const clienteData = JSON.parse(event.relatedTarget.dataset.cliente);
    this.loadClienteData(clienteData); // Sem índice = autor 1
  },
});

// Zonas específicas para cada autor
interact('.autor-drop-zone').dropzone({
  accept: '[data-type="cliente"]',
  ondrop: event => {
    const clienteData = JSON.parse(event.relatedTarget.dataset.cliente);
    const autorIndex = event.target.dataset.autorIndex; // 1, 2, 3...
    this.loadClienteData(clienteData, autorIndex); // Preenche autor específico
  },
});
```

### **4. HTML Atualizado**

```html
<!-- Seção de cada autor -->
<div class="form-section autor-drop-zone" data-autor-index="{{ autor_num }}">
  <div class="section-header">
    <h6>A{{ autor_num }}. Dados do Autor {{ autor_num }}</h6>
    <span class="badge bg-success">Drag & Drop</span>
  </div>
  <div class="section-content">
    <!-- Campos do autor -->
  </div>
</div>
```

### **5. Estilos CSS Visuais**

```css
.autor-drop-zone {
  position: relative;
  transition: all 0.3s ease;
  cursor: pointer;
}

.autor-drop-zone.drop-active {
  border: 2px dashed var(--color-success) !important;
  background-color: rgba(40, 167, 69, 0.05);
  transform: scale(1.02);
}

.autor-drop-zone::before {
  content: '📁 Arraste um cliente aqui para preencher';
  position: absolute;
  top: -8px;
  right: 10px;
  background: var(--color-info);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  opacity: 0;
  transition: all 0.3s ease;
}

.autor-drop-zone.drop-active::before {
  opacity: 1;
  background: var(--color-success);
  content: '✨ Solte aqui para preencher este autor';
}
```

## 🚀 Como Funciona Agora

### **Cenário 1: Carregamento Inicial**

```
🎯 Arrastar cliente para zona principal
   → Autor 1 preenchido automaticamente
   → Estado do formulário ativado
   → Data atual preenchida
```

### **Cenário 2: Autor Específico**

```
🎯 Arrastar cliente para "Seção Autor 2"
   → Apenas Autor 2 preenchido
   → Autor 1 mantém dados anteriores
   → Feedback visual durante o arraste
```

### **Cenário 3: Sobrescrita**

```
🎯 Arrastar novo cliente para autor já preenchido
   → Dados anteriores sobrescritos (overwrite=true)
   → Feedback de sucesso
   → Contador de campos atualizados
```

## 🎨 Experiência do Usuário

### **Feedback Visual Aprimorado:**

- ✨ **Hover:** Seções destacam quando cliente passa por cima
- 🎯 **Drop Zone Ativa:** Borda verde e tooltip explicativo
- 📊 **Contadores:** "Autor 2 carregado com 12 campos"
- 🔄 **Animações:** Suaves transições e scale effects

### **Logs Limpos e Informativos:**

```
📋 Preenchendo dados do Autor 2 com o cliente: {dados...}
✅ Campo [autor_2_nome] preenchido com: João Silva
✅ Campo [autor_2_cpf] preenchido com: 123.456.789-00
✅ Autor 2 carregado com 12 campos.
```

## 🧪 Como Testar

### **Teste 1: Carregamento Inicial**

1. Acesse formulário dinâmico
2. Arraste cliente para zona principal
3. **Esperado:** Autor 1 preenchido + formulário ativo

### **Teste 2: Autor Específico**

1. Arraste cliente diretamente para "Seção Autor 2"
2. **Esperado:** Apenas Autor 2 preenchido
3. **Verificar:** Autor 1 mantém dados anteriores

### **Teste 3: Sobrescrita**

1. Arraste novo cliente para autor já preenchido
2. **Esperado:** Dados atualizados
3. **Observar:** Feedback visual e logs

### **Teste 4: Múltiplos Autores**

1. Preencha Autor 1 com Cliente A
2. Preencha Autor 2 com Cliente B
3. **Esperado:** Dados independentes mantidos

## 📊 Benefícios Alcançados

### ✅ **UX Melhorada**

- **Controle preciso:** Usuário escolhe qual autor preencher
- **Feedback visual:** Interface responsiva e intuitiva
- **Prevenção de erros:** Não mais dados duplicados acidentalmente

### ✅ **Funcionalidade Robusta**

- **Mapeamento inteligente:** Sistema específico por índice de autor
- **Sobrescrita controlada:** Parâmetro `overwrite` quando necessário
- **Compatibilidade mantida:** Zona principal ainda funciona normalmente

### ✅ **Código Limpo**

- **Função unificada:** `fillField` para todos os preenchimentos
- **Logs informativos:** Debugging facilitado
- **Reutilização:** Sistema pode ser expandido para outros campos

## 🔄 Comparação Antes vs Depois

| Aspecto           | Antes                          | Depois                             |
| ----------------- | ------------------------------ | ---------------------------------- |
| **Controle**      | Preenche todos os autores      | Preenche autor específico          |
| **UX**            | Confuso para múltiplos autores | Intuitivo e preciso                |
| **Feedback**      | Logs excessivos                | Logs limpos e informativos         |
| **Flexibilidade** | Uma zona de drop               | Zona principal + zonas específicas |
| **Sobrescrita**   | Sempre sobrescreve             | Controlada por parâmetro           |

## 📝 Arquivos Modificados

- ✅ `templates/peticionador/formulario_dinamico.html`
  - Função `fillField` aprimorada com `overwrite`
  - Função `loadClienteData` refatorada com `autorIndex`
  - Função `setupInteractJS` expandida
  - CSS para `.autor-drop-zone` adicionado
  - HTML das seções de autor atualizado

## 🚀 Status Final

**Serviço:** ✅ **Active (running)** - 13:22:21  
**Memory:** 240.0M (otimizada)  
**CPU:** Baixo uso  
**Workers:** 4 processos ativos

**Funcionalidade:** ✅ **Operacional e intuitiva**  
**UX:** 🎯 **Controle preciso por autor**  
**Performance:** ⚡ **Rápida e responsiva**  
**Logs:** 📝 **Limpos e informativos**

---

## 🎉 Resultado Final

O sistema agora oferece uma experiência de usuário **profissional e intuitiva** para formulários com múltiplos autores:

1. **Zona principal** para carregamento inicial (Autor 1 + ativação)
2. **Zonas específicas** para preenchimento direcionado
3. **Feedback visual** rico durante interação
4. **Controle total** sobre quais dados preencher
5. **Compatibilidade** com fluxo existente

**Status:** 🟢 **IMPLEMENTAÇÃO CONCLUÍDA COM SUCESSO**
