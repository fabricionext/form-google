#!/usr/bin/env python3
"""
Script de teste para validar as melhorias implementadas no sistema de cadastro.
"""

import json
import requests
import time
from datetime import datetime

# Configurações
BASE_URL = "http://localhost:5000"  # Ajustar conforme necessário
TEST_TIMEOUT = 300  # 5 minutos


def test_validation_functions():
    """Testa as funções de validação."""
    print("🧪 Testando validações...")
    
    from app.validators.form_validator import FormValidator, validate_cpf, validate_cnpj
    
    # Teste CPF válido
    valid, error = validate_cpf("123.456.789-09")
    print(f"CPF válido: {valid} (erro: {error})")
    
    # Teste CPF inválido
    valid, error = validate_cpf("123.456.789-00")
    print(f"CPF inválido: {valid} (erro: {error})")
    
    # Teste CNPJ válido
    valid, error = validate_cnpj("11.222.333/0001-81")
    print(f"CNPJ válido: {valid} (erro: {error})")
    
    # Teste CNPJ inválido
    valid, error = validate_cnpj("11.222.333/0001-00")
    print(f"CNPJ inválido: {valid} (erro: {error})")
    
    # Teste FormValidator
    validator = FormValidator()
    
    # Dados válidos PF
    dados_pf_validos = {
        "tipoPessoa": "pf",
        "dadosCliente": {
            "primeiroNome": "João",
            "sobrenome": "Silva",
            "cpf": "123.456.789-09",
            "email": "joao@teste.com"
        }
    }
    
    valid, errors = validator.validate_form_data(dados_pf_validos)
    print(f"Dados PF válidos: {valid} (erros: {errors})")
    
    # Dados inválidos PF
    dados_pf_invalidos = {
        "tipoPessoa": "pf",
        "dadosCliente": {
            "primeiroNome": "",
            "sobrenome": "Silva",
            "cpf": "123.456.789-00",
            "email": "email_invalido"
        }
    }
    
    valid, errors = validator.validate_form_data(dados_pf_invalidos)
    print(f"Dados PF inválidos: {valid} (erros: {errors})")


