#!/bin/bash
# RESPOSTA DE EMERGÊNCIA CRÍTICA - RCE CONFIRMADO
# EXECUTE IMEDIATAMENTE: sudo bash emergency_response_CRITICAL.sh

echo "========== ALERTA CRÍTICO: RCE DETECTADO =========="
echo "Timestamp: $(date)"
echo "IPs realizando RCE via /device.rsp:"
echo "  47.121.194.82 - Script malicioso"
echo "  47.121.210.129 - Múltiplas tentativas" 
echo "  47.121.220.66 - Script malicioso"
echo "  141.255.162.250 - Malware download"
echo "  164.92.78.28 - PHP shell scanning"
echo "==============================================="

# Verificar se está executando como root
if [ "$EUID" -ne 0 ]; then
    echo "ERRO: Este script deve ser executado como root"
    echo "Execute: sudo bash $0"
    exit 1
fi

# Backup das regras atuais
echo "Fazendo backup das regras atuais..."
iptables-save > /tmp/iptables_emergency_backup_$(date +%Y%m%d_%H%M%S).rules

# IPs de RCE para bloqueio IMEDIATO
RCE_IPS=(
    "47.121.194.82"
    "47.121.210.129" 
    "47.121.220.66"
    "141.255.162.250"
    "164.92.78.28"
)

# Bloqueio imediato dos IPs de RCE
echo ""
echo "=== BLOQUEANDO IPS DE RCE IMEDIATAMENTE ==="
for ip in "${RCE_IPS[@]}"; do
    echo "BLOQUEANDO IP CRÍTICO: $ip"
    iptables -I INPUT 1 -s $ip -j DROP
    iptables -I INPUT 1 -s $ip -j LOG --log-prefix "BLOCKED-RCE-CRITICAL: "
    echo "  ✓ IP $ip BLOQUEADO"
done

# Bloqueio específico do endpoint /device.rsp
echo ""
echo "=== BLOQUEANDO ENDPOINT /device.rsp ==="
iptables -A INPUT -m string --string "/device.rsp" --algo bm -j DROP
iptables -A INPUT -m string --string "/device.rsp" --algo bm -j LOG --log-prefix "BLOCKED-DEVICE-RSP: "
echo "  ✓ Endpoint /device.rsp BLOQUEADO"

# Bloquear tentativas de download de scripts
echo ""
echo "=== BLOQUEANDO DOWNLOADS MALICIOSOS ==="
iptables -A OUTPUT -m string --string "wget" --algo bm -j DROP
iptables -A OUTPUT -m string --string "curl" --algo bm -j DROP
echo "  ✓ Downloads wget/curl BLOQUEADOS"

# Salvar regras
echo ""
echo "=== SALVANDO CONFIGURAÇÕES DE EMERGÊNCIA ==="
if command -v iptables-persistent &> /dev/null; then
    netfilter-persistent save
elif [ -f /etc/iptables/rules.v4 ]; then
    iptables-save > /etc/iptables/rules.v4
else
    iptables-save > /etc/iptables.rules
fi

echo ""
echo "========== BLOQUEIO DE EMERGÊNCIA CONCLUÍDO =========="
echo "AÇÕES TOMADAS:"
echo "  - 5 IPs de RCE bloqueados"
echo "  - Endpoint /device.rsp bloqueado" 
echo "  - Downloads maliciosos bloqueados"
echo ""
echo "PRÓXIMAS AÇÕES OBRIGATÓRIAS:"
echo "  1. Verificar se sistema foi comprometido"
echo "  2. Analisar logs de aplicação"
echo "  3. Implementar WAF/ModSecurity"
echo "  4. Atualizar Nginx com configuração de segurança"
echo ""
echo "MONITORE: tail -f /var/log/nginx/access.log"