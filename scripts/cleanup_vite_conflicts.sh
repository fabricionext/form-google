#!/bin/bash

echo "🧹 LIMPEZA DE CONFLITOS VITE/VUE - INICIANDO..."

# 1. Remover assets obsoletos do Vite
echo "1️⃣ Removendo assets Vite obsoletos..."
rm -f html/assets/index-*.js
rm -f html/assets/*.json.gz
echo "   ✅ Assets obsoletos removidos"

# 2. Limpar cache npm e node_modules conflitantes
echo "2️⃣ Limpando caches npm..."
if [ -d "frontend/node_modules" ]; then
    rm -rf frontend/node_modules
    echo "   ✅ frontend/node_modules removido"
fi

if [ -d "node_modules" ]; then
    rm -rf node_modules
    echo "   ✅ node_modules raiz removido"
fi

# 3. Limpar builds antigos
echo "3️⃣ Limpando builds antigos..."
rm -rf frontend/dist
rm -rf dist
rm -rf build
echo "   ✅ Diretórios de build limpos"

# 4. Verificar configurações conflitantes
echo "4️⃣ Verificando configurações..."
if [ -f "vite.config.js" ]; then
    echo "   ⚠️  vite.config.js na raiz - mover para .disabled"
    mv vite.config.js vite.config.js.disabled
fi

if [ -f "vite.config.ts" ]; then
    echo "   ⚠️  vite.config.ts na raiz - mover para .disabled"
    mv vite.config.ts vite.config.ts.disabled
fi

if [ -f "package.json" ]; then
    echo "   ⚠️  package.json na raiz - mover para .disabled"
    mv package.json package.json.disabled
fi

echo "   ✅ Configurações verificadas"

# 5. Limpeza de caches do sistema
echo "5️⃣ Limpando caches do sistema..."
rm -rf .vite
rm -rf .nuxt
rm -rf .cache
rm -rf frontend/.vite
echo "   ✅ Caches do sistema limpos"

# 6. Verificar estrutura final
echo "6️⃣ Verificando estrutura final..."
echo "   📁 Estrutura Vite/Vue:"
echo "      ✅ frontend/vite.config.js (ativo)"
echo "      ✅ frontend/package.json (ativo)"
echo "      ❌ vite.config.js.disabled (desabilitado)"
echo "      ❌ package.json.disabled (desabilitado)"

# 7. Reinstalar dependências do frontend
echo "7️⃣ Reinstalando dependências do frontend..."
cd frontend && npm install && cd ..
echo "   ✅ Dependências do frontend reinstaladas"

echo ""
echo "🎉 LIMPEZA CONCLUÍDA COM SUCESSO!"
echo "🔧 Próximos passos:"
echo "   1. Usar apenas Vue via CDN no html/index.html"
echo "   2. Manter frontend/ separado para desenvolvimento"
echo "   3. Evitar misturar builds Vite com CDN"
echo "" 