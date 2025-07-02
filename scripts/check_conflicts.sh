#!/bin/bash

echo "🔍 VERIFICANDO CONFLITOS VITE/VUE..."
echo "================================================="

CONFLICTS_FOUND=0

# 1. Verificar assets obsoletos do Vite
echo "1️⃣ Verificando assets Vite obsoletos..."
VITE_ASSETS=$(find html/assets/ -name 'index-*.js' 2>/dev/null)
if [ -n "$VITE_ASSETS" ]; then
    echo "   ❌ Assets Vite obsoletos encontrados:"
    echo "$VITE_ASSETS" | sed 's/^/      /'
    CONFLICTS_FOUND=$((CONFLICTS_FOUND + 1))
else
    echo "   ✅ Sem assets Vite obsoletos"
fi

# 2. Verificar configurações duplicadas
echo ""
echo "2️⃣ Verificando configurações duplicadas..."
if [ -f "vite.config.js" ] || [ -f "vite.config.ts" ]; then
    echo "   ❌ Configurações Vite conflitantes na raiz:"
    ls -la vite.config.* 2>/dev/null | sed 's/^/      /'
    CONFLICTS_FOUND=$((CONFLICTS_FOUND + 1))
else
    echo "   ✅ Sem configs Vite conflitantes na raiz"
fi

# 3. Verificar package.json múltiplos
echo ""
echo "3️⃣ Verificando package.json..."
if [ -f "package.json" ]; then
    echo "   ⚠️  package.json na raiz pode causar conflitos"
    echo "      Recomendado: mover para package.json.disabled"
    CONFLICTS_FOUND=$((CONFLICTS_FOUND + 1))
else
    echo "   ✅ package.json limpo na raiz"
fi

# 4. Verificar múltiplas versões Vue
echo ""
echo "4️⃣ Verificando versões Vue..."
VUE_VERSIONS=$(grep -r "vue@" . --include="*.html" --include="*.json" 2>/dev/null | grep -v node_modules | grep -v disabled)
if [ -n "$VUE_VERSIONS" ]; then
    echo "   ℹ️  Versões Vue encontradas:"
    echo "$VUE_VERSIONS" | sed 's/^/      /'
    
    # Contar versões diferentes
    UNIQUE_VERSIONS=$(echo "$VUE_VERSIONS" | grep -o 'vue@[0-9]\+\.[0-9]\+\.[0-9]\+' | sort | uniq | wc -l)
    if [ "$UNIQUE_VERSIONS" -gt 1 ]; then
        echo "   ⚠️  Múltiplas versões Vue detectadas!"
        CONFLICTS_FOUND=$((CONFLICTS_FOUND + 1))
    else
        echo "   ✅ Versão Vue consistente"
    fi
else
    echo "   ℹ️  Nenhuma versão Vue específica encontrada"
fi

# 5. Verificar estrutura de diretórios
echo ""
echo "5️⃣ Verificando estrutura de diretórios..."
if [ -d "frontend/html" ]; then
    echo "   ❌ Diretório frontend/html duplicado encontrado"
    CONFLICTS_FOUND=$((CONFLICTS_FOUND + 1))
else
    echo "   ✅ Sem diretórios duplicados"
fi

# 6. Verificar node_modules duplicados
echo ""
echo "6️⃣ Verificando node_modules..."
NODE_MODULES_COUNT=$(find . -name "node_modules" -type d 2>/dev/null | grep -v ".git" | wc -l)
if [ "$NODE_MODULES_COUNT" -gt 1 ]; then
    echo "   ⚠️  Múltiplos node_modules encontrados:"
    find . -name "node_modules" -type d 2>/dev/null | grep -v ".git" | sed 's/^/      /'
    echo "   💡 Recomendado: manter apenas frontend/node_modules"
else
    echo "   ✅ Estrutura node_modules limpa"
fi

# 7. Teste funcional básico
echo ""
echo "7️⃣ Teste funcional básico..."
if command -v curl > /dev/null 2>&1; then
    HTTP_STATUS=$(curl -s -w "%{http_code}" -o /dev/null https://appform.estevaoalmeida.com.br/cadastrodecliente 2>/dev/null)
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "   ✅ Endpoint público respondendo (Status: $HTTP_STATUS)"
    else
        echo "   ❌ Endpoint público com problema (Status: $HTTP_STATUS)"
        CONFLICTS_FOUND=$((CONFLICTS_FOUND + 1))
    fi
else
    echo "   ⚠️  curl não disponível - teste manual necessário"
fi

# Resultado final
echo ""
echo "================================================="
if [ $CONFLICTS_FOUND -eq 0 ]; then
    echo "🎉 SISTEMA LIMPO - Nenhum conflito detectado!"
    echo "✅ Todos os testes passaram"
else
    echo "⚠️  CONFLITOS DETECTADOS: $CONFLICTS_FOUND problema(s)"
    echo "🔧 Execute: ./scripts/cleanup_vite_conflicts.sh"
fi

echo ""
echo "📅 Verificação realizada em: $(date)"
echo "🔗 Documentação: docs/VITE_VUE_CONFLICT_PREVENTION.md"
echo "================================================="

exit $CONFLICTS_FOUND 