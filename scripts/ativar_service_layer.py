#!/usr/bin/env python3
"""
Script para ativar/desativar a camada de serviços de forma segura
"""

import os
import sys
import subprocess
import time
from datetime import datetime

def log_colored(message, color="green"):
    """Log com cores"""
    colors = {
        "green": "\033[32m",
        "red": "\033[31m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, '')}{message}{colors['reset']}")

def check_application_health():
    """Verifica se a aplicação está saudável"""
    try:
        result = subprocess.run([
            "curl", "-s", "-w", "%{http_code}", 
            "-o", "/dev/null", 
            "https://appform.estevaoalmeida.com.br/", 
            "--max-time", "10"
        ], capture_output=True, text=True)
        
        http_code = result.stdout.strip()
        return http_code in ["200", "302"]
    except Exception as e:
        log_colored(f"Erro ao verificar saúde: {e}", "red")
        return False

def test_cpf_validation():
    """Testa validação de CPF"""
    try:
        # Teste CPF malicioso
        result = subprocess.run([
            "curl", "-s", "-w", "%{http_code}",
            "-o", "/dev/null",
            "https://appform.estevaoalmeida.com.br/api/clientes/busca_cpf?cpf=123<script>alert(1)",
            "--max-time", "10"
        ], capture_output=True, text=True)
        
        return result.stdout.strip() == "400"
    except Exception as e:
        log_colored(f"Erro ao testar CPF: {e}", "red")
        return False

def set_feature_flag(enabled=True):
    """Define o feature flag"""
    flag_value = "true" if enabled else "false"
    os.environ["USE_SERVICE_LAYER"] = flag_value
    log_colored(f"Feature flag USE_SERVICE_LAYER = {flag_value}", "blue")

def restart_application():
    """Reinicia a aplicação"""
    try:
        log_colored("Reiniciando aplicação...", "yellow")
        
        # Parar aplicação
        subprocess.run(["sudo", "systemctl", "stop", "form_google"], check=True)
        time.sleep(2)
        
        # Iniciar aplicação
        subprocess.run(["sudo", "systemctl", "start", "form_google"], check=True)
        time.sleep(5)
        
        log_colored("Aplicação reiniciada", "green")
        return True
        
    except subprocess.CalledProcessError as e:
        log_colored(f"Erro ao reiniciar aplicação: {e}", "red")
        return False

def monitor_logs(duration=30):
    """Monitora logs por um período"""
    log_colored(f"Monitorando logs por {duration} segundos...", "blue")
    
    try:
        process = subprocess.Popen([
            "sudo", "journalctl", "-f", "-u", "form_google"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        start_time = time.time()
        errors = []
        
        while time.time() - start_time < duration:
            line = process.stdout.readline()
            if line:
                print(line.strip())
                if "ERROR" in line:
                    errors.append(line.strip())
            
            # Verificar se processo ainda está rodando
            if process.poll() is not None:
                break
        
        process.terminate()
        
        if errors:
            log_colored(f"⚠️  {len(errors)} erros detectados nos logs", "yellow")
            return False
        else:
            log_colored("✅ Logs normais - sem erros críticos", "green")
            return True
            
    except Exception as e:
        log_colored(f"Erro ao monitorar logs: {e}", "red")
        return False

def activate_service_layer():
    """Ativa a camada de serviços"""
    log_colored("🚀 ATIVANDO CAMADA DE SERVIÇOS", "blue")
    
    # 1. Verificar saúde inicial
    if not check_application_health():
        log_colored("❌ Aplicação não está saudável - abortando", "red")
        return False
    
    # 2. Testar validação de segurança
    if not test_cpf_validation():
        log_colored("❌ Validação de segurança falhando - abortando", "red")
        return False
    
    log_colored("✅ Testes pré-ativação passaram", "green")
    
    # 3. Ativar feature flag
    set_feature_flag(True)
    
    # 4. Reiniciar aplicação
    if not restart_application():
        log_colored("❌ Falha ao reiniciar - fazendo rollback", "red")
        rollback_service_layer()
        return False
    
    # 5. Verificar saúde pós-ativação
    time.sleep(10)  # Dar tempo para inicializar
    
    if not check_application_health():
        log_colored("❌ Aplicação não está saudável após ativação - fazendo rollback", "red")
        rollback_service_layer()
        return False
    
    # 6. Monitorar logs
    if not monitor_logs(30):
        log_colored("⚠️  Erros detectados nos logs - considere rollback", "yellow")
    
    log_colored("✅ CAMADA DE SERVIÇOS ATIVADA COM SUCESSO!", "green")
    return True

def rollback_service_layer():
    """Faz rollback da camada de serviços"""
    log_colored("🔄 FAZENDO ROLLBACK DA CAMADA DE SERVIÇOS", "yellow")
    
    # 1. Desativar feature flag
    set_feature_flag(False)
    
    # 2. Reiniciar aplicação
    if restart_application():
        # 3. Verificar saúde
        time.sleep(10)
        if check_application_health():
            log_colored("✅ ROLLBACK CONCLUÍDO COM SUCESSO", "green")
            return True
    
    log_colored("❌ ROLLBACK FALHOU - INTERVENÇÃO MANUAL NECESSÁRIA", "red")
    return False

def status_service_layer():
    """Verifica status da camada de serviços"""
    log_colored("📊 STATUS DA CAMADA DE SERVIÇOS", "blue")
    
    # Verificar feature flag
    flag_value = os.environ.get("USE_SERVICE_LAYER", "false")
    log_colored(f"Feature Flag: {flag_value}", "blue")
    
    # Verificar saúde
    health = check_application_health()
    status = "✅ Saudável" if health else "❌ Com problemas"
    log_colored(f"Saúde da aplicação: {status}", "green" if health else "red")
    
    # Verificar segurança
    security = test_cpf_validation()
    sec_status = "✅ Funcionando" if security else "❌ Com problemas"
    log_colored(f"Validação de segurança: {sec_status}", "green" if security else "red")
    
    return health and security

def main():
    if len(sys.argv) < 2:
        print("Uso: python ativar_service_layer.py [ativar|desativar|status]")
        print("  ativar   - Ativa a camada de serviços")
        print("  desativar - Desativa a camada de serviços (rollback)")
        print("  status   - Verifica status atual")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_colored(f"🕐 Iniciando operação '{action}' às {timestamp}", "blue")
    
    if action == "ativar":
        success = activate_service_layer()
        sys.exit(0 if success else 1)
        
    elif action == "desativar":
        success = rollback_service_layer()
        sys.exit(0 if success else 1)
        
    elif action == "status":
        success = status_service_layer()
        sys.exit(0 if success else 1)
        
    else:
        log_colored(f"Ação '{action}' não reconhecida", "red")
        sys.exit(1)

if __name__ == "__main__":
    main() 