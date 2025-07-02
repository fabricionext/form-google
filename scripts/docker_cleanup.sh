#!/bin/bash

# Script de Limpeza Automática do Docker
# Autor: Sistema ADV
# Versão: 1.0
# Data: $(date +%Y-%m-%d)

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configurações
LOG_FILE="/var/log/docker-cleanup.log"
MAX_LOG_SIZE="10M"
DRY_RUN=false
VERBOSE=false

# Função para logging
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        "DEBUG")
            if [ "$VERBOSE" = true ]; then
                echo -e "${BLUE}[DEBUG]${NC} $message"
            fi
            ;;
    esac
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Função para mostrar uso
show_usage() {
    echo "Uso: $0 [OPÇÕES]"
    echo ""
    echo "Opções:"
    echo "  -d, --dry-run     Executa em modo simulação (não remove nada)"
    echo "  -v, --verbose     Mostra informações detalhadas"
    echo "  -h, --help        Mostra esta ajuda"
    echo "  -l, --log-file    Especifica arquivo de log (padrão: $LOG_FILE)"
    echo ""
    echo "Exemplos:"
    echo "  $0                 # Executa limpeza normal"
    echo "  $0 -d              # Modo simulação"
    echo "  $0 -v              # Modo verboso"
    echo "  $0 -d -v           # Simulação verbosa"
}

# Função para verificar se Docker está rodando
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log "ERROR" "Docker não está rodando ou não há permissão"
        exit 1
    fi
    log "INFO" "Docker está rodando"
}

# Função para verificar espaço antes da limpeza
check_space_before() {
    log "INFO" "=== ESPAÇO ANTES DA LIMPEZA ==="
    docker system df | while read line; do
        log "DEBUG" "$line"
    done
    
    # Capturar espaço total usado
    local total_space=$(docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}" | grep "Images" | awk '{print $3}')
    log "INFO" "Espaço total usado: $total_space"
}

# Função para verificar espaço após a limpeza
check_space_after() {
    log "INFO" "=== ESPAÇO APÓS A LIMPEZA ==="
    docker system df | while read line; do
        log "DEBUG" "$line"
    done
    
    # Capturar espaço total usado
    local total_space=$(docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}\t{{.Reclaimable}}" | grep "Images" | awk '{print $3}')
    log "INFO" "Espaço total usado: $total_space"
}

# Função para limpar imagens órfãs
cleanup_dangling_images() {
    log "INFO" "Limpando imagens órfãs..."
    
    local dangling_images=$(docker images --filter "dangling=true" -q)
    
    if [ -z "$dangling_images" ]; then
        log "INFO" "Nenhuma imagem órfã encontrada"
        return 0
    fi
    
    local count=$(echo "$dangling_images" | wc -l)
    log "INFO" "Encontradas $count imagem(s) órfã(s)"
    
    if [ "$DRY_RUN" = true ]; then
        log "WARN" "DRY RUN: As seguintes imagens seriam removidas:"
        docker images --filter "dangling=true" --format "table {{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}"
        return 0
    fi
    
    # Remover imagens órfãs
    local removed_count=0
    for image_id in $dangling_images; do
        if docker rmi "$image_id" >/dev/null 2>&1; then
            log "DEBUG" "Imagem removida: $image_id"
            ((removed_count++))
        else
            log "WARN" "Falha ao remover imagem: $image_id"
        fi
    done
    
    log "INFO" "Removidas $removed_count imagem(s) órfã(s)"
}

# Função para limpar containers parados
cleanup_stopped_containers() {
    log "INFO" "Limpando containers parados..."
    
    local stopped_containers=$(docker ps -a --filter "status=exited" --filter "status=created" -q)
    
    if [ -z "$stopped_containers" ]; then
        log "INFO" "Nenhum container parado encontrado"
        return 0
    fi
    
    local count=$(echo "$stopped_containers" | wc -l)
    log "INFO" "Encontrados $count container(s) parado(s)"
    
    if [ "$DRY_RUN" = true ]; then
        log "WARN" "DRY RUN: Os seguintes containers seriam removidos:"
        docker ps -a --filter "status=exited" --filter "status=created" --format "table {{.Names}}\t{{.Status}}\t{{.Size}}"
        return 0
    fi
    
    # Remover containers parados
    local removed_count=0
    for container_id in $stopped_containers; do
        if docker rm "$container_id" >/dev/null 2>&1; then
            log "DEBUG" "Container removido: $container_id"
            ((removed_count++))
        else
            log "WARN" "Falha ao remover container: $container_id"
        fi
    done
    
    log "INFO" "Removidos $removed_count container(s) parado(s)"
}

