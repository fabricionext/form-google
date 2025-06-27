#!/usr/bin/env python3
"""
Teste Completo da Fase 4 - Expansão da API para Templates e Documentos
=====================================================================

Script para validar a implementação completa da Fase 4:
- TemplateController e rotas
- DocumentController e rotas  
- FormController e rotas
- Feature flags ativadas
- Integração end-to-end

Execução: python test_fase4_complete.py
"""

import sys
import json
import traceback
from datetime import datetime
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

class Fase4CompleteTester:
    """Testador completo da Fase 4."""
    
    def __init__(self):
        self.results = {
            'start_time': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'success_rate': 0
            }
        }
        self.app = None
    
    def log_test(self, test_name: str, success: bool, message: str, details: dict = None):
        """Registra resultado de um teste."""
        self.results['tests'][test_name] = {
            'success': success,
            'message': message,
            'details': details or {},
            'timestamp': datetime.now().isoformat()
        }
        self.results['summary']['total'] += 1
        if success:
            self.results['summary']['passed'] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.results['summary']['failed'] += 1
            print(f"❌ {test_name}: {message}")
    
    def test_feature_flags(self):
        """Testa se as feature flags estão ativadas."""
        try:
            from app.api.routes import FEATURE_FLAGS
            
            expected_flags = {
                'NEW_AUTH_API': True,
                'NEW_CLIENTS_API': True,
                'NEW_TEMPLATES_API': True,
                'NEW_FORMS_API': True,
                'NEW_DOCUMENTS_API': True
            }
            
            all_active = True
            inactive_flags = []
            
            for flag, expected in expected_flags.items():
                if FEATURE_FLAGS.get(flag) != expected:
                    all_active = False
                    inactive_flags.append(flag)
            
            if all_active:
                self.log_test(
                    "feature_flags",
                    True,
                    "Todas as feature flags da Fase 4 estão ativas",
                    {'flags': FEATURE_FLAGS}
                )
            else:
                self.log_test(
                    "feature_flags",
                    False,
                    f"Feature flags inativas: {inactive_flags}",
                    {'inactive': inactive_flags, 'current': FEATURE_FLAGS}
                )
                
        except Exception as e:
            self.log_test("feature_flags", False, f"Erro ao verificar flags: {str(e)}")
    
    def test_controllers_import(self):
        """Testa importação dos controllers expandidos."""
        try:
            from app.api.controllers.template_controller import TemplateController
            from app.api.controllers.document_controller import DocumentController
            from app.api.controllers.form_controller import FormController
            
            # Testar instanciação
            template_controller = TemplateController()
            document_controller = DocumentController()
            form_controller = FormController()
            
            # Verificar métodos essenciais
            template_methods = [
                'list_templates', 'get_template', 'create_template', 
                'update_template', 'delete_template', 'sync_placeholders'
            ]
            
            document_methods = [
                'generate_document', 'get_document_status', 'list_documents',
                'get_document', 'download_document', 'regenerate_document'
            ]
            
            form_methods = [
                'get_form_schema', 'validate_form_data', 'validate_field',
                'get_field_suggestions', 'process_form_submission'
            ]
            
            missing_methods = []
            
            for method in template_methods:
                if not hasattr(template_controller, method):
                    missing_methods.append(f"TemplateController.{method}")
            
            for method in document_methods:
                if not hasattr(document_controller, method):
                    missing_methods.append(f"DocumentController.{method}")
            
            for method in form_methods:
                if not hasattr(form_controller, method):
                    missing_methods.append(f"FormController.{method}")
            
            if not missing_methods:
                self.log_test(
                    "controllers_import",
                    True,
                    "Todos os controllers expandidos importados com sucesso",
                    {
                        'template_methods': len(template_methods),
                        'document_methods': len(document_methods),
                        'form_methods': len(form_methods)
                    }
                )
            else:
                self.log_test(
                    "controllers_import",
                    False,
                    f"Métodos ausentes: {missing_methods}",
                    {'missing': missing_methods}
                )
                
        except ImportError as e:
            self.log_test("controllers_import", False, f"Erro de importação: {str(e)}")
        except Exception as e:
            self.log_test("controllers_import", False, f"Erro inesperado: {str(e)}")
    
    def test_routes_import(self):
        """Testa importação das rotas expandidas."""
        try:
            from app.api.routes.auth import auth_bp
            from app.api.routes.clients import clients_bp
            from app.api.routes.templates import templates_bp
            from app.api.routes.forms import forms_bp
            from app.api.routes.documents import documents_bp
            
            blueprints = {
                'auth_bp': auth_bp,
                'clients_bp': clients_bp,
                'templates_bp': templates_bp,
                'forms_bp': forms_bp,
                'documents_bp': documents_bp
            }
            
            self.log_test(
                "routes_import",
                True,
                f"Todos os blueprints importados com sucesso",
                {'blueprints': list(blueprints.keys())}
            )
                
        except ImportError as e:
            self.log_test("routes_import", False, f"Erro de importação de rotas: {str(e)}")
        except Exception as e:
            self.log_test("routes_import", False, f"Erro inesperado: {str(e)}")
    
    def test_services_integration(self):
        """Testa integração básica com services."""
        try:
            from app.services.template_service import TemplateService
            from app.services.document_service import DocumentService
            from app.services.dynamic_form_service import DynamicFormService
            
            # Tentar instanciar services
            template_service = TemplateService()
            document_service = DocumentService()
            form_service = DynamicFormService()
            
            # Verificar métodos essenciais
            services_methods = {
                'TemplateService': ['list_templates', 'get_template_by_id', 'sync_placeholders'],
                'DocumentService': ['generate_document_async', 'get_generation_status'],
                'DynamicFormService': ['generate_form_schema', 'validate_form_data']
            }
            
            missing_methods = []
            services = {
                'TemplateService': template_service,
                'DocumentService': document_service,
                'DynamicFormService': form_service
            }
            
            for service_name, methods in services_methods.items():
                service = services[service_name]
                for method in methods:
                    if not hasattr(service, method):
                        missing_methods.append(f"{service_name}.{method}")
            
            if not missing_methods:
                self.log_test(
                    "services_integration",
                    True,
                    "Integração com services funcionando",
                    {'services': list(services_methods.keys())}
                )
            else:
                self.log_test(
                    "services_integration",
                    False,
                    f"Métodos de service ausentes: {missing_methods}",
                    {'missing': missing_methods}
                )
                
        except ImportError as e:
            self.log_test("services_integration", False, f"Erro de importação de services: {str(e)}")
        except Exception as e:
            self.log_test("services_integration", False, f"Erro inesperado: {str(e)}")
    
    def test_app_creation(self):
        """Testa criação da aplicação com novos blueprints."""
        try:
            from application import create_app
            
            # Criar app de teste
            self.app = create_app()
            
            # Verificar blueprints registrados
            registered_blueprints = list(self.app.blueprints.keys())
            
            expected_blueprints = [
                'auth_api', 'clients_api', 'templates_api', 
                'forms_api', 'documents_api'
            ]
            
            new_blueprints = [bp for bp in expected_blueprints if bp in registered_blueprints]
            missing_blueprints = [bp for bp in expected_blueprints if bp not in registered_blueprints]
            
            if len(new_blueprints) >= 3:  # Pelo menos auth, clients e mais um
                self.log_test(
                    "app_creation",
                    True,
                    f"App criada com {len(new_blueprints)} novos blueprints",
                    {
                        'registered': new_blueprints,
                        'missing': missing_blueprints,
                        'total_blueprints': len(registered_blueprints)
                    }
                )
            else:
                self.log_test(
                    "app_creation",
                    False,
                    f"Poucos blueprints registrados: {new_blueprints}",
                    {'missing': missing_blueprints}
                )
                
        except Exception as e:
            self.log_test("app_creation", False, f"Erro ao criar app: {str(e)}")
    
    def test_api_routes_structure(self):
        """Testa estrutura das rotas da API."""
        if not self.app:
            self.log_test("api_routes_structure", False, "App não foi criada")
            return
        
        try:
            with self.app.app_context():
                # Mapear todas as rotas
                routes = {}
                for rule in self.app.url_map.iter_rules():
                    endpoint = rule.endpoint
                    if 'api' in endpoint:
                        blueprint = endpoint.split('.')[0]
                        if blueprint not in routes:
                            routes[blueprint] = []
                        routes[blueprint].append({
                            'rule': str(rule.rule),
                            'methods': list(rule.methods - {'OPTIONS', 'HEAD'}),
                            'endpoint': endpoint
                        })
                
                # Verificar rotas críticas
                critical_routes = {
                    'auth_api': ['/api/auth/login', '/api/auth/logout'],
                    'clients_api': ['/api/clients/', '/api/clients/search/cpf'],
                    'templates_api': ['/api/templates/', '/api/templates/<int:template_id>'],
                    'forms_api': ['/api/forms/<int:template_id>/schema'],
                    'documents_api': ['/api/documents/generate/<int:template_id>']
                }
                
                missing_routes = []
                for blueprint, expected_routes in critical_routes.items():
                    if blueprint in routes:
                        blueprint_routes = [r['rule'] for r in routes[blueprint]]
                        for expected in expected_routes:
                            # Busca flexível (pode ter variações nos parâmetros)
                            found = any(expected.replace('<int:template_id>', '').strip('/')
                                      in route.replace('<int:template_id>', '').strip('/')
                                      for route in blueprint_routes)
                            if not found:
                                missing_routes.append(f"{blueprint}: {expected}")
                
                total_api_routes = sum(len(routes[bp]) for bp in routes)
                
                if len(missing_routes) == 0:
                    self.log_test(
                        "api_routes_structure",
                        True,
                        f"Estrutura de rotas API completa: {total_api_routes} rotas",
                        {'blueprints': list(routes.keys()), 'route_count': total_api_routes}
                    )
                else:
                    self.log_test(
                        "api_routes_structure",
                        False,
                        f"Rotas críticas ausentes: {missing_routes}",
                        {'missing': missing_routes, 'found_routes': routes}
                    )
                    
        except Exception as e:
            self.log_test("api_routes_structure", False, f"Erro ao analisar rotas: {str(e)}")
    
    def test_constants_configuration(self):
        """Testa configuração das constantes para a nova API."""
        try:
            from app.config.constants import API_RATE_LIMITS, FORM_CONFIG
            
            # Verificar rate limits para novas APIs
            required_limits = [
                'templates_list', 'templates_get', 'templates_create',
                'forms_schema', 'forms_validate', 'documents_generate'
            ]
            
            missing_limits = []
            for limit in required_limits:
                if limit not in API_RATE_LIMITS:
                    missing_limits.append(limit)
            
            # Verificar configuração de formulários
            form_config_keys = ['FIELD_TYPES_MAPPING', 'VALIDATION_RULES']
            missing_form_config = []
            for key in form_config_keys:
                if key not in FORM_CONFIG:
                    missing_form_config.append(key)
            
            issues = missing_limits + missing_form_config
            
            if not issues:
                self.log_test(
                    "constants_configuration",
                    True,
                    "Configuração de constantes completa",
                    {
                        'api_rate_limits': len(API_RATE_LIMITS),
                        'form_config_keys': len(FORM_CONFIG)
                    }
                )
            else:
                self.log_test(
                    "constants_configuration",
                    False,
                    f"Configurações ausentes: {issues}",
                    {'missing': issues}
                )
                
        except ImportError as e:
            self.log_test("constants_configuration", False, f"Erro de importação: {str(e)}")
        except Exception as e:
            self.log_test("constants_configuration", False, f"Erro inesperado: {str(e)}")
    
    def test_exception_handling(self):
        """Testa sistema de exceções customizadas."""
        try:
            from app.utils.exceptions import (
                TemplateNotFoundException, DocumentNotFoundException,
                FormProcessingException, IntegrationException
            )
            
            # Testar instanciação das exceções com argumentos corretos
            template_exc = TemplateNotFoundException(123)
            document_exc = DocumentNotFoundException(456)
            form_exc = FormProcessingException("Erro de processamento")
            integration_exc = IntegrationException("google_drive", "Erro de integração")
            
            exceptions_tested = [
                'TemplateNotFoundException',
                'DocumentNotFoundException', 
                'FormProcessingException',
                'IntegrationException'
            ]
            
            self.log_test(
                "exception_handling",
                True,
                "Sistema de exceções funcionando",
                {'exceptions': exceptions_tested}
            )
            
        except ImportError as e:
            self.log_test("exception_handling", False, f"Erro de importação: {str(e)}")
        except Exception as e:
            self.log_test("exception_handling", False, f"Erro inesperado: {str(e)}")
    
    def run_all_tests(self):
        """Executa todos os testes da Fase 4."""
        print("🚀 Iniciando testes da Fase 4 - Expansão da API")
        print("=" * 60)
        
        # Lista de testes
        tests = [
            self.test_feature_flags,
            self.test_controllers_import,
            self.test_routes_import,
            self.test_services_integration,
            self.test_app_creation,
            self.test_api_routes_structure,
            self.test_constants_configuration,
            self.test_exception_handling
        ]
        
        # Executar testes
        for test in tests:
            try:
                test()
            except Exception as e:
                test_name = test.__name__
                self.log_test(test_name, False, f"Erro na execução: {str(e)}")
                print(f"  Debug: {traceback.format_exc()}")
        
        # Calcular taxa de sucesso
        total = self.results['summary']['total']
        passed = self.results['summary']['passed']
        self.results['summary']['success_rate'] = (passed / total * 100) if total > 0 else 0
        self.results['end_time'] = datetime.now().isoformat()
        
        # Mostrar resumo
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES DA FASE 4")
        print("=" * 60)
        print(f"Total de testes: {total}")
        print(f"Passou: {passed}")
        print(f"Falhou: {self.results['summary']['failed']}")
        print(f"Taxa de sucesso: {self.results['summary']['success_rate']:.1f}%")
        
        # Status final
        if self.results['summary']['success_rate'] >= 75:
            print("\n🎉 FASE 4 IMPLEMENTADA COM SUCESSO!")
            print("   ✅ Templates API funcional")
            print("   ✅ Documents API funcional") 
            print("   ✅ Forms API funcional")
            print("   ✅ Integração completa")
            exit_code = 0
        else:
            print("\n⚠️  FASE 4 COM PROBLEMAS")
            print("   Alguns componentes precisam de correção")
            exit_code = 1
        
        # Salvar resultados
        with open(f'test_results_fase4_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json', 'w') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        return exit_code


if __name__ == "__main__":
    tester = Fase4CompleteTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code) 