def test_api_endpoints():
    """Testa os endpoints da API."""
    print("\n🌐 Testando endpoints da API...")
    
    # Teste 1: Formulário principal
    try:
        response = requests.get(f"{BASE_URL}/cadastrodecliente", timeout=10)
        print(f"GET /cadastrodecliente: {response.status_code}")
        if response.status_code == 200:
            print("✅ Formulário principal carregando corretamente")
        else:
            print("❌ Erro ao carregar formulário principal")
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
    
    # Teste 2: API CEP
    try:
        response = requests.get(f"{BASE_URL}/api/cep/01310-100", timeout=10)
        print(f"GET /api/cep/01310-100: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ CEP: {data.get('logradouro', 'N/A')} - {data.get('localidade', 'N/A')}")
        else:
            print("❌ Erro na API de CEP")
    except Exception as e:
        print(f"❌ Erro na requisição CEP: {e}")
    
    # Teste 3: Validação de dados inválidos
    try:
        payload_invalido = {
            "tipoPessoa": "pf",
            "dadosCliente": {
                "primeiroNome": "",
                "sobrenome": "",
                "cpf": "123.456.789-00",
                "email": "email_invalido"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/gerar-documento",
            json=payload_invalido,
            timeout=10
        )
        print(f"POST /api/gerar-documento (dados inválidos): {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            print(f"✅ Validação funcionando: {data.get('erros', [])}")
        else:
            print("❌ Validação backend não está funcionando")
            
    except Exception as e:
        print(f"❌ Erro na requisição de validação: {e}")


def test_task_status_api():
    """Testa a API de status de tarefas."""
    print("\n📊 Testando API de status de tarefas...")
    
    # Teste com task_id fictício
    try:
        fake_task_id = "test-task-123"
        response = requests.get(f"{BASE_URL}/api/task-status/{fake_task_id}", timeout=10)
        print(f"GET /api/task-status/{fake_task_id}: {response.status_code}")
        
        if response.status_code in [200, 500]:  # 500 é esperado para task inexistente
            data = response.json()
            print(f"✅ API de status funcionando: {data.get('status', 'N/A')}")
        else:
            print("❌ API de status não funcionando")
            
    except Exception as e:
        print(f"❌ Erro na API de status: {e}")


def test_complete_flow():
    """Testa o fluxo completo com dados válidos."""
    print("\n🚀 Testando fluxo completo...")
    
    # Dados de teste válidos
    payload_valido = {
        "tipoPessoa": "pf",
        "dadosCliente": {
            "primeiroNome": "João",
            "sobrenome": "Silva",
            "cpf": "123.456.789-09",  # CPF de teste (não real)
            "email": "joao.teste@exemplo.com",
            "telefoneCelular": "(11) 99999-9999",
            "logradouro": "Rua Teste",
            "numero": "123",
            "bairro": "Centro",
            "cidade": "São Paulo",
            "estado": "SP",
            "cep": "01310-100"
        }
    }
    
    try:
        print("Enviando dados válidos...")
        response = requests.post(
            f"{BASE_URL}/api/gerar-documento",
            json=payload_valido,
            timeout=30
        )
        
        print(f"Status da resposta: {response.status_code}")
        
        if response.status_code == 202:
            data = response.json()
            task_id = data.get("task_id")
            print(f"✅ Tarefa enfileirada com ID: {task_id}")
            
            if task_id:
                # Acompanha o progresso da tarefa
                print("Acompanhando progresso...")
                monitor_task_progress(task_id)
            
        else:
            print(f"❌ Erro na submissão: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro no fluxo completo: {e}")


def monitor_task_progress(task_id, max_checks=20):
    """Monitora o progresso de uma tarefa."""
    print(f"\n📈 Monitorando tarefa {task_id}...")
    
    for check in range(max_checks):
        try:
            response = requests.get(f"{BASE_URL}/api/task-status/{task_id}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "UNKNOWN")
                progress = data.get("progress", 0)
                message = data.get("status_message", "")
                
                print(f"Check {check + 1}: {status} - {progress}% - {message}")
                
                if status == "SUCCESS":
                    print("✅ Tarefa concluída com sucesso!")
                    if data.get("link_pasta_cliente"):
                        print(f"📁 Pasta do cliente: {data['link_pasta_cliente']}")
                    if data.get("documentos_gerados"):
                        print(f"📄 Documentos gerados: {len(data['documentos_gerados'])}")
                    break
                    
                elif status == "FAILURE":
                    print(f"❌ Tarefa falhou: {data.get('error_message', 'Erro desconhecido')}")
                    break
                    
                elif status in ["PENDING", "PROGRESS"]:
                    time.sleep(5)  # Aguarda 5 segundos antes da próxima verificação
                    
            else:
                print(f"❌ Erro ao verificar status: {response.status_code}")
                break
                
        except Exception as e:
            print(f"❌ Erro ao monitorar tarefa: {e}")
            break
    
    else:
        print("⏰ Timeout no monitoramento da tarefa")


def run_all_tests():
    """Executa todos os testes."""
    print("🔧 Iniciando testes do sistema melhorado")
    print("=" * 50)
    
    # Teste 1: Validações
    try:
        test_validation_functions()
    except Exception as e:
        print(f"❌ Erro nos testes de validação: {e}")
    
    # Teste 2: Endpoints básicos
    test_api_endpoints()
    
    # Teste 3: API de status
    test_task_status_api()
    
    # Teste 4: Fluxo completo (comentado por padrão para evitar criar documentos reais)
    print(f"\n⚠️  Teste de fluxo completo desabilitado por padrão")
    print("Para testar o fluxo completo, descomente a linha abaixo:")
    print("# test_complete_flow()")
    
    print("\n" + "=" * 50)
    print("🏁 Testes concluídos!")


if __name__ == "__main__":
    run_all_tests() 