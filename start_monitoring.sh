#!/bin/bash

# Script para iniciar o stack de monitoramento (Loki + Grafana)

echo "🚀 Iniciando stack de monitoramento..."

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

# Verificar se o docker-compose.yml existe
if [ ! -f "$MONITORING_DIR/docker-compose.yml" ]; then
    echo "❌ docker-compose.yml não encontrado em: $MONITORING_DIR"
    exit 1
fi

# Navegar para o diretório de monitoramento
cd "$MONITORING_DIR"

# Parar containers existentes se houver
echo "🛑 Parando containers existentes..."
docker-compose down

# Iniciar os serviços
echo "📦 Iniciando Loki e Grafana..."
docker-compose up -d

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
    docker-compose logs loki
fi

if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana está rodando em http://localhost:3000"
    echo "📊 Acesse o Grafana: http://localhost:3000"
    echo "👤 Login: admin / admin"
else
    echo "❌ Grafana não está respondendo"
    echo "📋 Verificando logs do Grafana..."
    docker-compose logs grafana
fi

echo ""
echo "📝 Para parar os serviços:"
echo "   cd $MONITORING_DIR && docker-compose down"
echo ""
echo "📝 Para ver logs:"
echo "   cd $MONITORING_DIR && docker-compose logs -f" 