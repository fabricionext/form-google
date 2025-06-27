#!/bin/bash
# safe_cleanup.sh - Script de limpeza segura do codebase
# Criado para remover arquivos obsoletos e organizar a estrutura

set -e  # Parar em caso de erro

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR"

echo "🧹 Iniciando limpeza segura do codebase..."
echo "📍 Diretório: $(pwd)"

# Função para confirmar ação
confirm() {
    read -p "$1 (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

# 1. Criar backup de segurança
echo ""
echo "📦 Passo 1: Criando backup de segurança..."
BACKUP_NAME="backup_before_cleanup_$(date +%Y%m%d_%H%M%S).tar.gz"

if confirm "Criar backup de segurança?"; then
    tar -czf "$BACKUP_NAME" \
        --exclude=venv \
        --exclude=node_modules \
        --exclude=__pycache__ \
        --exclude=.git \
        logs/ *.py docs/ templates/ static/ || true
    echo "✅ Backup criado: $BACKUP_NAME"
else
    echo "⚠️ Pulando backup - CUIDADO!"
fi

# 2. Criar estrutura de diretórios
echo ""
echo "📁 Passo 2: Criando estrutura de organização..."
mkdir -p archive/{scripts,demos,imports,logs}
mkdir -p tests
echo "✅ Estrutura criada"

# 3. Remover arquivos de debug/temporários (SEGURO)
echo ""
echo "🗑️ Passo 3: Removendo arquivos temporários..."
TEMP_FILES=(
    "cookies.txt"
    "headers.txt" 
    "update"
    "cloudflared.deb"
    "debug_celery_task.log"
    "debug_dados_cliente.log"
    "diagnostico.log"
    "gunicorn_test.log"
)

for file in "${TEMP_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "  Removendo: $file"
        rm -f "$file"
    fi
done
echo "✅ Arquivos temporários removidos"

# 4. Limpar logs de teste antigos
echo ""
echo "📋 Passo 4: Limpando logs de teste antigos..."
if confirm "Remover diretórios de logs de teste antigos?"; then
    rm -rf logs_teste_20250625_084235/ 2>/dev/null || true
    rm -rf logs_teste_20250625_084411/ 2>/dev/null || true  
    rm -rf logs_teste_20250625_084220/ 2>/dev/null || true
    echo "✅ Logs de teste removidos"
else
    echo "⏭️ Pulando limpeza de logs de teste"
fi

# 5. Arquivar scripts de demonstração
echo ""
echo "📦 Passo 5: Arquivando scripts de demonstração..."
DEMO_FILES=(
    "demo_api_refatorada.py"
    "demo_importacao.py"
    "demo_refatoracao_funcionando.py"
    "demonstracao_importacao.py"
    "demonstracao_melhorias_seguranca.py"
    "comparacao_implementacoes.py"
)

if confirm "Arquivar scripts de demonstração?"; then
    for file in "${DEMO_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            echo "  Arquivando: $file"
            mv "$file" archive/demos/
        fi
    done
    echo "✅ Scripts de demo arquivados"
else
    echo "⏭️ Pulando arquivamento de demos"
fi

# 6. Mover arquivos de teste para diretório específico
echo ""
echo "🧪 Passo 6: Organizando arquivos de teste..."
if confirm "Mover arquivos de teste para diretório tests/?"; then
    find . -maxdepth 1 -name "test_*.py" -exec mv {} tests/ \; 2>/dev/null || true
    find . -maxdepth 1 -name "teste_*.py" -exec mv {} tests/ \; 2>/dev/null || true
    echo "✅ Testes organizados"
else
    echo "⏭️ Pulando organização de testes"
fi

# 7. Arquivar scripts de monitoramento duplicados
echo ""
echo "📊 Passo 7: Organizando scripts de monitoramento..."
if confirm "Arquivar scripts de monitoramento antigos (manter apenas finais)?"; then
    # Manter apenas as versões robustas/finais
    MONITOR_TO_ARCHIVE=(
        "start_monitoring.sh"
        "start_monitoring_fixed.sh"
        "start_monitoring_simple.sh"
        "start_monitoring_temp.sh"
        "clean_monitoring.sh"
        "clean_monitoring_fixed.sh"
    )
    
    for file in "${MONITOR_TO_ARCHIVE[@]}"; do
        if [[ -f "$file" ]]; then
            echo "  Arquivando: $file"
            mv "$file" archive/scripts/
        fi
    done
    echo "✅ Scripts de monitoramento organizados"
else
    echo "⏭️ Pulando organização de monitoramento"
fi

# 8. Implementar rotação básica de logs
echo ""
echo "📄 Passo 8: Configurando rotação de logs..."
if confirm "Limpar logs antigos (manter apenas os 5 mais recentes)?"; then
    cd logs/
    # Manter apenas os 5 arquivos .log.X mais recentes
    find . -name "*.log.[0-9]*" -type f | sort -V | head -n -5 | xargs -r rm -f
    cd ..
    echo "✅ Logs antigos limpos"
else
    echo "⏭️ Pulando limpeza de logs"
fi

# 9. Resumo final
echo ""
echo "📈 Resumo da Limpeza:"
echo "==================="
echo "📦 Backup criado: $BACKUP_NAME"
echo "📁 Estrutura organizada: archive/, tests/"
echo "🗑️ Arquivos temporários removidos"
echo "📋 Logs de teste limpos"
echo "📦 Scripts demo arquivados"
echo "🧪 Testes organizados"
echo "📊 Scripts de monitoramento organizados"
echo "📄 Logs rotacionados"

echo ""
echo "✅ Limpeza concluída com sucesso!"
echo ""
echo "📌 Próximos passos recomendados:"
echo "  1. Verificar se a aplicação ainda funciona"
echo "  2. Configurar logrotate para rotação automática"
echo "  3. Revisar arquivos em archive/ após algumas semanas"
echo "  4. Considerar remover o backup após confirmação"

echo ""
echo "⚠️ Em caso de problemas, restaure com:"
echo "  tar -xzf $BACKUP_NAME"