# Configuração de Monitoramento: Grafana Loki

Este documento descreve como configurar e usar o sistema de monitoramento baseado em Grafana Loki para logs centralizados.

## 🎯 Visão Geral

O sistema de monitoramento inclui:

- **Grafana Loki**: Agregação e armazenamento de logs
- **Grafana**: Visualização e análise de logs
- **Logs estruturados**: Sistema de logging avançado com contexto

## 🚀 Configuração Rápida

### 1. Grafana Loki (Já configurado)

O sistema já está configurado com Grafana Loki. Para iniciar:

```bash
./start_monitoring.sh
```

### 2. Acessar Grafana

- **URL**: http://localhost:3000
- **Login**: admin / admin
- **Senha inicial**: admin (será solicitada para alteração)

## 📊 Uso do Sistema

### Logs Estruturados

O sistema inclui funções para logging estruturado:

```python
from loki_logger import setup_loki_logging, log_google_api_operation, log_document_generation

# Configurar logging
setup_loki_logging()

# Log de operação da API
log_google_api_operation(
    operation='create_document',
    status='success',
    metadata={'document_id': '123', 'template': 'ficha_cadastral'}
)

# Log de geração de documento
log_document_generation(
    form_id=123,
    user_id=456,
    status='completed',
    document_type='ficha_cadastral',
    processing_time=2.5
)
```

### Queries no Grafana

Use estas queries para analisar os logs:

```logql
# Todos os logs da aplicação
{app="form-google"}

# Logs de erro
{app="form-google"} |= "error"

# Logs de operações da API
{app="form-google"} |= "google_api"

# Logs de geração de documentos
{app="form-google"} |= "document_generation"

# Logs de um usuário específico
{app="form-google"} | json | user_id="456"

# Logs de um período específico
{app="form-google"} | json | timestamp > "2024-01-15T10:00:00Z"
```

## 🛠️ Configuração Avançada

### Variáveis de Ambiente

Adicione ao seu `.env`:

```bash
# Configurações de Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOKI_URL=http://localhost:3100
```

### Configuração do Loki

O arquivo `monitoring/loki/loki-config.yaml` contém a configuração do Loki:

```yaml
auth_enabled: false
server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-05-15
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
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /tmp/loki/chunks

compactor:
  working_directory: /tmp/loki/boltdb-shipper-compactor
  shared_store: filesystem

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

### Configuração do Grafana

O arquivo `monitoring/grafana/provisioning/datasources/loki.yml` configura a fonte de dados:

```yaml
apiVersion: 1

datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      maxLines: 1000
```

## 📈 Dashboards

### Dashboard Principal

O sistema inclui um dashboard pré-configurado em `monitoring/grafana/provisioning/dashboards/dashboard.yml`:

- **Visão geral dos logs**: Contadores e métricas
- **Logs por nível**: Distribuição de logs por severidade
- **Logs por componente**: Análise por módulo da aplicação
- **Logs de erro**: Foco em erros e exceções
- **Performance**: Tempo de resposta e latência

### Criando Dashboards Personalizados

1. Acesse o Grafana
2. Vá para "Dashboards" > "New Dashboard"
3. Adicione painéis com queries LogQL
4. Configure alertas se necessário

## 🔍 Troubleshooting

### Loki não está rodando

```bash
# Verificar status dos containers
docker ps

# Verificar logs do Loki
docker logs monitoring-loki-1

# Reiniciar serviços
./start_monitoring.sh
```

### Grafana não está acessível

```bash
# Verificar se a porta 3000 está em uso
netstat -tlnp | grep :3000

# Verificar logs do Grafana
docker logs monitoring-grafana-1

# Reiniciar apenas o Grafana
docker restart monitoring-grafana-1
```

### Logs não aparecem

1. Verificar se o Loki está rodando
2. Verificar a URL do Loki no código
3. Verificar se os logs estão sendo enviados
4. Verificar a query no Grafana

### Performance

Para melhorar a performance:

1. **Ajustar retenção**: Configure `retention_period` no Loki
2. **Otimizar queries**: Use filtros específicos
3. **Monitorar recursos**: Verifique uso de CPU e memória

## 📚 Recursos Adicionais

- [Documentação do Loki](https://grafana.com/docs/loki/latest/)
- [Documentação do Grafana](https://grafana.com/docs/)
- [LogQL Reference](https://grafana.com/docs/loki/latest/logql/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)

## 🔧 Manutenção

### Backup dos Dados

```bash
# Backup dos dados do Loki
docker exec monitoring-loki-1 tar czf /tmp/loki-backup.tar.gz /tmp/loki

# Backup da configuração do Grafana
docker exec monitoring-grafana-1 tar czf /tmp/grafana-backup.tar.gz /etc/grafana
```

### Atualizações

```bash
# Parar serviços
docker-compose -f monitoring/docker-compose.yml down

# Atualizar imagens
docker-compose -f monitoring/docker-compose.yml pull

# Reiniciar serviços
docker-compose -f monitoring/docker-compose.yml up -d
```

### Limpeza

```bash
# Limpar logs antigos (manualmente)
docker exec monitoring-loki-1 rm -rf /tmp/loki/chunks/*

# Limpar cache
docker exec monitoring-loki-1 rm -rf /tmp/loki/boltdb-shipper-cache/*
```
