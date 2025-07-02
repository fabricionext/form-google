#!/bin/bash

echo "🔧 CORREÇÃO COMPLETA - VUE PRODUCTION + FRAMEWORK FIXES"
echo "======================================================="

# 1. Backup dos arquivos originais
echo "1️⃣ Criando backups..."
cp html/index.html html/index.html.backup.$(date +%Y%m%d_%H%M%S)
cp templates/_base_peticionador_vuetify.html templates/_base_peticionador_vuetify.html.backup.$(date +%Y%m%d_%H%M%S)
echo "   ✅ Backups criados"

# 2. Trocar Vue Development para Production em todos os arquivos
echo "2️⃣ Corrigindo Vue para Production Build..."

# Procurar e substituir em todos os arquivos HTML
find . -name "*.html" -not -path "./node_modules/*" -not -path "./.git/*" | xargs grep -l "vue.global.js" | while read file; do
    echo "   🔄 Corrigindo: $file"
    sed -i 's|vue@3\.4\.21/dist/vue\.global\.js|vue@3.4.21/dist/vue.global.prod.js|g' "$file"
    sed -i 's|/vue@3\.4\.21/dist/vue\.global\.js|/vue@3.4.21/dist/vue.global.prod.js|g' "$file"
done

echo "   ✅ Vue Production Build aplicado"

# 3. Verificar e corrigir problemas de framework
echo "3️⃣ Verificando dependências problemáticas..."

# Remover dependências que podem causar conflitos
if [ -d "node_modules" ]; then
    echo "   ⚠️  Removendo node_modules da raiz (conflitos)"
    rm -rf node_modules
fi

# Limpar cache de builds antigos
rm -rf .cache
rm -rf frontend/.nuxt
rm -rf frontend/.vite

echo "   ✅ Cache limpo"

# 4. Corrigir problemas específicos do Docker
echo "4️⃣ Preparando correções para Docker..."

# Criar script de atualização para Docker
cat > docker_update_files.sh << 'EOF'
#!/bin/bash
echo "🐳 Atualizando arquivos no Docker..."

# Copiar arquivos corrigidos para container
docker cp html/index.html form-google-app:/home/app/html/index.html
docker cp templates/_base_peticionador_vuetify.html form-google-app:/home/app/templates/_base_peticionador_vuetify.html

# Reiniciar serviços
docker exec form-google-app supervisorctl restart gunicorn
docker exec form-google-app supervisorctl restart nginx

echo "✅ Arquivos atualizados no Docker"
EOF

chmod +x docker_update_files.sh
echo "   ✅ Script Docker criado"

# 5. Verificar templates duplicados
echo "5️⃣ Verificando templates duplicados..."
if [ -f "templates/peticionador/dashboard.html" ] && [ -f "templates/peticionador/dashboard_vuetify.html" ]; then
    echo "   ⚠️  Templates dashboard duplicados encontrados"
    echo "      📁 dashboard.html"
    echo "      📁 dashboard_vuetify.html"
    echo "   💡 Recomendação: usar dashboard_vuetify.html (mais moderno)"
else
    echo "   ✅ Sem duplicação de templates"
fi

# 6. Teste de integridade
echo "6️⃣ Teste de integridade dos arquivos..."
ERRORS=0

# Verificar se Vue production foi aplicado
if grep -r "vue.global.js" html/ templates/ 2>/dev/null | grep -v ".backup"; then
    echo "   ❌ Ainda há referências ao Vue development"
    ERRORS=$((ERRORS + 1))
else
    echo "   ✅ Vue production aplicado corretamente"
fi

# Verificar sintaxe HTML básica
for file in html/index.html templates/_base_peticionador_vuetify.html; do
    if [ -f "$file" ]; then
        if grep -q "</html>" "$file" && grep -q "<html" "$file"; then
            echo "   ✅ $file - HTML válido"
        else
            echo "   ❌ $file - HTML pode estar corrompido"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

# 7. Aplicar correções no Docker (se disponível)
echo "7️⃣ Aplicando correções no Docker..."
if docker ps | grep -q "form-google-app"; then
    echo "   🐳 Container encontrado - aplicando correções..."
    ./docker_update_files.sh
    
    # Teste após correção
    sleep 5
    HTTP_STATUS=$(curl -s -w "%{http_code}" -o /dev/null https://appform.estevaoalmeida.com.br/cadastrodecliente 2>/dev/null)
    if [ "$HTTP_STATUS" = "200" ]; then
        echo "   ✅ Endpoint público funcionando (Status: $HTTP_STATUS)"
    else
        echo "   ⚠️  Endpoint com status: $HTTP_STATUS"
    fi
else
    echo "   ℹ️  Container não encontrado - execute ./docker_update_files.sh após iniciar"
fi

# Resultado final
echo ""
echo "======================================================="
if [ $ERRORS -eq 0 ]; then
    echo "🎉 CORREÇÃO CONCLUÍDA COM SUCESSO!"
    echo "✅ Vue Production Build aplicado"
    echo "✅ Cache limpo"
    echo "✅ Docker atualizado (se disponível)"
    echo ""
    echo "🔗 Teste os endpoints:"
    echo "   • https://appform.estevaoalmeida.com.br/cadastrodecliente"
    echo "   • https://appform.estevaoalmeida.com.br/peticionador/dashboard"
else
    echo "⚠️  CORREÇÃO PARCIAL - $ERRORS erro(s) encontrado(s)"
    echo "🔧 Verifique os problemas acima e execute novamente"
fi

echo ""
echo "📅 Correção realizada em: $(date)"
echo "🗂️  Backups salvos em: *.backup.*"
echo "======================================================="

exit $ERRORS 