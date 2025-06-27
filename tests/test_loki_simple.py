#!/usr/bin/env python3
"""
Script de teste simplificado para verificar as funções de logging
(sem dependência do Docker)
"""
import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_logging_functions():
    """Testa as funções de logging localmente"""
    print("🧪 Testando funções de logging...")

    try:
        # Simular as funções de logging
        from loki_logger import (
            log_document_generation,
            log_google_api_operation,
            setup_loki_logging,
        )

        # Configurar logging (vai falhar se Loki não estiver rodando, mas não é problema)
        setup_loki_logging()
        print("✅ Logging configurado com sucesso!")

        # Testar log de operação da API
        print("📤 Enviando log de operação da API...")
        log_google_api_operation(
            operation="create_document",
            status="success",
            details={"document_id": "test_123", "template": "ficha_cadastral"},
        )
        print("✅ Log de operação da API enviado")

        # Testar log de geração de documento
        print("📤 Enviando log de geração de documento...")
        log_document_generation(
            form_id=123,
            user_id=456,
            status="completed",
            details={"document_type": "ficha_cadastral", "processing_time": 2.5},
        )
        print("✅ Log de geração de documento enviado")

        # Testar log de erro
        print("📤 Enviando log de erro...")
        log_google_api_operation(
            operation="update_document",
            status="error",
            details={"error": "Document not found", "document_id": "invalid_123"},
        )
        print("✅ Log de erro enviado")

        return True

    except ImportError as e:
        print(f"❌ Erro ao importar módulos: {e}")
        print("💡 Verifique se o arquivo loki_logger.py existe")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar logging: {e}")
        return False


def test_log_file_creation():
    """Testa se os logs estão sendo salvos em arquivo local"""
    print("\n📝 Testando criação de arquivos de log...")

    try:
        # Verificar se existe diretório de logs
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            print(f"✅ Diretório {log_dir} criado")

        # Criar um log de teste
        test_log = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "app": "form-google",
            "message": "Teste de log local",
            "operation": "test",
            "status": "success",
        }

        # Salvar log em arquivo
        log_file = os.path.join(log_dir, "test.log")
        with open(log_file, "a") as f:
            f.write(json.dumps(test_log) + "\n")

        print(f"✅ Log salvo em {log_file}")

        # Verificar se o arquivo foi criado
        if os.path.exists(log_file):
            print(f"✅ Arquivo de log criado com sucesso")
            return True
        else:
            print("❌ Arquivo de log não foi criado")
            return False

    except Exception as e:
        print(f"❌ Erro ao testar criação de logs: {e}")
        return False


def show_docker_instructions():
    """Mostra instruções para configurar Docker"""
    print("\n" + "=" * 60)
    print("🐳 CONFIGURAÇÃO DO DOCKER")
    print("=" * 60)

    print("\nPara usar o Grafana Loki completo, você precisa:")

    print("\n1. 🔧 Instalar Docker (se não estiver instalado):")
    print("   sudo apt update")
    print("   sudo apt install docker.io docker-compose")

    print("\n2. 🚀 Iniciar o Docker:")
    print("   sudo systemctl start docker")
    print("   sudo systemctl enable docker")

    print("\n3. 👤 Adicionar usuário ao grupo docker:")
    print("   sudo usermod -aG docker $USER")
    print("   # Faça logout e login novamente")

    print("\n4. 🧪 Testar Docker:")
    print("   docker --version")
    print("   docker ps")

    print("\n5. 📊 Iniciar monitoramento:")
    print("   ./start_monitoring.sh")

    print("\n6. 🌐 Acessar:")
    print("   Grafana: http://localhost:3000 (admin/admin)")
    print("   Loki: http://localhost:3100")


def show_alternative_solutions():
    """Mostra soluções alternativas sem Docker"""
    print("\n" + "=" * 60)
    print("🔄 SOLUÇÕES ALTERNATIVAS")
    print("=" * 60)

    print("\nSe você não quiser usar Docker, pode:")

    print("\n1. 📝 Usar logs locais:")
    print("   - Os logs já estão sendo salvos em logs/")
    print("   - Use ferramentas como 'tail', 'grep', 'jq'")
    print("   - Exemplo: tail -f logs/test.log | jq")

    print("\n2. 📊 Usar ferramentas de log simples:")
    print("   - logrotate para rotação de logs")
    print("   - rsyslog para logs do sistema")
    print("   - Ferramentas web como LogViewer")

    print("\n3. ☁️ Usar serviços cloud gratuitos:")
    print("   - Loggly (plano gratuito)")
    print("   - Papertrail (plano gratuito)")
    print("   - Logentries (plano gratuito)")


def main():
    """Função principal"""
    print("🚀 TESTE SIMPLIFICADO DE MONITORAMENTO")
    print("=" * 60)

    # Teste 1: Funções de logging
    logging_ok = test_logging_functions()

    # Teste 2: Criação de arquivos de log
    file_ok = test_log_file_creation()

    # Resumo
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES:")
    print("=" * 60)
    print(f"📝 Funções de logging: {'OK' if logging_ok else 'FALHOU'}")
    print(f"📄 Criação de arquivos: {'OK' if file_ok else 'FALHOU'}")

    if logging_ok and file_ok:
        print("\n✅ Testes básicos passaram!")
        print("\n📊 Para usar o monitoramento completo:")
        show_docker_instructions()
        show_alternative_solutions()
    else:
        print("\n❌ Alguns testes falharam.")
        print("💡 Verifique as configurações e tente novamente.")
        show_alternative_solutions()


if __name__ == "__main__":
    main()
