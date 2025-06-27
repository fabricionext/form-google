# 🚀 GUIA COMPLETO DE TESTES EM PRODUÇÃO

Este guia detalha como testar de forma segura todas as melhorias de segurança e refatoração implementadas no ambiente de produção.

## 📋 PRÉ-REQUISITOS

### 1. Dependências Python

```bash
pip install requests
```

### 2. Acesso ao Servidor

- Acesso SSH ao servidor de produção
- Credenciais de login da aplicação
- URL base da aplicação

### 3. Backup de Segurança

```bash
# Fazer backup do banco antes dos testes
sudo systemctl stop form_google
sudo -u postgres pg_dump form_google > backup_pre_testes_$(date +%Y%m%d_%H%M%S).sql
sudo systemctl start form_google
```

## 🧪 ESTRATÉGIAS DE TESTE

### Fase 1: Testes de Segurança (SEM RISCO)

Testa apenas as melhorias de validação e segurança sem modificar dados.

### Fase 2: Testes de Service Layer (BAIXO RISCO)

Testa as novas rotas V2 em paralelo com as originais.

### Fase 3: Migração Gradual (RISCO CONTROLADO)

Ativa o feature flag para usar as novas implementações.

## 🔒 FASE 1: TESTES DE SEGURANÇA

### 1.1 Teste Automático de Segurança

```bash
# Executar script de teste automático
python test_seguranca_producao.py https://appform.estevaoalmeida.com.br

# Com autenticação (se necessário)
python test_seguranca_producao.py https://appform.estevaoalmeida.com.br "session_cookie_value"

# Com slug de teste para Service Layer
python test_seguranca_producao.py https://appform.estevaoalmeida.com.br "session_cookie" "formulario-teste"
```

### 1.2 Teste Manual de CPF

```bash
# CPF válido - deve funcionar
curl "https://appform.estevaoalmeida.com.br/api/clientes/busca_cpf?cpf=123.456.789-00"

# CPF malicioso - deve ser rejeitado com erro 400
curl "https://appform.estevaoalmeida.com.br/api/clientes/busca_cpf?cpf=123<script>alert(1)"

# CPF muito longo - deve ser rejeitado
curl "https://appform.estevaoalmeida.com.br/api/clientes/busca_cpf?cpf=123456789012345"
```

### 1.3 Verificação de Headers de Segurança

```bash
# Verificar headers de segurança
curl -I https://appform.estevaoalmeida.com.br/ | grep -E "(X-Content-Type|X-Frame|X-XSS)"
```

### 1.4 Teste da Rota de Desenvolvimento

```bash
# Deve retornar 404 em produção
curl -I https://appform.estevaoalmeida.com.br/setup_admin_dev
```

## 🏗️ FASE 2: TESTES DE SERVICE LAYER

### 2.1 Verificar Slugs Disponíveis

```bash
# Conectar ao servidor
ssh usuario@servidor

# Listar formulários disponíveis
cd /var/www/estevaoalmeida.com.br/form-google
python -c "
import sys
sys.path.insert(0, '.')
from application import app
from app.peticionador.models import FormularioGerado

with app.app_context():
    formularios = FormularioGerado.query.all()
    for f in formularios:
        print(f'{f.slug} - {f.nome}')
"
```

### 2.2 Teste das Rotas V2

```bash
# Escolher um slug de teste (ex: suspensao-cnh-teste)
SLUG="suspensao-cnh-teste"

# Testar rota original
curl -X POST "https://appform.estevaoalmeida.com.br/formularios/$SLUG" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "autor_nome=João+Teste&autor_cpf=123.456.789-00&processo_numero=TESTE-$(date +%s)" \
  --cookie "session=SEU_COOKIE_AQUI"

# Testar rota V2 (nova implementação)
curl -X POST "https://appform.estevaoalmeida.com.br/formularios/$SLUG/v2" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "autor_nome=João+Teste&autor_cpf=123.456.789-00&processo_numero=TESTE-$(date +%s)" \
  --cookie "session=SEU_COOKIE_AQUI"
```

