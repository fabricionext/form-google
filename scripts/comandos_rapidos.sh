#!/bin/bash
# Comandos rápidos para administração do sistema refatorado

echo "🚀 COMANDOS RÁPIDOS - SISTEMA REFATORADO"
echo "========================================"

case "$1" in
    "teste-rapido"|"tr")
        echo "🧪 Executando teste rápido de segurança..."
        curl -s "https://appform.estevaoalmeida.com.br/api/clientes/busca_cpf?cpf=123<script>alert(1)" -w "\nHTTP: %{http_code}\n"
        echo "✅ Se HTTP 400, validação funcionando!"
        ;;
        
    "status"|"s")
        echo "📊 Status do sistema..."
        python ativar_service_layer.py status
        ;;
        
    "teste-completo"|"tc")
        echo "🔍 Executando testes completos..."
        ./scripts_testes_producao.sh
        ;;
        
    "ativar-service"|"as")
        echo "🚀 Ativando Service Layer..."
        python ativar_service_layer.py ativar
        ;;
        
    "desativar-service"|"ds")
        echo "🔄 Desativando Service Layer..."
        python ativar_service_layer.py desativar
        ;;
        
    "logs"|"l")
        echo "📋 Logs recentes..."
        sudo journalctl -u form_google --no-pager -n 20 | tail -10
        ;;
        
    "restart"|"r")
        echo "🔄 Reiniciando aplicação..."
        sudo systemctl restart form_google
        echo "✅ Reiniciado. Aguarde alguns segundos..."
        ;;
        
    "monitor"|"m")
        echo "👁️  Monitorando aplicação (Ctrl+C para parar)..."
        sudo journalctl -f -u form_google
        ;;
        
    "health"|"h")
        echo "💗 Verificando saúde..."
        curl -s -w "HTTP: %{http_code}\n" -o /dev/null https://appform.estevaoalmeida.com.br/
        echo "✅ Se HTTP 200/302, sistema ok!"
        ;;
        
    "backup"|"b")
        echo "💾 Fazendo backup rápido..."
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        sudo -u postgres pg_dump form_google > "$BACKUP_FILE"
        echo "✅ Backup salvo em: $BACKUP_FILE"
        ;;
        
    "arquivos"|"a")
        echo "📁 Verificando arquivos implementados..."
        for file in "app/validators/cliente_validator.py" "app/peticionador/services/suspensao_service.py" "app/peticionador/services/formulario_service.py" "app/peticionador/services/documento_service.py"; do
            if [ -f "$file" ]; then
                LINES=$(wc -l < "$file")
                echo "✅ $file ($LINES linhas)"
            else
                echo "❌ $file (AUSENTE)"
            fi
        done
        ;;
        
    "performance"|"p")
        echo "⚡ Teste de performance..."
        for i in {1..3}; do
            echo "Teste $i:"
            time curl -s https://appform.estevaoalmeida.com.br/api/clientes/busca_cpf?cpf=123.456.789-00 > /dev/null
        done
        ;;
        
    *)
        echo "📖 USO: $0 [comando]"
        echo ""
        echo "COMANDOS DISPONÍVEIS:"
        echo "  teste-rapido (tr)     - Teste rápido de segurança"
        echo "  status (s)           - Status da aplicação"
        echo "  teste-completo (tc)  - Bateria completa de testes"
        echo "  ativar-service (as)  - Ativar Service Layer"
        echo "  desativar-service (ds) - Desativar Service Layer"
        echo "  logs (l)             - Ver logs recentes"
        echo "  restart (r)          - Reiniciar aplicação"
        echo "  monitor (m)          - Monitorar logs em tempo real"
        echo "  health (h)           - Verificar saúde básica"
        echo "  backup (b)           - Backup rápido do banco"
        echo "  arquivos (a)         - Verificar arquivos implementados"
        echo "  performance (p)      - Teste de performance"
        echo ""
        echo "EXEMPLOS:"
        echo "  $0 tr                # Teste rápido"
        echo "  $0 status            # Ver status"
        echo "  $0 ativar-service    # Ativar melhorias"
        ;;
esac 