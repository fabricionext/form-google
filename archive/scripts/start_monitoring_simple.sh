#!/bin/bash

# Script alternativo para iniciar o stack de monitoramento usando Docker diretamente

echo "🚀 Iniciando stack de monitoramento (Docker direto)..."

# Verificar se o Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Inicie o Docker primeiro."
    exit 1
fi

# Obter o diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$SCRIPT_DIR/monitoring"

# Verificar se o diretório de monitoramento existe
if [ ! -d "$MONITORING_DIR" ]; then
    echo "❌ Diretório de monitoramento não encontrado: $MONITORING_DIR"
    exit 1
fi

# Parar containers existentes se houver
echo "🛑 Parando containers existentes..."
docker stop loki grafana 2>/dev/null || true
docker rm loki grafana 2>/dev/null || true

# Criar rede se não existir
echo "🌐 Criando rede de monitoramento..."
docker network create monitoring 2>/dev/null || true

# Iniciar Loki
echo "📦 Iniciando Loki..."
docker run -d \
  --name loki \
  --network monitoring \
  -p 3100:3100 \
  -v "$MONITORING_DIR/loki/loki-config.yaml:/etc/loki/local-config.yaml" \
  -v loki-data:/tmp/loki \
  grafana/loki:2.9.0 \
  -config.file=/etc/loki/local-config.yaml

# Aguardar Loki iniciar
echo "⏳ Aguardando Loki iniciar..."
sleep 5

# Iniciar Grafana
echo "📦 Iniciando Grafana..."
docker run -d \
  --name grafana \
  --network monitoring \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  -v grafana-data:/var/lib/grafana \
  -v "$MONITORING_DIR/grafana/provisioning:/etc/grafana/provisioning" \
  grafana/grafana:latest

# Aguardar os serviços iniciarem
echo "⏳ Aguardando serviços iniciarem..."
sleep 15

# Verificar status
echo "🔍 Verificando status dos serviços..."

if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
    echo "✅ Loki está rodando em http://localhost:3100"
else
    echo "❌ Loki não está respondendo"
    echo "📋 Verificando logs do Loki..."
    docker logs loki
fi

if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana está rodando em http://localhost:3000"
    echo "📊 Acesse o Grafana: http://localhost:3000"
    echo "👤 Login: admin / admin"
else
    echo "❌ Grafana não está respondendo"
    echo "📋 Verificando logs do Grafana..."
    docker logs grafana
fi

echo ""
echo "📝 Para parar os serviços:"
echo "   docker stop loki grafana"
echo ""
echo "📝 Para ver logs:"
echo "   docker logs -f loki"
echo "   docker logs -f grafana" 