### 2.3 Comparação de Performance

```bash
# Script para medir tempo de resposta
for i in {1..5}; do
  echo "Teste $i - Rota Original:"
  time curl -s -X POST "https://appform.estevaoalmeida.com.br/formularios/$SLUG" \
    -d "autor_nome=Teste$i" --cookie "session=COOKIE" > /dev/null

  echo "Teste $i - Rota V2:"
  time curl -s -X POST "https://appform.estevaoalmeida.com.br/formularios/$SLUG/v2" \
    -d "autor_nome=Teste$i" --cookie "session=COOKIE" > /dev/null
done
```

## 🚦 FASE 3: MIGRAÇÃO GRADUAL

### 3.1 Ativação do Feature Flag

```bash
# Conectar ao servidor
ssh usuario@servidor

# Ativar o feature flag
export USE_SERVICE_LAYER=true

# Reiniciar a aplicação
sudo systemctl restart form_google

# Verificar logs
sudo journalctl -f -u form_google
```

### 3.2 Monitoramento Durante Migração

```bash
# Terminal 1: Logs da aplicação
sudo journalctl -f -u form_google | grep -E "(ERROR|FEATURE FLAG|Service Layer)"

# Terminal 2: Teste contínuo
while true; do
  curl -s "https://appform.estevaoalmeida.com.br/api/clientes/busca_cpf?cpf=123.456.789-00" | jq .
  sleep 5
done

# Terminal 3: Monitorar recursos
top -p $(pgrep -f "gunicorn.*form_google")
```

### 3.3 Rollback de Emergência

```bash
# Em caso de problemas, rollback imediato
export USE_SERVICE_LAYER=false
sudo systemctl restart form_google

# Verificar se voltou ao normal
curl -s "https://appform.estevaoalmeida.com.br/api/clientes/busca_cpf?cpf=123.456.789-00"
```

## 📊 SCRIPTS DE MONITORAMENTO

### Script de Monitoramento Contínuo

```bash
#!/bin/bash
# monitor_producao.sh

URL="https://appform.estevaoalmeida.com.br"
LOG_FILE="monitor_$(date +%Y%m%d_%H%M%S).log"

echo "Iniciando monitoramento de produção..." | tee -a $LOG_FILE

while true; do
  TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

  # Teste de saúde básico
  HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null "$URL/")
  echo "[$TIMESTAMP] Health Check: HTTP $HTTP_CODE" | tee -a $LOG_FILE

  # Teste de API de CPF
  API_RESPONSE=$(curl -s "$URL/api/clientes/busca_cpf?cpf=123.456.789-00")
  if echo "$API_RESPONSE" | grep -q "error\|success"; then
    echo "[$TIMESTAMP] API CPF: OK" | tee -a $LOG_FILE
  else
    echo "[$TIMESTAMP] API CPF: ERRO - $API_RESPONSE" | tee -a $LOG_FILE
  fi

  # Verificar uso de CPU/Memória
  CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
  MEM=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
  echo "[$TIMESTAMP] Recursos: CPU ${CPU}%, MEM ${MEM}%" | tee -a $LOG_FILE

  sleep 30
done
```

### Script de Validação Pós-Deploy

