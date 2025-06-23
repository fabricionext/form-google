#!/bin/bash
# Script para limpar completamente o stack de monitoramento

echo "🧹 Limpando stack de monitoramento..."

# Parar containers
echo "🛑 Parando containers..."
docker stop loki grafana 2>/dev/null || true

# Remover containers
echo "🗑️  Removendo containers..."
docker rm loki grafana 2>/dev/null || true

# Remover rede
echo "🌐 Removendo rede de monitoramento..."
docker network rm monitoring 2>/dev/null || true

# Limpar volumes órfãos
echo "💾 Removendo volumes órfãos..."
docker volume prune -f

# Limpar arquivos temporários
echo "📁 Limpando arquivos temporários..."
rm -rf /tmp/loki-data
rm -rf /tmp/grafana-data
rm -rf /tmp/loki-config
rm -rf /tmp/grafana-config

echo "✅ Limpeza concluída!"
echo ""
echo "📝 Para verificar se tudo foi removido:"
echo "   docker ps -a | grep -E 'loki|grafana'"
echo "   docker network ls | grep monitoring"
echo "   docker volume ls | grep -E 'loki|grafana'" 