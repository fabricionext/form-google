# 🛡️ PREVENÇÃO DE CONFLITOS VITE/VUE

## 📋 **ESTRUTURA RECOMENDADA**

### ✅ **ARQUITETURA LIMPA**

```
form-google/
├── frontend/                    # Desenvolvimento Vue.js + Vite
│   ├── vite.config.js          # ✅ Configuração Vite isolada
│   ├── package.json            # ✅ Dependências frontend
│   └── src/                    # ✅ Código Vue.js moderno
├── html/                       # Produção - HTML simples
│   ├── index.html              # ✅ Vue via CDN (público)
│   └── assets/                 # ✅ Apenas CSS/fontes
├── vite.config.*.disabled      # ❌ Configs desabilitadas (raiz)
└── package.json.disabled       # ❌ Package desabilitado (raiz)
```

## 🚫 **NUNCA FAZER**

### ❌ **CONFLITOS CRÍTICOS**

1. **Múltiplas versões Vue**: CDN + build compilado na mesma página
2. **Configs duplicadas**: vite.config.js na raiz + frontend/
3. **Assets misturados**: index-\*.js do Vite + Vue CDN
4. **Package.json múltiplos**: Dependências conflitantes

### ❌ **EXEMPLOS PROBLEMÁTICOS**

```html
<!-- ❌ NUNCA FAZER - Mistura CDN + build -->
<script src="vue@3.4.21/dist/vue.global.js"></script>
<script src="/assets/index-ABC123.js"></script>
<!-- Build Vite -->
```

```bash
# ❌ NUNCA FAZER - Configs conflitantes
vite.config.js          # Raiz
frontend/vite.config.js  # Frontend
```

## ✅ **BOAS PRÁTICAS**

### 🎯 **SEPARAÇÃO CLARA**

1. **Frontend (Desenvolvimento)**: `frontend/` com Vite + Vue npm
2. **Público (Produção)**: `html/` com Vue CDN apenas
3. **API**: Flask independente do frontend

### 🔧 **COMANDOS SEGUROS**

```bash
# ✅ Desenvolvimento frontend
cd frontend && npm run dev

# ✅ Build frontend
cd frontend && npm run build

# ✅ Limpeza de conflitos
./scripts/cleanup_vite_conflicts.sh
```

### 📁 **ESTRUTURA DE ARQUIVOS**

```
# ✅ CORRETO
html/index.html          → Vue CDN (3.4.21)
frontend/src/main.js     → Vue npm (3.5.17)

# ❌ INCORRETO
html/index.html          → Vue CDN + assets Vite
frontend/html/index.html → Duplicação
```

## 🚨 **SINAIS DE CONFLITO**

### ⚠️ **ERROS INDICATIVOS**

- `u.onUnmount is not a function`
- `createApp is not a function`
- `Multiple Vue instances detected`
- `framework.ts:85 error`

### 🔍 **VERIFICAÇÕES RÁPIDAS**

```bash
# Verificar assets Vite obsoletos
find html/assets/ -name "index-*.js"

# Verificar configs duplicadas
ls -la *.config.*

# Verificar package.json múltiplos
ls -la package.json*

# Verificar Vue versions
grep -r "vue@" . --include="*.html" --include="*.json"
```

## 🛠️ **SCRIPT DE MONITORAMENTO**

### 📊 **Verificação Automática**

```bash
#!/bin/bash
# scripts/check_conflicts.sh

echo "🔍 Verificando conflitos Vite/Vue..."

# 1. Assets obsoletos
if [ -n "$(find html/assets/ -name 'index-*.js' 2>/dev/null)" ]; then
    echo "❌ Assets Vite obsoletos encontrados"
    find html/assets/ -name "index-*.js"
else
    echo "✅ Sem assets Vite obsoletos"
fi

# 2. Configs duplicadas
if [ -f "vite.config.js" ] || [ -f "vite.config.ts" ]; then
    echo "❌ Configurações Vite conflitantes na raiz"
    ls -la vite.config.*
else
    echo "✅ Sem configs Vite conflitantes"
fi

# 3. Package.json múltiplos
if [ -f "package.json" ]; then
    echo "❌ package.json na raiz pode causar conflitos"
else
    echo "✅ package.json limpo na raiz"
fi

echo "🎯 Verificação concluída"
```

## 📝 **CHECKLIST DE PREVENÇÃO**

### ✅ **ANTES DE FAZER DEPLOY**

- [ ] Executar `./scripts/cleanup_vite_conflicts.sh`
- [ ] Verificar `find html/assets/ -name "index-*.js"` = vazio
- [ ] Confirmar `ls vite.config.js` = "not found" (na raiz)
- [ ] Testar endpoint público sem erros console
- [ ] Verificar uma única versão Vue por página

### ✅ **DESENVOLVIMENTO SEGURO**

- [ ] Usar `frontend/` para desenvolvimento Vue/Vite
- [ ] Usar `html/` para páginas públicas simples
- [ ] Nunca misturar CDN + build na mesma página
- [ ] Manter configs Vite apenas em `frontend/`

## 🚑 **RECUPERAÇÃO RÁPIDA**

### 🆘 **Em caso de erro**

```bash
# Limpeza de emergência
./scripts/cleanup_vite_conflicts.sh

# Verificar funcionamento
curl -s https://appform.estevaoalmeida.com.br/cadastrodecliente | head -3

# Testar API
curl -X POST -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","primeiro_nome":"Test","sobrenome":"User","cpf":"123.456.789-00","tipo_pessoa":"FISICA"}' \
  https://appform.estevaoalmeida.com.br/api/clientes
```

---

**📅 Criado**: 02/07/2025  
**✅ Status**: Conflitos resolvidos  
**🔧 Versão**: 1.0
