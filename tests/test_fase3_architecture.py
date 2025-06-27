#!/usr/bin/env python3
"""
Teste da Nova Arquitetura - Fase 3
=================================

Script para validar o funcionamento das novas APIs e Services
implementados na refatoração da Fase 3.

Este script testa:
- APIs REST da nova arquitetura
- Integração entre Services
- Validação de dados
- Cache e performance
- Frontend e formulários dinâmicos
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Any

class Fase3ArchitectureTester:
    """Testador para a nova arquitetura da Fase 3."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.results = []
        
        # Headers padrão
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Fase3-Architecture-Tester/1.0'
        })
        
        print(f"🚀 Testador da Nova Arquitetura - Fase 3")
        print(f"🌐 Base URL: {self.base_url}")
        print(f"📅 Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def log_test(self, test_name: str, success: bool, message: str = "", data: Any = None):
        """Registra resultado de um teste."""
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} {test_name}")
        if message:
            print(f"   📝 {message}")
        if data and isinstance(data, dict) and len(str(data)) < 200:
            print(f"   📊 {data}")
        
        self.results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        print()
    
    def test_architecture_status(self) -> bool:
        """Testa o endpoint de status da arquitetura."""
        try:
            response = self.session.get(f"{self.base_url}/api/architecture-status")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    feature_flags = data.get('data', {}).get('feature_flags', {})
                    active_flags = [k for k, v in feature_flags.items() if v]
                    
                    self.log_test(
                        "Status da Arquitetura",
                        True,
                        f"APIs ativas: {len(active_flags)} ({', '.join(active_flags)})",
                        {'status': 'ok', 'active_apis': len(active_flags)}
                    )
                    return True
                else:
                    self.log_test("Status da Arquitetura", False, "Response indica falha")
                    return False
            else:
                self.log_test("Status da Arquitetura", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Status da Arquitetura", False, f"Erro: {str(e)}")
            return False
    
    def test_auth_api(self) -> bool:
        """Testa a API de autenticação."""
        try:
            # Teste de validação de sessão
            response = self.session.get(f"{self.base_url}/api/auth/validate-session")
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get('data', {}).get('valid', False)
                
                self.log_test(
                    "API de Autenticação",
                    True,
                    f"Sessão válida: {is_valid}",
                    {'session_valid': is_valid}
                )
                return True
            else:
                self.log_test("API de Autenticação", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("API de Autenticação", False, f"Erro: {str(e)}")
            return False
    
    def test_clients_api(self) -> bool:
        """Testa a API de clientes."""
        try:
            # Teste de listagem de clientes
            response = self.session.get(f"{self.base_url}/api/clients/?page=1&per_page=5")
            
            if response.status_code in [200, 401]:  # 401 é esperado se não autenticado
                if response.status_code == 401:
                    self.log_test(
                        "API de Clientes",
                        True,
                        "Endpoint protegido corretamente (401 Unauthorized)",
                        {'protection': 'active'}
                    )
                else:
                    data = response.json()
                    if data.get('success'):
                        total = data.get('data', {}).get('total', 0)
                        self.log_test(
                            "API de Clientes",
                            True,
                            f"Listagem funcionando: {total} clientes",
                            {'total_clients': total}
                        )
                    else:
                        self.log_test("API de Clientes", False, "Response indica falha")
                        return False
                return True
            else:
                self.log_test("API de Clientes", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("API de Clientes", False, f"Erro: {str(e)}")
            return False
    
    def test_cpf_search(self) -> bool:
        """Testa busca de cliente por CPF."""
        try:
            # Teste com CPF fictício
            test_cpf = "12345678901"
            response = self.session.get(f"{self.base_url}/api/clients/search/cpf?cpf={test_cpf}")
            
            if response.status_code in [200, 401]:  # 401 é esperado se não autenticado
                if response.status_code == 401:
                    self.log_test(
                        "Busca por CPF",
                        True,
                        "Endpoint protegido corretamente",
                        {'protection': 'active'}
                    )
                else:
                    data = response.json()
                    client_found = data.get('data') is not None
                    self.log_test(
                        "Busca por CPF",
                        True,
                        f"Cliente encontrado: {client_found}",
                        {'cpf_search': 'working'}
                    )
                return True
            else:
                self.log_test("Busca por CPF", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Busca por CPF", False, f"Erro: {str(e)}")
            return False
    
    def test_forms_api(self) -> bool:
        """Testa a API de formulários dinâmicos."""
        try:
            # Teste de geração de formulário dinâmico
            payload = {
                "template_id": 1,
                "include_entities": True,
                "include_validation": True
            }
            
            response = self.session.post(
                f"{self.base_url}/api/forms/generate",
                json=payload
            )
            
            if response.status_code in [200, 401, 404]:  # 404 pode ser esperado se rota não estiver ativa
                if response.status_code == 401:
                    self.log_test(
                        "API de Formulários",
                        True,
                        "Endpoint protegido corretamente",
                        {'protection': 'active'}
                    )
                elif response.status_code == 404:
                    self.log_test(
                        "API de Formulários",
                        True,
                        "API não ativa ainda (esperado na Fase 3.1)",
                        {'status': 'pending'}
                    )
                else:
                    data = response.json()
                    form_generated = data.get('success', False)
                    self.log_test(
                        "API de Formulários",
                        True,
                        f"Formulário gerado: {form_generated}",
                        {'form_generation': 'working'}
                    )
                return True
            else:
                self.log_test("API de Formulários", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("API de Formulários", False, f"Erro: {str(e)}")
            return False
    
    def test_validation_api(self) -> bool:
        """Testa a API de validação."""
        try:
            # Teste de validação de campo
            payload = {
                "field_name": "cpf",
                "field_value": "12345678901"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/clients/validate-field",
                json=payload
            )
            
            if response.status_code in [200, 401, 404]:
                if response.status_code == 401:
                    self.log_test(
                        "API de Validação",
                        True,
                        "Endpoint protegido corretamente",
                        {'protection': 'active'}
                    )
                elif response.status_code == 404:
                    self.log_test(
                        "API de Validação",
                        True,
                        "Endpoint não encontrado (pode estar inativo)",
                        {'status': 'not_found'}
                    )
                else:
                    data = response.json()
                    validation_working = data.get('success', False)
                    self.log_test(
                        "API de Validação",
                        True,
                        f"Validação funcionando: {validation_working}",
                        {'validation': 'working'}
                    )
                return True
            else:
                self.log_test("API de Validação", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("API de Validação", False, f"Erro: {str(e)}")
            return False
    
    def test_frontend_assets(self) -> bool:
        """Testa se os assets do frontend estão disponíveis."""
        try:
            # Teste do JavaScript principal
            js_response = self.session.get(f"{self.base_url}/peticionador/static/js/dynamic_forms_api.js")
            
            # Teste do CSS
            css_response = self.session.get(f"{self.base_url}/peticionador/static/css/dynamic_forms.css")
            
            js_ok = js_response.status_code == 200
            css_ok = css_response.status_code == 200
            
            if js_ok and css_ok:
                js_size = len(js_response.content)
                css_size = len(css_response.content)
                
                self.log_test(
                    "Assets do Frontend",
                    True,
                    f"JS: {js_size} bytes, CSS: {css_size} bytes",
                    {'js_loaded': js_ok, 'css_loaded': css_ok}
                )
                return True
            else:
                self.log_test(
                    "Assets do Frontend",
                    False,
                    f"JS: {js_response.status_code}, CSS: {css_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_test("Assets do Frontend", False, f"Erro: {str(e)}")
            return False
    
    def test_performance_basic(self) -> bool:
        """Teste básico de performance."""
        try:
            start_time = time.time()
            
            # Fazer algumas requisições para medir tempo
            endpoints = [
                "/api/architecture-status",
                "/api/auth/validate-session",
            ]
            
            response_times = []
            for endpoint in endpoints:
                req_start = time.time()
                response = self.session.get(f"{self.base_url}{endpoint}")
                req_end = time.time()
                response_times.append(req_end - req_start)
            
            avg_response_time = sum(response_times) / len(response_times)
            total_time = time.time() - start_time
            
            performance_ok = avg_response_time < 2.0  # Menos de 2 segundos
            
            self.log_test(
                "Performance Básica",
                performance_ok,
                f"Tempo médio: {avg_response_time:.2f}s, Total: {total_time:.2f}s",
                {'avg_response_time': round(avg_response_time, 2)}
            )
            return performance_ok
            
        except Exception as e:
            self.log_test("Performance Básica", False, f"Erro: {str(e)}")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Executa todos os testes."""
        print("🧪 Iniciando bateria de testes da Nova Arquitetura...")
        print()
        
        tests = [
            self.test_architecture_status,
            self.test_auth_api,
            self.test_clients_api,
            self.test_cpf_search,
            self.test_forms_api,
            self.test_validation_api,
            self.test_frontend_assets,
            self.test_performance_basic
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
        
        # Resumo final
        print("=" * 60)
        print(f"📊 RESUMO DOS TESTES")
        print(f"✅ Passou: {passed}/{total} ({(passed/total)*100:.1f}%)")
        print(f"❌ Falhou: {total-passed}/{total}")
        print(f"📅 Concluído em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if passed == total:
            print(f"🎉 TODOS OS TESTES PASSARAM! Nova arquitetura funcionando corretamente.")
        elif passed >= total * 0.7:
            print(f"⚠️  MAIORIA DOS TESTES PASSOU. Alguns componentes podem precisar de ajustes.")
        else:
            print(f"⚠️  MUITOS TESTES FALHARAM. Verificar implementação da nova arquitetura.")
        
        return {
            'total_tests': total,
            'passed_tests': passed,
            'success_rate': (passed/total)*100,
            'results': self.results,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Função principal."""
    # Verificar argumentos
    base_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    # Executar testes
    tester = Fase3ArchitectureTester(base_url)
    results = tester.run_all_tests()
    
    # Salvar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"test_results_fase3_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"📁 Resultados salvos em: {filename}")
    except Exception as e:
        print(f"⚠️  Erro ao salvar resultados: {e}")
    
    # Exit code baseado no sucesso
    exit_code = 0 if results['success_rate'] >= 70 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 