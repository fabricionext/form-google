#!/usr/bin/env python3
"""
Script de teste para verificar a configuração do Grafana Loki
"""
import os
import sys
import time
from unittest import mock

import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from loki_logger import (
    log_document_generation,
    log_google_api_operation,
    setup_loki_logging,
)


def check_loki_connection():
    """Testa a conexão com o Loki"""
    print("🔧 Testando conexão com Loki...")

    try:
        # Tentar conectar com o Loki
        response = requests.get("http://localhost:3100/ready", timeout=5)
        if response.status_code == 200:
            print("✅ Loki está rodando e acessível!")
            return True
        else:
            print(f"❌ Loki retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao Loki")
        print("💡 Certifique-se de que o Loki está rodando:")
        print("   ./start_monitoring.sh")
        return False
    except Exception as e:
        print(f"❌ Erro ao conectar com Loki: {e}")
        return False


def check_grafana_connection():
    """Testa a conexão com o Grafana"""
    print("\n📊 Testando conexão com Grafana...")

    try:
        # Tentar conectar com o Grafana
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Grafana está rodando e acessível!")
            return True
        else:
            print(f"❌ Grafana retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao Grafana")
        print("💡 Certifique-se de que o Grafana está rodando:")
        print("   ./start_monitoring.sh")
        return False
    except Exception as e:
        print(f"❌ Erro ao conectar com Grafana: {e}")
        return False


def perform_logging_functions():
    """Testa as funções de logging"""
    print("\n📝 Testando funções de logging...")

    try:
        # Configurar logging
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

    except Exception as e:
        print(f"❌ Erro ao testar logging: {e}")
        return False


def perform_log_retrieval():
    """Testa a recuperação de logs via API do Loki"""
    print("\n🔍 Testando recuperação de logs...")

    try:
        # Aguardar um pouco para os logs serem processados
        time.sleep(2)

        # Query para buscar logs recentes
        query = '{app="form-google"}'
        response = requests.get(
            "http://localhost:3100/loki/api/v1/query_range",
            params={
                "query": query,
                "start": int((time.time() - 300) * 1e9),  # 5 minutos atrás
                "end": int(time.time() * 1e9),  # agora
                "step": "1s",
            },
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            if "data" in data and "result" in data["data"]:
                log_count = len(data["data"]["result"])
                print(f"✅ Encontrados {log_count} streams de log")

                # Mostrar alguns logs de exemplo
                for i, stream in enumerate(data["data"]["result"][:3]):
                    print(f"   Stream {i+1}: {stream['stream']}")
                    if "values" in stream and stream["values"]:
                        latest_log = stream["values"][-1]
                        print(f"   Último log: {latest_log[1][:100]}...")
            else:
                print(
                    "⚠️  Nenhum log encontrado (pode ser normal se não houver logs recentes)"
                )
        else:
            print(f"❌ Erro ao buscar logs: {response.status_code}")

        return True

    except Exception as e:
        print(f"❌ Erro ao testar recuperação de logs: {e}")
        return False


def main():
    """Função principal de teste"""
    print("🧪 Iniciando testes do Grafana Loki...\n")

    # Teste 1: Conexão com Loki
    if not check_loki_connection():
        print("\n❌ Teste de conexão com Loki falhou.")
        print("💡 Execute: ./start_monitoring.sh")
        return

    # Teste 2: Conexão com Grafana
    if not check_grafana_connection():
        print("\n❌ Teste de conexão com Grafana falhou.")
        print("💡 Execute: ./start_monitoring.sh")
        return

    # Teste 3: Funções de logging
    if not perform_logging_functions():
        print("\n❌ Teste de logging falhou.")
        return

    # Teste 4: Recuperação de logs
    perform_log_retrieval()

    print("\n🎉 Todos os testes do Grafana Loki foram executados!")
    print("\n📊 Para verificar os resultados:")
    print("1. Acesse Grafana: http://localhost:3000")
    print("2. Login: admin / admin")
    print("3. Vá para 'Explore'")
    print("4. Selecione 'Loki' como fonte de dados")
    print('5. Use a query: {app="form-google"}')
    print("6. Você deve ver os logs de teste")


if __name__ == "__main__":
    main()


def test_loki(monkeypatch):
    """Executa o fluxo de testes do Loki sem acesso à rede."""

    def fake_get(*args, **kwargs):
        resp = mock.Mock()
        resp.status_code = 200
        resp.json.return_value = {}
        resp.text = "ok"
        return resp

    def fake_post(*args, **kwargs):
        resp = mock.Mock()
        resp.status_code = 204
        return resp

    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    assert check_loki_connection()
    assert check_grafana_connection()
    assert perform_logging_functions()
    assert perform_log_retrieval()
