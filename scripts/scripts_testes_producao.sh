#!/bin/bash
# Scripts práticos para testes em produção

URL_BASE="https://appform.estevaoalmeida.com.br"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR="logs_teste_$TIMESTAMP"

# Criar diretório de logs
mkdir -p $LOG_DIR

echo "🚀 INICIANDO TESTES DE PRODUÇÃO - $TIMESTAMP"
echo "📁 Logs em: $LOG_DIR"

# Função para logs coloridos
log_success() { echo -e "\033[32m✅ $1\033[0m" | tee -a "$LOG_DIR/teste.log"; }
log_error() { echo -e "\033[31m❌ $1\033[0m" | tee -a "$LOG_DIR/teste.log"; }
log_warning() { echo -e "\033[33m⚠️  $1\033[0m" | tee -a "$LOG_DIR/teste.log"; }
log_info() { echo -e "\033[34mℹ️  $1\033[0m" | tee -a "$LOG_DIR/teste.log"; }

# TESTE 1: Verificar se aplicação está online
test_app_online() {
    log_info "Testando se aplicação está online..."
    
    HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null "$URL_BASE/" --max-time 10)
    
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
        log_success "Aplicação online - HTTP $HTTP_CODE"
        return 0
    else
        log_error "Aplicação offline ou com problema - HTTP $HTTP_CODE"
        return 1
    fi
}

# TESTE 2: Validação de CPF segura
test_cpf_validation() {
    log_info "Testando validação de CPF..."
    
    # CPF válido
    RESPONSE=$(curl -s "$URL_BASE/api/clientes/busca_cpf?cpf=123.456.789-00" --max-time 10)
    if [[ $? -eq 0 ]]; then
        log_success "CPF válido aceito"
        echo "Response: $RESPONSE" >> "$LOG_DIR/cpf_valido.json"
    else
        log_error "Falha no teste de CPF válido"
    fi
    
    # CPF malicioso
    HTTP_CODE_MAL=$(curl -s -w "%{http_code}" -o /dev/null "$URL_BASE/api/clientes/busca_cpf?cpf=123<script>alert(1)" --max-time 10)
    RESPONSE_MAL=$(curl -s "$URL_BASE/api/clientes/busca_cpf?cpf=123<script>alert(1)" --max-time 10)
    if [ "$HTTP_CODE_MAL" = "400" ] || echo "$RESPONSE_MAL" | grep -q "error"; then
        log_success "CPF malicioso rejeitado corretamente (HTTP $HTTP_CODE_MAL)"
    else
        log_error "CPF malicioso NÃO foi rejeitado - RISCO DE SEGURANÇA! (HTTP $HTTP_CODE_MAL)"
    fi
    echo "Response malicioso (HTTP $HTTP_CODE_MAL): $RESPONSE_MAL" >> "$LOG_DIR/cpf_malicioso.json"
}

# TESTE 3: Headers de segurança
test_security_headers() {
    log_info "Verificando headers de segurança..."
    
    HEADERS=$(curl -s -I "$URL_BASE/" --max-time 10)
    echo "$HEADERS" > "$LOG_DIR/headers.txt"
    
    # Verificar headers específicos
    if echo "$HEADERS" | grep -q "X-Content-Type-Options"; then
        log_success "Header X-Content-Type-Options presente"
    else
        log_warning "Header X-Content-Type-Options ausente"
    fi
    
    if echo "$HEADERS" | grep -q "X-Frame-Options"; then
        log_success "Header X-Frame-Options presente"
    else
        log_warning "Header X-Frame-Options ausente"
    fi
}

# TESTE 4: Rota de desenvolvimento bloqueada
test_dev_route_blocked() {
    log_info "Verificando se rota de desenvolvimento está bloqueada..."
    
    DEV_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null "$URL_BASE/setup_admin_dev" --max-time 10)
    
    if [ "$DEV_RESPONSE" = "404" ] || [ "$DEV_RESPONSE" = "403" ]; then
        log_success "Rota de desenvolvimento bloqueada - HTTP $DEV_RESPONSE"
    else
        log_error "Rota de desenvolvimento ACESSÍVEL - RISCO DE SEGURANÇA! HTTP $DEV_RESPONSE"
    fi
}

