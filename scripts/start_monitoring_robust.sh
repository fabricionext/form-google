#!/bin/bash
# Script final corrigido para iniciar o stack de monitoramento
# Resolve problemas de permissão do Loki

echo "🚀 Iniciando stack de monitoramento (versão corrigida)..."

# Verificar se o Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Inicie o Docker primeiro."
    exit 1
fi

# Obter o diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITORING_DIR="$SCRIPT_DIR/monitoring"

# Limpar containers existentes
echo "🛑 Limpando containers existentes..."
docker stop loki grafana 2>/dev/null || true
docker rm loki grafana 2>/dev/null || true

# Limpar volumes órfãos
echo "🧹 Limpando volumes órfãos..."
docker volume prune -f

# Criar rede se não existir
echo "🌐 Criando rede de monitoramento..."
docker network create monitoring 2>/dev/null || true

# Criar diretórios locais com permissões corretas
echo "📁 Criando diretórios locais..."
mkdir -p /tmp/loki-data
mkdir -p /tmp/grafana-data
chmod 777 /tmp/loki-data
chmod 777 /tmp/grafana-data

# Criar configuração mínima do Loki
echo "📋 Criando configuração mínima do Loki..."
mkdir -p /tmp/loki-config
cat > /tmp/loki-config/loki.yaml << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9095

ingester:
  wal:
    enabled: false
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 1h
  max_chunk_age: 1h
  chunk_target_size: 1048576
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /tmp/loki/boltdb-shipper-active
    cache_location: /tmp/loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /tmp/loki/chunks

compactor:
  working_directory: /tmp/loki/compactor
  shared_store: filesystem

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

ruler:
  storage:
    type: local
    local:
      directory: /tmp/loki/rules
  rule_path: /tmp/loki/rules-temp
  alertmanager_url: http://localhost:9093
  ring:
    kvstore:
      store: inmemory
  enable_api: true
EOF

# Iniciar Loki sem configuração inicial (evita problemas de montagem)
echo "📦 Iniciando Loki..."
docker run -d \
  --name loki \
  --network monitoring \
  --user root \
  -p 3100:3100 \
  -v /tmp/loki-data:/tmp/loki \
  grafana/loki:2.9.0 \
  -config.file=/etc/loki/local-config.yaml

# Aguardar um pouco e copiar o arquivo de configuração
sleep 3
echo "📋 Copiando configuração para o container..."
docker cp /tmp/loki-config/loki.yaml loki:/etc/loki/local-config.yaml

# Reiniciar Loki para usar a configuração
echo "🔄 Reiniciando Loki com configuração..."
docker restart loki

# Aguardar Loki iniciar
echo "⏳ Aguardando Loki iniciar..."
sleep 10

# Verificar se Loki iniciou corretamente
LOKI_READY=false
for i in {1..30}; do
    if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
        LOKI_READY=true
        break
    fi
    echo "Tentativa $i/30 - Aguardando Loki..."
    sleep 2
done

if [ "$LOKI_READY" = true ]; then
    echo "✅ Loki iniciado com sucesso"
else
    echo "❌ Falha ao iniciar Loki"
    echo "📋 Logs do Loki:"
    docker logs loki --tail 30
    exit 1
fi

# Criar configuração do Grafana
echo "📋 Criando configuração do Grafana..."
mkdir -p /tmp/grafana-config/provisioning/datasources
cat > /tmp/grafana-config/provisioning/datasources/loki.yaml << 'EOF'
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: true
    editable: true
EOF

# Iniciar Grafana
echo "📦 Iniciando Grafana..."
docker run -d \
  --name grafana \
  --network monitoring \
  --user root \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  -e GF_INSTALL_PLUGINS=grafana-piechart-panel \
  -v /tmp/grafana-data:/var/lib/grafana \
  -v /tmp/grafana-config/provisioning:/etc/grafana/provisioning \
  grafana/grafana:latest

# Aguardar Grafana iniciar
echo "⏳ Aguardando Grafana iniciar..."
sleep 15

# Verificar status final
echo "🔍 Verificando status dos serviços..."

# Testar Loki
if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
    echo "✅ Loki está rodando em http://localhost:3100"
    
    # Testar se Loki pode receber logs
    echo "🧪 Testando envio de log para Loki..."
    curl -X POST http://localhost:3100/loki/api/v1/push \
      -H "Content-Type: application/json" \
      -d '{
        "streams": [
          {
            "stream": {
              "job": "test",
              "level": "info"
            },
            "values": [
              ["'$(date +%s%N)'", "Test log message from monitoring setup"]
            ]
          }
        ]
      }' > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Loki pode receber logs"
    else
        echo "⚠️  Loki iniciou mas pode ter problemas para receber logs"
    fi
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
    echo "🔌 Datasource Loki será configurado automaticamente"
else
    echo "❌ Grafana não está respondendo"
    echo "📋 Verificando logs do Grafana..."
    docker logs grafana --tail 20
fi

echo ""
echo "🎉 Setup concluído!"
echo ""
echo "📝 Comandos úteis:"
echo "   Parar serviços: docker stop loki grafana"
echo "   Remover containers: docker rm loki grafana"
echo "   Ver logs Loki: docker logs -f loki"
echo "   Ver logs Grafana: docker logs -f grafana"
echo ""
echo "📝 Para enviar logs para Loki:"
echo '   curl -X POST http://localhost:3100/loki/api/v1/push \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"streams":[{"stream":{"job":"myapp"},"values":[["'"'"'$(date +%s%N)'"'"'","Minha mensagem de log"]]}]}'"'"
echo ""
echo "📝 Para consultar logs no Loki:"
echo "   curl 'http://localhost:3100/loki/api/v1/query_range?query={job=\"myapp\"}'"
echo ""
echo "⚠️  NOTA: Esta configuração usa armazenamento temporário em /tmp."
echo "   Os dados serão perdidos quando o sistema for reiniciado." 