# Função para limpar redes não utilizadas
cleanup_unused_networks() {
    log "INFO" "Limpando redes não utilizadas..."
    
    local unused_networks=$(docker network ls --filter "type=custom" -q)
    
    if [ -z "$unused_networks" ]; then
        log "INFO" "Nenhuma rede não utilizada encontrada"
        return 0
    fi
    
    local count=$(echo "$unused_networks" | wc -l)
    log "INFO" "Encontradas $count rede(s) não utilizada(s)"
    
    if [ "$DRY_RUN" = true ]; then
        log "WARN" "DRY RUN: As seguintes redes seriam removidas:"
        docker network ls --filter "type=custom" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
        return 0
    fi
    
    # Remover redes não utilizadas
    local removed_count=0
    for network_id in $unused_networks; do
        if docker network rm "$network_id" >/dev/null 2>&1; then
            log "DEBUG" "Rede removida: $network_id"
            ((removed_count++))
        else
            log "WARN" "Falha ao remover rede: $network_id"
        fi
    done
    
    log "INFO" "Removidas $removed_count rede(s) não utilizada(s)"
}

# Função para limpar volumes não utilizados
cleanup_unused_volumes() {
    log "INFO" "Limpando volumes não utilizados..."
    
    if [ "$DRY_RUN" = true ]; then
        log "WARN" "DRY RUN: Volumes que seriam removidos:"
        docker volume ls -qf dangling=true
        return 0
    fi
    
    # Remover volumes órfãos
    local removed_volumes=$(docker volume prune -f 2>/dev/null | grep "Total reclaimed space" | awk '{print $4}')
    
    if [ -n "$removed_volumes" ]; then
        log "INFO" "Volumes removidos: $removed_volumes"
    else
        log "INFO" "Nenhum volume não utilizado encontrado"
    fi
}

# Função para limpar cache de build
cleanup_build_cache() {
    log "INFO" "Limpando cache de build..."
    
    if [ "$DRY_RUN" = true ]; then
        log "WARN" "DRY RUN: Cache de build seria limpo"
        return 0
    fi
    
    # Limpar cache de build
    local reclaimed_space=$(docker system prune -f 2>/dev/null | grep "Total reclaimed space" | awk '{print $4}')
    
    if [ -n "$reclaimed_space" ]; then
        log "INFO" "Cache de build limpo: $reclaimed_space"
    else
        log "INFO" "Nenhum cache de build para limpar"
    fi
}

# Função para limpar logs antigos
cleanup_old_logs() {
    log "INFO" "Limpando logs antigos..."
    
    if [ -f "$LOG_FILE" ]; then
        local log_size=$(du -h "$LOG_FILE" | cut -f1)
        log "DEBUG" "Tamanho atual do log: $log_size"
        
        # Se o log for maior que MAX_LOG_SIZE, truncar
        if [ "$(du -b "$LOG_FILE" | cut -f1)" -gt "$(numfmt --from=iec $MAX_LOG_SIZE)" ]; then
            if [ "$DRY_RUN" = true ]; then
                log "WARN" "DRY RUN: Log seria truncado (tamanho: $log_size)"
            else
                # Manter apenas as últimas 1000 linhas
                tail -n 1000 "$LOG_FILE" > "${LOG_FILE}.tmp" && mv "${LOG_FILE}.tmp" "$LOG_FILE"
                log "INFO" "Log truncado para 1000 linhas"
            fi
        fi
    fi
}

# Função principal de limpeza
main_cleanup() {
    log "INFO" "=== INICIANDO LIMPEZA DO DOCKER ==="
    log "INFO" "Data/Hora: $(date)"
    log "INFO" "Modo DRY RUN: $DRY_RUN"
    log "INFO" "Modo VERBOSE: $VERBOSE"
    
    # Verificar Docker
    check_docker
    
    # Verificar espaço antes
    check_space_before
    
    # Executar limpezas
    cleanup_dangling_images
    cleanup_stopped_containers
    cleanup_unused_networks
    cleanup_unused_volumes
    cleanup_build_cache
    
    # Verificar espaço após
    check_space_after
    
    # Limpar logs antigos
    cleanup_old_logs
    
    log "INFO" "=== LIMPEZA CONCLUÍDA ==="
}

# Função para criar diretório de log se não existir
setup_logging() {
    local log_dir=$(dirname "$LOG_FILE")
    if [ ! -d "$log_dir" ]; then
        mkdir -p "$log_dir"
    fi
    
    # Criar arquivo de log se não existir
    if [ ! -f "$LOG_FILE" ]; then
        touch "$LOG_FILE"
    fi
}

# Função para verificar permissões
check_permissions() {
    if [ "$EUID" -ne 0 ] && ! groups | grep -q docker; then
        log "ERROR" "Este script precisa ser executado como root ou o usuário precisa estar no grupo docker"
        exit 1
    fi
}

# Parse de argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        -l|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        *)
            log "ERROR" "Opção desconhecida: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Configuração inicial
setup_logging
check_permissions

# Executar limpeza
main_cleanup

exit 0 