#!/usr/bin/env python3
"""
SCRIPT DE TESTE DE SEGURANÇA EM PRODUÇÃO

Este script testa todas as melhorias de segurança implementadas
de forma segura no ambiente de produção.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple

class SecurityTester:
"""Testador de segurança para ambiente de produção"""

    def __init__(self, base_url: str, session_cookie: str = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if session_cookie:
            self.session.cookies.set('session', session_cookie)

        self.results = []

    def log_result(self, test_name: str, success: bool, details: str):
        """Log dos resultados dos testes"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'timestamp': timestamp,
            'test': test_name,
            'status': status,
            'details': details
        }
        self.results.append(result)
        print(f"[{timestamp}] {status} {test_name}: {details}")

    def test_cpf_validation_security(self):
        """Testa a validação segura de CPF"""
        print("\n🔒 TESTANDO VALIDAÇÃO DE CPF...")

        test_cases = [
            ("123.456.789-00", True, "CPF válido"),
            ("12345678900", True, "CPF sem formatação"),
            ("123<script>alert(1)", False, "CPF com script malicioso"),
            ("123456789012345", False, "CPF muito longo"),
            ("123';DROP TABLE users;--", False, "Tentativa de SQL injection"),
            ("123%3Cscript%3E", False, "Script encoded"),
        ]

        for cpf, should_succeed, description in test_cases:
            try:
                response = self.session.get(
                    f"{self.base_url}/api/clientes/busca_cpf",
                    params={"cpf": cpf},
                    timeout=10
                )

                if should_succeed:
                    success = response.status_code in [200, 404]  # 404 = não encontrado, mas validação ok
                    details = f"{description} - Status: {response.status_code}"
                else:
                    success = response.status_code == 400  # Deve ser rejeitado
                    try:
                        error_msg = response.json().get('error', 'Sem mensagem')
                        details = f"{description} - Rejeitado: {error_msg}"
                    except:
                        details = f"{description} - Status: {response.status_code}"

                self.log_result(f"CPF Validation: {cpf}", success, details)

            except Exception as e:
                self.log_result(f"CPF Validation: {cpf}", False, f"Erro: {str(e)}")

    def test_api_performance(self):
        """Testa performance das APIs melhoradas"""
        print("\n⚡ TESTANDO PERFORMANCE...")

        # Teste de carga simples na API de CPF
        cpf_valido = "123.456.789-00"
        tempos = []

        for i in range(10):
            start_time = time.time()
            try:
                response = self.session.get(
                    f"{self.base_url}/api/clientes/busca_cpf",
                    params={"cpf": cpf_valido},
                    timeout=5
                )
                tempo = time.time() - start_time
                tempos.append(tempo)

                if response.status_code in [200, 404]:
                    self.log_result(f"Performance Test #{i+1}", True, f"{tempo:.3f}s")
                else:
                    self.log_result(f"Performance Test #{i+1}", False, f"Status {response.status_code}")

            except Exception as e:
                self.log_result(f"Performance Test #{i+1}", False, f"Erro: {str(e)}")

        if tempos:
            avg_time = sum(tempos) / len(tempos)
            max_time = max(tempos)
            self.log_result("Performance Summary", avg_time < 1.0,
                          f"Média: {avg_time:.3f}s, Máximo: {max_time:.3f}s")

    def test_form_validation(self):
        """Testa validação de formulários"""
        print("\n📝 TESTANDO VALIDAÇÃO DE FORMULÁRIOS...")

        # Dados maliciosos para teste
        malicious_data = {
            "autor_nome": "<script>alert('xss')</script>",
            "autor_email": "test@domain.com';DROP TABLE--",
            "processo_numero": "12345<img src=x onerror=alert(1)>",
        }

        try:
            # Teste em rota de teste se disponível
            response = self.session.post(
                f"{self.base_url}/api/preview-document",
                data=malicious_data,
                timeout=10
            )

            # Verificar se dados maliciosos foram sanitizados
            if response.status_code == 400:
                self.log_result("Form Validation", True, "Dados maliciosos rejeitados")
            elif response.status_code == 200:
                # Verificar se response não contém scripts
                content = response.text
                if "<script>" not in content and "alert(" not in content:
                    self.log_result("Form Validation", True, "Dados sanitizados corretamente")
                else:
                    self.log_result("Form Validation", False, "XSS possível detectado")
            else:
                self.log_result("Form Validation", False, f"Status inesperado: {response.status_code}")

        except Exception as e:
            self.log_result("Form Validation", False, f"Erro: {str(e)}")

    def test_service_layer(self, test_slug: str = None):
        """Testa a nova camada de serviços"""
        if not test_slug:
            print("\n⚠️  PULANDO TESTE DE SERVICE LAYER (slug não fornecido)")
            return

        print(f"\n🏗️  TESTANDO SERVICE LAYER COM SLUG: {test_slug}")

        test_data = {
            "autor_nome": "João Teste Produção",
            "autor_cpf": "123.456.789-00",
            "processo_numero": f"TESTE-{int(time.time())}"
        }

        # Testar rota original
        try:
            start_time = time.time()
            response_original = self.session.post(
                f"{self.base_url}/formularios/{test_slug}",
                data=test_data,
                timeout=30
            )
            time_original = time.time() - start_time

            self.log_result("Service Layer - Original",
                          response_original.status_code == 200,
                          f"Status: {response_original.status_code}, Tempo: {time_original:.2f}s")
        except Exception as e:
            self.log_result("Service Layer - Original", False, f"Erro: {str(e)}")

        # Testar rota V2 se disponível
        try:
            start_time = time.time()
            response_v2 = self.session.post(
                f"{self.base_url}/formularios/{test_slug}/v2",
                data=test_data,
                timeout=30
            )
            time_v2 = time.time() - start_time

            self.log_result("Service Layer - V2",
                          response_v2.status_code == 200,
                          f"Status: {response_v2.status_code}, Tempo: {time_v2:.2f}s")
        except Exception as e:
            self.log_result("Service Layer - V2", False, f"Erro: {str(e)}")

    def test_environment_security(self):
        """Testa configurações de segurança do ambiente"""
        print("\n🛡️  TESTANDO SEGURANÇA DO AMBIENTE...")

        # Teste da rota de desenvolvimento (deve estar bloqueada)
        try:
            response = self.session.get(f"{self.base_url}/setup_admin_dev", timeout=5)

            if response.status_code == 404:
                self.log_result("Dev Route Security", True, "Rota de dev bloqueada em produção")
            else:
                self.log_result("Dev Route Security", False,
                              f"Rota de dev acessível! Status: {response.status_code}")
        except Exception as e:
            self.log_result("Dev Route Security", False, f"Erro: {str(e)}")

        # Teste de headers de segurança
        try:
            response = self.session.get(self.base_url, timeout=5)
            headers = response.headers

            security_headers = [
                ('X-Content-Type-Options', 'nosniff'),
                ('X-Frame-Options', 'DENY'),
                ('X-XSS-Protection', '1; mode=block'),
            ]

            for header, expected in security_headers:
                if header in headers:
                    self.log_result(f"Security Header: {header}", True, f"Presente: {headers[header]}")
                else:
                    self.log_result(f"Security Header: {header}", False, "Ausente")

        except Exception as e:
            self.log_result("Security Headers", False, f"Erro: {str(e)}")

    def generate_report(self):
        """Gera relatório final dos testes"""
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL DE TESTES DE SEGURANÇA")
        print("="*80)

        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if "✅ PASS" in r['status']])
        failed_tests = total_tests - passed_tests

        print(f"\n📈 ESTATÍSTICAS:")
        print(f"  Total de testes: {total_tests}")
        print(f"  ✅ Aprovados: {passed_tests}")
        print(f"  ❌ Falharam: {failed_tests}")
        print(f"  📊 Taxa de sucesso: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print(f"\n❌ TESTES FALHARAM:")
            for result in self.results:
                if "❌ FAIL" in result['status']:
                    print(f"  • {result['test']}: {result['details']}")

        print(f"\n{'✅ TODOS OS TESTES PASSARAM!' if failed_tests == 0 else '⚠️  ALGUNS TESTES FALHARAM - REVISAR'}")

        return failed_tests == 0

def main():
"""Executa todos os testes de segurança"""
if len(sys.argv) < 2:
print("Uso: python test_seguranca_producao.py <URL_BASE> [SESSION_COOKIE] [TEST_SLUG]")
print("Exemplo: python test_seguranca_producao.py https://appform.estevaoalmeida.com.br abc123 suspensao-teste")
sys.exit(1)

    base_url = sys.argv[1]
    session_cookie = sys.argv[2] if len(sys.argv) > 2 else None
    test_slug = sys.argv[3] if len(sys.argv) > 3 else None

    print(f"🚀 INICIANDO TESTES DE SEGURANÇA EM PRODUÇÃO")
    print(f"🌐 URL: {base_url}")
    print(f"🔐 Autenticação: {'Sim' if session_cookie else 'Não'}")
    print(f"📝 Slug de teste: {test_slug or 'Não fornecido'}")

    tester = SecurityTester(base_url, session_cookie)

    # Executar todos os testes
    tester.test_cpf_validation_security()
    tester.test_api_performance()
    tester.test_form_validation()
    tester.test_service_layer(test_slug)
    tester.test_environment_security()

    # Gerar relatório
    success = tester.generate_report()

    sys.exit(0 if success else 1)

if **name** == "**main**":
main()