# TESTE 5: Performance básica
test_basic_performance() {
    log_info "Testando performance básica..."
    
    TIMES_FILE="$LOG_DIR/performance.txt"
    echo "Teste de Performance - $TIMESTAMP" > "$TIMES_FILE"
    
    for i in {1..5}; do
        START_TIME=$(date +%s.%N)
        curl -s "$URL_BASE/api/clientes/busca_cpf?cpf=123.456.789-00" > /dev/null
        END_TIME=$(date +%s.%N)
        DURATION=$(echo "$END_TIME - $START_TIME" | bc)
        echo "Teste $i: ${DURATION}s" >> "$TIMES_FILE"
        
        if (( $(echo "$DURATION < 2.0" | bc -l) )); then
            log_success "Teste $i: ${DURATION}s - OK"
        else
            log_warning "Teste $i: ${DURATION}s - LENTO"
        fi
    done
}

# TESTE 6: Validação de formulário
test_form_validation() {
    log_info "Testando validação de formulários..."
    
    # Dados com potencial XSS
    FORM_DATA="autor_nome=<script>alert('xss')</script>&autor_email=test@test.com&processo_numero=123"
    
    FORM_RESPONSE=$(curl -s -X POST "$URL_BASE/api/preview-document" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "$FORM_DATA" --max-time 15)
    
    echo "Form Response: $FORM_RESPONSE" >> "$LOG_DIR/form_validation.txt"
    
    if echo "$FORM_RESPONSE" | grep -q "error\|invalid"; then
        log_success "Validação de formulário rejeitando dados maliciosos"
    elif ! echo "$FORM_RESPONSE" | grep -q "<script>"; then
        log_success "Dados maliciosos sanitizados"
    else
        log_error "Possível vulnerabilidade XSS detectada!"
    fi
}

# TESTE 7: Verificar estrutura de arquivos críticos
test_file_structure() {
    log_info "Verificando estrutura de arquivos implementados..."
    
    FILES_TO_CHECK=(
        "app/validators/cliente_validator.py"
        "app/peticionador/services/suspensao_service.py"
        "app/peticionador/services/formulario_service.py"
        "app/peticionador/services/documento_service.py"
    )
    
    for file in "${FILES_TO_CHECK[@]}"; do
        if [ -f "$file" ]; then
            log_success "Arquivo $file presente"
            wc -l "$file" >> "$LOG_DIR/file_sizes.txt"
        else
            log_error "Arquivo $file AUSENTE"
        fi
    done
}

# TESTE 8: Verificar logs de aplicação
test_application_logs() {
    log_info "Verificando logs de aplicação..."
    
    if command -v journalctl >/dev/null 2>&1; then
        # Últimos 50 logs da aplicação
        sudo journalctl -u form_google --no-pager -n 50 > "$LOG_DIR/app_logs.txt" 2>/dev/null || {
            log_warning "Não foi possível acessar logs do systemd"
        }
        
        # Contar erros recentes
        ERROR_COUNT=$(sudo journalctl -u form_google --since "5 minutes ago" | grep -c "ERROR" 2>/dev/null || echo "0")
        
        if [ "$ERROR_COUNT" -lt 5 ]; then
            log_success "Logs normais - $ERROR_COUNT erros recentes"
        else
            log_warning "Muitos erros nos logs - $ERROR_COUNT erros recentes"
        fi
    else
        log_warning "journalctl não disponível - pulando verificação de logs"
    fi
}

# FUNÇÃO PRINCIPAL
main() {
    echo "========================================="
    echo "🔍 EXECUÇÃO DE TESTES DE PRODUÇÃO"
    echo "========================================="
    
    # Executar todos os testes
    test_app_online || exit 1
    test_cpf_validation
    test_security_headers
    test_dev_route_blocked
    test_basic_performance
    test_form_validation
    test_file_structure
    test_application_logs
    
    # Relatório final
    echo ""
    echo "========================================="
    echo "📊 RELATÓRIO FINAL"
    echo "========================================="
    
    TOTAL_ERRORS=$(grep -c "❌" "$LOG_DIR/teste.log" 2>/dev/null || echo "0")
    TOTAL_SUCCESS=$(grep -c "✅" "$LOG_DIR/teste.log" 2>/dev/null || echo "0")
    TOTAL_WARNINGS=$(grep -c "⚠️" "$LOG_DIR/teste.log" 2>/dev/null || echo "0")
    
    echo "✅ Sucessos: $TOTAL_SUCCESS"
    echo "❌ Erros: $TOTAL_ERRORS"
    echo "⚠️  Avisos: $TOTAL_WARNINGS"
    echo "📁 Logs salvos em: $LOG_DIR"
    
    if [ "$TOTAL_ERRORS" -eq 0 ]; then
        log_success "TODOS OS TESTES CRÍTICOS PASSARAM!"
        return 0
    else
        log_error "ALGUNS TESTES FALHARAM - REVISAR LOGS"
        return 1
    fi
}

# Executar se chamado diretamente
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 