#!/bin/bash

echo "🚨 LIMPEZA DE EMERGÊNCIA - VUE/VITE CONFLICTS"
echo "================================================="

# 1. Limpeza local
echo "1️⃣ Limpeza local..."
rm -rf html/assets/index-*.js
rm -rf html/assets/*.ts
rm -rf frontend/dist
rm -rf frontend/.vite
rm -rf frontend/node_modules/.vite
find . -name "framework.ts" -delete
find . -name "*.js.map" -delete
echo "   ✅ Local limpo"

# 2. Limpeza no container
echo "2️⃣ Limpeza no container..."
docker exec form-google-app bash -c "find /home/app/html -name 'index-*.js' -delete"
docker exec form-google-app bash -c "find /home/app -name '*.ts' -not -path '*/node_modules/*' -delete"
docker exec form-google-app bash -c "find /home/app -name 'framework.*' -delete"
docker exec form-google-app bash -c "rm -rf /home/app/.cache"
echo "   ✅ Container limpo"

# 3. Cache do nginx
echo "3️⃣ Limpeza cache nginx..."
docker exec form-google-app bash -c "rm -rf /var/cache/nginx/*"
docker exec form-google-app bash -c "nginx -s reload"
echo "   ✅ Cache nginx limpo"

# 4. Copiar templates corretos
echo "4️⃣ Aplicando templates corretos..."
docker cp templates/peticionador/dashboard_vuetify.html form-google-app:/home/app/templates/peticionador/dashboard_vuetify.html
docker cp templates/_base_peticionador_vuetify.html form-google-app:/home/app/templates/_base_peticionador_vuetify.html
docker cp html/index.html form-google-app:/home/app/html/index.html
echo "   ✅ Templates atualizados"

# 5. Reiniciar serviços
echo "5️⃣ Reiniciando serviços..."
docker exec form-google-app supervisorctl restart all
sleep 5
echo "   ✅ Serviços reiniciados"

# 6. Cache headers para forçar reload no navegador
echo "6️⃣ Configurando headers para limpar cache do navegador..."
docker exec form-google-app bash -c 'echo "location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires -1;
    add_header Cache-Control \"no-cache, no-store, must-revalidate\";
    add_header Pragma \"no-cache\";
}" > /etc/nginx/conf.d/no-cache.conf'
docker exec form-google-app nginx -s reload
echo "   ✅ Headers no-cache aplicados"

echo ""
echo "🎉 LIMPEZA DE EMERGÊNCIA CONCLUÍDA"
echo "================================================="
echo "✅ Todos os vestígios Vite/TypeScript removidos"
echo "✅ Templates Vue corrigidos aplicados"
echo "✅ Cache do navegador forçado a recarregar"
echo "✅ Serviços reiniciados"
echo ""
echo "⚠️  IMPORTANTE: Pressione Ctrl+F5 no navegador para forçar reload"
echo "" 