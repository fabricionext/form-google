#!/bin/bash

# Script para limpar completamente o stack de monitoramento
# Uso: ./clean_monitoring.sh [--force-volumes] [--prune-images]

FORCE_VOLUMES=false
PRUNE_IMAGES=false

for arg in "$@"; do
  case $arg in
    --force-volumes)
      FORCE_VOLUMES=true
      ;;
    --prune-images)
      PRUNE_IMAGES=true
      ;;
  esac
done

echo "🧹 Limpando stack de monitoramento..."

# Parar containers
if docker ps -a --format '{{.Names}}' | grep -qE '^(loki|grafana)$'; then
  echo "🛑 Parando containers..."
  docker stop loki grafana 2>/dev/null || true
else
  echo "ℹ️  Containers loki/grafana não encontrados."
fi

# Remover containers
if docker ps -a --format '{{.Names}}' | grep -qE '^(loki|grafana)$'; then
  echo "🗑️ Removendo containers..."
  docker rm loki grafana 2>/dev/null || true
else
  echo "ℹ️  Containers loki/grafana já removidos."
fi

# Remover volumes (CUIDADO: isso apaga todos os dados)
if docker volume ls --format '{{.Name}}' | grep -qE '^(loki-data|grafana-data)$'; then
  if $FORCE_VOLUMES; then
    echo "🗑️ Removendo volumes..."
    docker volume rm loki-data grafana-data 2>/dev/null || true
  else
    read -p "❓ Deseja remover os volumes (dados serão perdidos)? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      echo "🗑️ Removendo volumes..."
      docker volume rm loki-data grafana-data 2>/dev/null || true
    else
      echo "📦 Volumes mantidos"
    fi
  fi
else
  echo "ℹ️  Volumes loki-data/grafana-data não encontrados."
fi

# Remover rede
if docker network ls --format '{{.Name}}' | grep -q '^monitoring$'; then
  echo "🌐 Removendo rede..."
  docker network rm monitoring 2>/dev/null || true
else
  echo "ℹ️  Rede monitoring não encontrada."
fi

# Limpar arquivos temporários
if [ -d "/tmp/monitoring-config" ]; then
  echo "🧹 Limpando arquivos temporários..."
  rm -rf /tmp/monitoring-config
else
  echo "ℹ️  Nenhum arquivo temporário encontrado em /tmp/monitoring-config."
fi

# Limpar imagens não utilizadas (opcional)
if $PRUNE_IMAGES; then
  echo "🧹 Limpando imagens não utilizadas..."
  docker image prune -f
else
  read -p "❓ Deseja limpar imagens Docker não utilizadas? [y/N]: " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Limpando imagens não utilizadas..."
    docker image prune -f
  fi
fi

echo "✅ Limpeza concluída!" 