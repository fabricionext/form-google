#!/bin/bash
echo "🐳 Atualizando arquivos no Docker..."

# Copiar arquivos corrigidos para container
docker cp html/index.html form-google-app:/home/app/html/index.html
docker cp templates/_base_peticionador_vuetify.html form-google-app:/home/app/templates/_base_peticionador_vuetify.html

# Reiniciar serviços
docker exec form-google-app supervisorctl restart gunicorn
docker exec form-google-app supervisorctl restart nginx

echo "✅ Arquivos atualizados no Docker"
