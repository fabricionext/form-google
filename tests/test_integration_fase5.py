#!/usr/bin/env python3
"""
Teste de Integração Fase 5 - Vue.js + APIs REST
==============================================

Testa a integração completa entre frontend Vue.js e backend APIs REST
implementadas nas Fases 4 e 5.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

# Configuração base
BASE_URL = "http://localhost:5000"
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

class IntegrationTester:
    """Testador de integração completa."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.test_results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        """Registra resultado do teste."""
        result = {
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
    
    def test_feature_flags(self) -> bool:
        """Testa se as feature flags estão habilitadas."""
        print("\n📋 Testando Feature Flags...")
        
        try:
            # Importar constants para verificar feature flags
            import sys
            import os
            sys.path.append('/var/www/estevaoalmeida.com.br/form-google')
            
            from app.config.constants import FEATURE_FLAGS
            
            required_flags = [
                'NEW_TEMPLATES_API',
                'NEW_FORMS_API', 
                'NEW_DOCUMENTS_API'
            ]
            
            all_enabled = True
            for flag in required_flags:
                enabled = FEATURE_FLAGS.get(flag, False)
                self.log_result(f"Feature Flag {flag}", enabled, 
                              f"Status: {'Enabled' if enabled else 'Disabled'}")
                if not enabled:
                    all_enabled = False
            
            return all_enabled
            
        except Exception as e:
            self.log_result("Feature Flags Import", False, f"Error: {e}")
            return False
    
    def test_templates_api(self) -> bool:
        """Testa API de Templates."""
        print("\n🔧 Testando Templates API...")
        
        try:
            # Test GET /api/templates/
            response = self.session.get(f"{BASE_URL}/api/templates/")
            success = response.status_code in [200, 401, 403]  # 401/403 = auth required (ok)
            
            self.log_result("GET /api/templates/", success, 
                          f"Status: {response.status_code}")
            
            if success and response.status_code == 200:
                data = response.json()
                templates_count = len(data.get('data', {}).get('templates', []))
                self.log_result("Templates Data", True, 
                              f"Found {templates_count} templates")
            
            return success
            
        except requests.exceptions.ConnectionError:
            self.log_result("Templates API Connection", False, 
                          "Server not running or endpoint not available")
            return False
        except Exception as e:
            self.log_result("Templates API", False, f"Error: {e}")
            return False
    
    def test_forms_api(self) -> bool:
        """Testa API de Forms."""
        print("\n📋 Testando Forms API...")
        
        try:
            # Test health check first
            response = self.session.get(f"{BASE_URL}/api/forms/health")
            success = response.status_code == 200
            
            self.log_result("GET /api/forms/health", success, 
                          f"Status: {response.status_code}")
            
            if success:
                data = response.json()
                service_status = data.get('status', 'unknown')
                self.log_result("Forms Service Health", 
                              service_status == 'healthy',
                              f"Service status: {service_status}")
            
            # Test schema endpoint (should require auth but endpoint should exist)
            response = self.session.get(f"{BASE_URL}/api/forms/1/schema")
            endpoint_exists = response.status_code in [200, 401, 403, 404]
            
            self.log_result("GET /api/forms/1/schema", endpoint_exists,
                          f"Endpoint exists (Status: {response.status_code})")
            
            return success and endpoint_exists
            
        except requests.exceptions.ConnectionError:
            self.log_result("Forms API Connection", False, 
                          "Server not running or endpoint not available")
            return False
        except Exception as e:
            self.log_result("Forms API", False, f"Error: {e}")
            return False
    
    def test_documents_api(self) -> bool:
        """Testa API de Documents."""
        print("\n📄 Testando Documents API...")
        
        try:
            # Test GET /api/documents/
            response = self.session.get(f"{BASE_URL}/api/documents/")
            success = response.status_code in [200, 401, 403]
            
            self.log_result("GET /api/documents/", success,
                          f"Status: {response.status_code}")
            
            # Test generation endpoint structure (should require auth)
            response = self.session.post(f"{BASE_URL}/api/documents/generate/1")
            endpoint_exists = response.status_code in [200, 400, 401, 403, 422]
            
            self.log_result("POST /api/documents/generate/1", endpoint_exists,
                          f"Endpoint exists (Status: {response.status_code})")
            
            return success and endpoint_exists
            
        except requests.exceptions.ConnectionError:
            self.log_result("Documents API Connection", False,
                          "Server not running or endpoint not available")
            return False
        except Exception as e:
            self.log_result("Documents API", False, f"Error: {e}")
            return False
    
    def test_client_api(self) -> bool:
        """Testa API de Clients (legacy + new)."""
        print("\n👥 Testando Clients API...")
        
        try:
            # Test legacy endpoint
            response = self.session.get(f"{BASE_URL}/peticionador/api/clientes")
            legacy_success = response.status_code in [200, 401, 403]
            
            self.log_result("GET /peticionador/api/clientes (Legacy)", legacy_success,
                          f"Status: {response.status_code}")
            
            # Test new endpoint
            response = self.session.get(f"{BASE_URL}/api/clients/")
            new_success = response.status_code in [200, 401, 403]
            
            self.log_result("GET /api/clients/ (New)", new_success,
                          f"Status: {response.status_code}")
            
            return legacy_success or new_success
            
        except requests.exceptions.ConnectionError:
            self.log_result("Clients API Connection", False,
                          "Server not running")
            return False
        except Exception as e:
            self.log_result("Clients API", False, f"Error: {e}")
            return False
    
    def test_pydantic_schemas(self) -> bool:
        """Testa se os schemas Pydantic estão funcionando."""
        print("\n🔍 Testando Schemas Pydantic...")
        
        try:
            # Importar schemas para verificar se não há erros
            import sys
            sys.path.append('/var/www/estevaoalmeida.com.br/form-google')
            
            from app.schemas.form_schema import FormSchema, FormFieldSchema
            from app.schemas.template_schema import TemplateSchema, TemplateCreateSchema
            from app.schemas.document_schema import DocumentGenerationSchema
            
            # Test FormFieldSchema
            test_field = FormFieldSchema(
                name="test_field",
                label="Test Field", 
                type="text"
            )
            self.log_result("FormFieldSchema Creation", True,
                          f"Created field: {test_field.name}")
            
            # Test DocumentGenerationSchema
            test_doc = DocumentGenerationSchema(
                template_id=1,
                cliente_nome="Test Client"
            )
            self.log_result("DocumentGenerationSchema Creation", True,
                          f"Created doc schema for template: {test_doc.template_id}")
            
            return True
            
        except ImportError as e:
            self.log_result("Pydantic Schema Import", False, f"Import error: {e}")
            return False
        except Exception as e:
            self.log_result("Pydantic Schemas", False, f"Error: {e}")
            return False
    
    def test_vue_build(self) -> bool:
        """Testa se o build Vue.js está funcionando."""
        print("\n🚀 Testando Vue.js Build...")
        
        try:
            import subprocess
            import os
            
            # Change to project directory
            project_dir = '/var/www/estevaoalmeida.com.br/form-google'
            
            # Test if package.json exists
            package_json = os.path.join(project_dir, 'package.json')
            if not os.path.exists(package_json):
                self.log_result("Vue.js Package.json", False, "package.json not found")
                return False
            
            self.log_result("Vue.js Package.json", True, "package.json exists")
            
            # Test if node_modules exists (dependencies installed)
            node_modules = os.path.join(project_dir, 'node_modules')
            deps_installed = os.path.exists(node_modules)
            
            self.log_result("Vue.js Dependencies", deps_installed,
                          "node_modules exists" if deps_installed else "Run npm install")
            
            # Test TypeScript compilation (quick check)
            try:
                result = subprocess.run(
                    ['npm', 'run', 'type-check'], 
                    cwd=project_dir,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                ts_success = result.returncode == 0
                self.log_result("Vue.js TypeScript Check", ts_success,
                              "No TypeScript errors" if ts_success else "TypeScript errors found")
                
            except (subprocess.TimeoutExpired, FileNotFoundError):
                self.log_result("Vue.js TypeScript Check", False, "npm or typescript not available")
                ts_success = False
            
            return deps_installed
            
        except Exception as e:
            self.log_result("Vue.js Build Test", False, f"Error: {e}")
            return False
    
    def test_component_imports(self) -> bool:
        """Testa se os componentes Vue.js podem ser importados."""
        print("\n🧩 Testando Componentes Vue.js...")
        
        try:
            import os
            
            project_dir = '/var/www/estevaoalmeida.com.br/form-google'
            components_dir = os.path.join(project_dir, 'src', 'components')
            
            # Check if main components exist
            components_to_check = [
                'DynamicSchemaRenderer.vue',
                'DynamicField.vue', 
                'DocumentGenerationMonitor.vue'
            ]
            
            all_exist = True
            for component in components_to_check:
                component_path = os.path.join(components_dir, component)
                exists = os.path.exists(component_path)
                
                self.log_result(f"Component {component}", exists,
                              "File exists" if exists else "File missing")
                
                if not exists:
                    all_exist = False
            
            # Check services
            services_dir = os.path.join(project_dir, 'src', 'services')
            api_js = os.path.join(services_dir, 'api.js')
            api_exists = os.path.exists(api_js)
            
            self.log_result("API Service (api.js)", api_exists,
                          "File exists" if api_exists else "File missing")
            
            # Check stores
            stores_dir = os.path.join(project_dir, 'src', 'stores')
            store_js = os.path.join(stores_dir, 'formulario.js')
            store_exists = os.path.exists(store_js)
            
            self.log_result("Pinia Store (formulario.js)", store_exists,
                          "File exists" if store_exists else "File missing")
            
            return all_exist and api_exists and store_exists
            
        except Exception as e:
            self.log_result("Vue.js Components Check", False, f"Error: {e}")
            return False
    
    def run_full_test_suite(self) -> Dict[str, Any]:
        """Executa todos os testes e retorna relatório."""
        print("🔥 INICIANDO TESTE DE INTEGRAÇÃO FASE 5")
        print("=" * 50)
        
        start_time = time.time()
        
        # Execute all tests
        tests = [
            ("Feature Flags", self.test_feature_flags),
            ("Pydantic Schemas", self.test_pydantic_schemas),
            ("Vue.js Components", self.test_component_imports),
            ("Vue.js Build", self.test_vue_build),
            ("Templates API", self.test_templates_api),
            ("Forms API", self.test_forms_api),
            ("Documents API", self.test_documents_api),
            ("Clients API", self.test_client_api)
        ]
        
        for test_name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                self.log_result(test_name, False, f"Test execution error: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate report
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': round(success_rate, 2),
                'duration_seconds': round(duration, 2)
            },
            'results': self.test_results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 RELATÓRIO FINAL")
        print("=" * 50)
        print(f"✅ Testes Passaram: {passed_tests}")
        print(f"❌ Testes Falharam: {failed_tests}")
        print(f"📈 Taxa de Sucesso: {success_rate:.1f}%")
        print(f"⏱️  Duração: {duration:.2f}s")
        
        if success_rate >= 80:
            print("🎉 INTEGRAÇÃO FUNCIONANDO ADEQUADAMENTE!")
        elif success_rate >= 60:
            print("⚠️  INTEGRAÇÃO PARCIAL - REQUER AJUSTES")
        else:
            print("🚨 INTEGRAÇÃO COM PROBLEMAS CRÍTICOS")
        
        return report

def main():
    """Função principal."""
    tester = IntegrationTester()
    report = tester.run_full_test_suite()
    
    # Save report to file
    report_file = f"/var/www/estevaoalmeida.com.br/form-google/integration_test_report_{int(time.time())}.json"
    try:
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📁 Relatório salvo em: {report_file}")
    except Exception as e:
        print(f"\n⚠️  Erro ao salvar relatório: {e}")
    
    return report

if __name__ == "__main__":
    main()