#!/bin/bash

# Script final simplificado para iniciar o stack de monitoramento
# Usa configuração do Loki sem volumes persistentes para evitar problemas de permissão

echo "🚀 Iniciando stack de monitoramento (versão simplificada)..."

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

# Limpar containers existentes
echo "🛑 Limpando containers existentes..."
docker stop loki grafana 2>/dev/null || true
docker rm loki grafana 2>/dev/null || true

# Criar rede se não existir
echo "🌐 Criando rede de monitoramento..."
docker network create monitoring 2>/dev/null || true

# Copiar arquivos de configuração para /tmp
echo "📋 Preparando arquivos de configuração..."
mkdir -p /tmp/monitoring-config
cp -r "$MONITORING_DIR"/* /tmp/monitoring-config/

# Iniciar Loki com configuração simplificada (sem volumes persistentes)
echo "📦 Iniciando Loki (configuração simplificada)..."
docker run -d \
  --name loki \
  --network monitoring \
  -p 3100:3100 \
  grafana/loki:2.9.0 \
  -config.file=/etc/loki/local-config.yaml

# Aguardar um pouco e copiar o arquivo de configuração simplificada
sleep 3
docker cp /tmp/monitoring-config/loki/loki-config-simple.yaml loki:/etc/loki/local-config.yaml

# Reiniciar Loki para usar a configuração
echo "🔄 Reiniciando Loki com configuração simplificada..."
docker restart loki

# Aguardar Loki iniciar
echo "⏳ Aguardando Loki iniciar..."
sleep 15

# Verificar se Loki iniciou corretamente
if docker ps --format '{{.Names}}' | grep -q '^loki$'; then
    echo "✅ Loki iniciado com sucesso"
else
    echo "❌ Falha ao iniciar Loki"
    echo "📋 Logs do Loki:"
    docker logs loki --tail 20
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
sleep 20

# Verificar status
echo "🔍 Verificando status dos serviços..."

# Testar Loki
if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
    echo "✅ Loki está rodando em http://localhost:3100"
else
    echo "❌ Loki não está respondendo"
    echo "📋 Verificando logs do Loki..."
    docker logs loki --tail 20
fi

# Testar Grafana
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana está rodando em http://localhost:3000"
    echo "📊 Acesse o Grafana: http://localhost:3000"
    echo "👤 Login: admin / admin"
else
    echo "❌ Grafana não está respondendo"
    echo "📋 Verificando logs do Grafana..."
    docker logs grafana --tail 20
fi

echo ""
echo "📝 Para parar os serviços:"
echo "   ./clean_monitoring.sh"
echo ""
echo "📝 Para ver logs:"
echo "   docker logs -f loki"
echo "   docker logs -f grafana"
echo ""
echo "📝 Para testar Loki:"
echo "   curl http://localhost:3100/ready"
echo ""
echo "📝 Para testar Grafana:"
echo "   curl http://localhost:3000/api/health"
echo ""
echo "⚠️  NOTA: Esta configuração usa armazenamento temporário. Os logs serão perdidos quando o container for reiniciado." 