#!/bin/bash
# Script de Emergência - Bloqueio Imediato de IPs Maliciosos
# Executar com privilégios de root: sudo bash emergency_firewall_rules.sh

echo "=== INICIANDO BLOQUEIO DE EMERGÊNCIA ==="
echo "Timestamp: $(date)"

# IPs com ataques de força bruta confirmados
BRUTE_FORCE_IPS=(
    "204.76.203.211"  # 70+ tentativas força bruta (ATIVO)
    "95.214.52.169"   # Múltiplas tentativas admin
    "152.42.166.7"    # Tentativas .env e .git/config
)

# IPs com tentativas de RCE/exploração
RCE_IPS=(
    "47.121.194.82"   # Tentativa RCE via device.rsp
    "47.121.210.129"  # Tentativa RCE via device.rsp  
    "47.121.220.66"   # Tentativa RCE via device.rsp
    "141.255.162.250" # Tentativa RCE via device.rsp
)

# IPs com reconnaissance/scanning
SCANNER_IPS=(
    "172.202.118.43"  # zgrab scanner
    "78.153.140.179"  # Tentativa acesso .env
    "202.83.55.203"   # masscan
    "74.235.140.14"   # zgrab scanner
    "164.92.78.28"    # Múltiplas tentativas exploração
    "194.165.16.167"  # Tentativa RDP
    "5.101.64.6"      # Múltiplas tentativas exploração
    "185.242.226.115" # Scanning ativo
)

# Função para bloquear IP
block_ip() {
    local ip=$1
    local reason=$2
    
    echo "Bloqueando IP: $ip ($reason)"
    
    # Adiciona regra de bloqueio no iptables
    iptables -I INPUT 1 -s $ip -j DROP
    
    # Adiciona comentário para tracking
    iptables -I INPUT 1 -s $ip -j LOG --log-prefix "BLOCKED-$reason: "
    
    echo "  ✓ IP $ip bloqueado"
}

# Verificar se está executando como root
if [ "$EUID" -ne 0 ]; then
    echo "ERRO: Este script deve ser executado como root"
    echo "Execute: sudo bash $0"
    exit 1
fi

# Backup das regras atuais
echo "Fazendo backup das regras atuais..."
iptables-save > /tmp/iptables_backup_$(date +%Y%m%d_%H%M%S).rules
echo "  ✓ Backup salvo em /tmp/"

# Bloquear IPs de força bruta
echo ""
echo "=== BLOQUEANDO IPS DE FORÇA BRUTA ==="
for ip in "${BRUTE_FORCE_IPS[@]}"; do
    block_ip "$ip" "BRUTE-FORCE"
done

# Bloquear IPs de RCE
echo ""
echo "=== BLOQUEANDO IPS DE RCE/EXPLORAÇÃO ==="
for ip in "${RCE_IPS[@]}"; do
    block_ip "$ip" "RCE-ATTEMPT"
done

# Bloquear IPs de scanning
echo ""
echo "=== BLOQUEANDO IPS DE RECONNAISSANCE ==="
for ip in "${SCANNER_IPS[@]}"; do
    block_ip "$ip" "SCANNER"
done

# Adicionar regras específicas de proteção
echo ""
echo "=== ADICIONANDO REGRAS DE PROTEÇÃO ==="

# Rate limiting usando iptables (básico)
echo "Configurando rate limiting..."
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT

# Bloquear tentativas de acesso a arquivos sensíveis
echo "Bloqueando acesso a arquivos sensíveis..."
iptables -A INPUT -m string --string "/.env" --algo bm -j DROP
iptables -A INPUT -m string --string "/.git" --algo bm -j DROP
iptables -A INPUT -m string --string "/device.rsp" --algo bm -j DROP

# Salvar regras para persistir após reboot
echo ""
echo "=== SALVANDO CONFIGURAÇÕES ==="
if command -v iptables-persistent &> /dev/null; then
    echo "Salvando com iptables-persistent..."
    netfilter-persistent save
elif [ -f /etc/iptables/rules.v4 ]; then
    echo "Salvando em /etc/iptables/rules.v4..."
    iptables-save > /etc/iptables/rules.v4
else
    echo "Salvando em /etc/iptables.rules..."
    iptables-save > /etc/iptables.rules
    echo "ATENÇÃO: Configure a restauração automática das regras no boot!"
fi

# Mostrar estatísticas
echo ""
echo "=== RESUMO DO BLOQUEIO ==="
echo "IPs bloqueados por força bruta: ${#BRUTE_FORCE_IPS[@]}"
echo "IPs bloqueados por RCE: ${#RCE_IPS[@]}"
echo "IPs bloqueados por scanning: ${#SCANNER_IPS[@]}"
echo "Total de IPs bloqueados: $((${#BRUTE_FORCE_IPS[@]} + ${#RCE_IPS[@]} + ${#SCANNER_IPS[@]}))"

echo ""
echo "=== REGRAS ATIVAS ==="
iptables -L INPUT -n --line-numbers | head -20

echo ""
echo "=== PRÓXIMOS PASSOS RECOMENDADOS ==="
echo "1. Implementar configuração Nginx com rate limiting"
echo "2. Ativar fail2ban para proteção automática"
echo "3. Configurar monitoramento de logs em tempo real"
echo "4. Considerar mudança de porta SSH se aplicável"
echo "5. Revisar logs de aplicação para possíveis compromissos"

echo ""
echo "=== BLOQUEIO DE EMERGÊNCIA CONCLUÍDO ==="
echo "Sistema protegido contra ataques conhecidos."
echo "Monitore logs continuamente: tail -f /var/log/nginx/security.log"