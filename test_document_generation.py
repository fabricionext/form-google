#!/usr/bin/env python3
"""
Script de teste para verificar a geração de documentos.
"""
import json
import time
from unittest import mock

import requests


def perform_document_generation():
    """Testa a geração de documentos via API"""

    # URL da API
    url = "https://appform.estevaoalmeida.com.br/api/gerar-documento"

    # Dados de teste
    test_data = {
        "tipoPessoa": "pf",
        "dadosCliente": {
            "primeiroNome": "João",
            "sobrenome": "Silva",
            "email": "joao.silva@teste.com",
            "cpf": "12345678901",
            "rg": "123456789",
            "dataNascimento": "15/03/1990",
            "telefoneCelular": "11987654321",
            "logradouro": "Rua das Flores",
            "numero": "123",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
            "cep": "01234567",
            "nacionalidade": "Brasileiro",
            "estadoCivil": "Solteiro",
            "profissao": "Advogado",
        },
    }

    # Headers
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "test-key",  # Substitua pela chave real
    }

    print("🔄 Enviando requisição para geração de documentos...")
    print(f"📤 Dados: {json.dumps(test_data, indent=2)}")

    try:
        # Fazer a requisição
        response = requests.post(url, json=test_data, headers=headers, timeout=30)

        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Response: {response.text}")

        if response.status_code == 202:
            # Se foi aceito, verificar o status da tarefa
            task_data = response.json()
            task_id = task_data.get("task_id")

            if task_id:
                print(f"✅ Tarefa enfileirada com ID: {task_id}")
                print("🔄 Aguardando processamento...")

                # Aguardar um pouco e verificar o status
                time.sleep(5)

                status_url = (
                    f"https://appform.estevaoalmeida.com.br/api/task-status/{task_id}"
                )
                status_response = requests.get(status_url, headers=headers)

                print(f"📊 Status da tarefa: {status_response.status_code}")
                print(f"📊 Resposta: {status_response.text}")

        return response.status_code == 202 or response.status_code == 200

    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Iniciando teste de geração de documentos...")
    success = perform_document_generation()

    if success:
        print("✅ Teste concluído com sucesso!")
    else:
        print("❌ Teste falhou!")


def test_document_generation(monkeypatch):
    """Testa geração de documentos sem realizar chamadas HTTP reais."""

    def fake_post(*args, **kwargs):
        response = mock.Mock()
        response.status_code = 202
        response.text = "accepted"
        response.json.return_value = {"task_id": "123"}
        return response

    def fake_get(*args, **kwargs):
        response = mock.Mock()
        response.status_code = 200
        response.text = "completed"
        return response

    monkeypatch.setattr(requests, "post", fake_post)
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(time, "sleep", lambda x: None)

    assert perform_document_generation() is True
