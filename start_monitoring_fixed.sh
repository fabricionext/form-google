#!/bin/bash

# Script corrigido para iniciar o stack de monitoramento
# Resolve o problema de montagem do arquivo de configuração do Loki

echo "🚀 Iniciando stack de monitoramento (versão corrigida)..."

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

# Copiar arquivos de configuração para /tmp
echo "📋 Preparando arquivos de configuração..."
mkdir -p /tmp/monitoring-config
cp -r "$MONITORING_DIR"/* /tmp/monitoring-config/

# Iniciar Loki (CORRIGIDO: montando em /etc/local-config.yaml)
echo "📦 Iniciando Loki..."
docker run -d \
  --name loki \
  --network monitoring \
  -p 3100:3100 \
  -v "/tmp/monitoring-config/loki/loki-config.yaml:/etc/local-config.yaml" \
  -v loki-data:/tmp/loki \
  grafana/loki:2.9.0 \
  -config.file=/etc/local-config.yaml

# Aguardar Loki iniciar
echo "⏳ Aguardando Loki iniciar..."
sleep 10

# Verificar se Loki iniciou corretamente
if docker ps --format '{{.Names}}' | grep -q '^loki$'; then
    echo "✅ Loki iniciado com sucesso"
else
    echo "❌ Falha ao iniciar Loki"
    echo "📋 Logs do Loki:"
    docker logs loki
    exit 1
fi

# Iniciar Grafana
echo "📦 Iniciando Grafana..."
docker run -d \
  --name grafana \
  --network monitoring \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  -v grafana-data:/var/lib/grafana \
  -v "/tmp/monitoring-config/grafana/provisioning:/etc/grafana/provisioning" \
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
echo "   ./clean_monitoring.sh"
echo ""
echo "📝 Para ver logs:"
echo "   docker logs -f loki"
echo "   docker logs -f grafana" 