```bash
#!/bin/bash
# validacao_pos_deploy.sh

echo "🔍 VALIDAÇÃO PÓS-DEPLOY"
echo "======================="

# 1. Verificar se aplicação está rodando
if curl -s https://appform.estevaoalmeida.com.br/ > /dev/null; then
  echo "✅ Aplicação está online"
else
  echo "❌ Aplicação offline - CRÍTICO!"
  exit 1
fi

# 2. Testar API de CPF com validação segura
echo "🧪 Testando validação de CPF..."
RESPONSE=$(curl -s "https://appform.estevaoalmeida.com.br/api/clientes/busca_cpf?cpf=123<script>")
if echo "$RESPONSE" | grep -q "error"; then
  echo "✅ Validação de CPF rejeitando entradas maliciosas"
else
  echo "❌ Validação de CPF FALHANDO - SEGURANÇA COMPROMETIDA!"
fi

# 3. Verificar logs de erro
echo "📋 Verificando logs recentes..."
ERRORS=$(sudo journalctl -u form_google --since "5 minutes ago" | grep -c ERROR)
if [ $ERRORS -gt 10 ]; then
  echo "⚠️  Muitos erros nos logs: $ERRORS"
else
  echo "✅ Logs normais: $ERRORS erros"
fi

echo "✅ Validação pós-deploy concluída"
```

## 🚨 PROCEDIMENTOS DE EMERGÊNCIA

### Rollback Completo

```bash
#!/bin/bash
# rollback_emergencia.sh

echo "🚨 INICIANDO ROLLBACK DE EMERGÊNCIA"

# 1. Desativar feature flags
export USE_SERVICE_LAYER=false

# 2. Parar aplicação
sudo systemctl stop form_google

# 3. Restaurar backup do banco (se necessário)
# sudo -u postgres psql -d form_google < backup_pre_testes_XXXXXX.sql

# 4. Reverter código (se necessário)
# git checkout HEAD~1
# sudo systemctl restart form_google

# 5. Reiniciar aplicação
sudo systemctl start form_google

# 6. Verificar saúde
curl -s https://appform.estevaoalmeida.com.br/ && echo "✅ ROLLBACK CONCLUÍDO"
```

### Alertas Automatizados

```bash
# Adicionar ao crontab para monitoramento a cada 5 min
*/5 * * * * /path/to/check_health.sh

# check_health.sh
#!/bin/bash
if ! curl -s https://appform.estevaoalmeida.com.br/ > /dev/null; then
  echo "ALERTA: Aplicação offline $(date)" | mail -s "PRODUÇÃO OFFLINE" admin@empresa.com
fi
```

## 📈 MÉTRICAS DE SUCESSO

### Indicadores de Performance

- ✅ Tempo de resposta API < 1s
- ✅ Zero erros de validação falsos positivos
- ✅ CPU usage < 80%
- ✅ Memory usage < 85%

### Indicadores de Segurança

- ✅ 100% de rejeição de CPFs maliciosos
- ✅ Headers de segurança presentes
- ✅ Rota de desenvolvimento bloqueada
- ✅ Logs de segurança ativos

### Indicadores de Funcionalidade

- ✅ Service Layer funcionando
- ✅ Formulários gerando documentos
- ✅ Propriedades @property ativas
- ✅ Zero downtime durante migração

## ✅ CHECKLIST FINAL

### Antes dos Testes

- [ ] Backup do banco de dados realizado
- [ ] Servidor de monitoramento ativo
- [ ] Scripts de rollback prontos
- [ ] Equipe de plantão notificada

### Durante os Testes

- [ ] Monitoramento contínuo ativo
- [ ] Logs sendo acompanhados
- [ ] Métricas de performance ok
- [ ] Usuários não reportando problemas

### Após os Testes

- [ ] Todos os testes passaram
- [ ] Performance mantida ou melhorada
- [ ] Zero downtime registrado
- [ ] Documentação atualizada

---

## 🎯 COMANDOS RÁPIDOS

```bash
# Teste rápido de segurança
python test_seguranca_producao.py https://appform.estevaoalmeida.com.br

# Monitoramento em tempo real
sudo journalctl -f -u form_google | grep -E "(ERROR|INFO|WARNING)"

# Verificação de saúde
curl -I https://appform.estevaoalmeida.com.br/

# Rollback de emergência
export USE_SERVICE_LAYER=false && sudo systemctl restart form_google
```

Com este guia, você pode testar todas as melhorias de forma gradual e segura, sempre com possibilidade de rollback imediato em caso de problemas.
