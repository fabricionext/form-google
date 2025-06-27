#!/usr/bin/env python3
"""
TESTE FASE 6 - QDD/TDD COMPLETE
=============================

Validação completa da Fase 6 do framework Quality-Driven Development:
- 6.1: Transição para Nova Arquitetura (Docker + Nginx + Gunicorn)
- 6.2: Limpeza e Reorganização Final

Autor: Sistema Form Google - Peticionador ADV
Data: 27 de Junho de 2025
"""

import os
import json
import subprocess
import yaml
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

@dataclass
class TestResult:
    test_name: str
    passed: bool
    details: str
    score: float
    category: str

class Fase6QDDValidator:
    """Validador completo da Fase 6 - Transição e Limpeza"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.base_path = Path(".")
        
    def run_all_tests(self) -> Dict:
        """Executa todos os testes da Fase 6"""
        print("🧪 INICIANDO TESTE FASE 6 - QDD/TDD COMPLETE")
        print("=" * 60)
        
        # Fase 6.1: Transição para Nova Arquitetura
        self._test_docker_architecture()
        self._test_nginx_configuration()
        self._test_gunicorn_setup()
        self._test_supervisor_config()
        self._test_backup_system()
        self._test_security_headers()
        self._test_performance_optimization()
        self._test_monitoring_setup()
        
        # Fase 6.2: Limpeza e Reorganização
        self._test_legacy_cleanup()
        self._test_dependency_optimization()
        self._test_code_quality()
        self._test_documentation_update()
        
        # Testes de Integração
        self._test_production_readiness()
        self._test_deployment_automation()
        
        return self._generate_report()
    
    def _test_docker_architecture(self):
        """Testa a arquitetura Docker completa"""
        category = "6.1_DOCKER_ARCHITECTURE"
        
        # Test 1: Docker Compose válido
        try:
            compose_path = self.base_path / "docker-compose.yml"
            if compose_path.exists():
                with open(compose_path) as f:
                    compose_data = yaml.safe_load(f)
                
                required_services = ['app', 'db', 'redis']
                has_services = all(service in compose_data.get('services', {}) 
                                 for service in required_services)
                
                self.results.append(TestResult(
                    "docker_compose_structure",
                    has_services,
                    f"Serviços encontrados: {list(compose_data.get('services', {}).keys())}",
                    100 if has_services else 0,
                    category
                ))
        except Exception as e:
            self.results.append(TestResult(
                "docker_compose_structure", False, f"Erro: {e}", 0, category
            ))
        
        # Test 2: Dockerfile otimizado
        dockerfile_path = self.base_path / "Dockerfile"
        if dockerfile_path.exists():
            with open(dockerfile_path) as f:
                dockerfile_content = f.read()
            
            optimizations = [
                "python:3.11-slim",  # Base image otimizada
                "nginx",              # Nginx integrado
                "supervisor",         # Gerenciador de processos
                "HEALTHCHECK"         # Health check configurado
            ]
            
            optimization_score = sum(
                100 for opt in optimizations 
                if opt in dockerfile_content
            ) / len(optimizations)
            
            self.results.append(TestResult(
                "dockerfile_optimization",
                optimization_score >= 75,
                f"Otimizações encontradas: {optimization_score:.1f}%",
                optimization_score,
                category
            ))
    
    def _test_nginx_configuration(self):
        """Testa configuração do Nginx"""
        category = "6.1_NGINX_CONFIG"
        
        # Test 1: Configuração principal do Nginx
        nginx_conf_path = self.base_path / "docker" / "nginx.conf"
        if nginx_conf_path.exists():
            with open(nginx_conf_path) as f:
                nginx_content = f.read()
            
            required_configs = [
                "gzip on",                    # Compressão
                "limit_req_zone",            # Rate limiting
                "add_header X-Frame-Options", # Security headers
                "worker_processes auto"       # Performance
            ]
            
            config_score = sum(
                100 for config in required_configs 
                if config in nginx_content
            ) / len(required_configs)
            
            self.results.append(TestResult(
                "nginx_main_config",
                config_score >= 75,
                f"Configurações encontradas: {config_score:.1f}%",
                config_score,
                category
            ))
        
        # Test 2: Configuração do site/app
        app_conf_path = self.base_path / "docker" / "app.conf"
        if app_conf_path.exists():
            with open(app_conf_path) as f:
                app_conf_content = f.read()
            
            required_features = [
                "proxy_pass http://gunicorn", # Proxy reverso
                "location /api/",             # API routes
                "return 301",                 # Redirecionamentos
                "try_files $uri $uri/ /index.html" # SPA fallback
            ]
            
            feature_score = sum(
                100 for feature in required_features 
                if feature in app_conf_content
            ) / len(required_features)
            
            self.results.append(TestResult(
                "nginx_app_config",
                feature_score >= 75,
                f"Features encontradas: {feature_score:.1f}%",
                feature_score,
                category
            ))
    
    def _test_gunicorn_setup(self):
        """Testa configuração do Gunicorn"""
        category = "6.1_GUNICORN_SETUP"
        
        gunicorn_conf_path = self.base_path / "docker" / "gunicorn.conf.py"
        if gunicorn_conf_path.exists():
            with open(gunicorn_conf_path) as f:
                gunicorn_content = f.read()
            
            production_configs = [
                "workers = multiprocessing.cpu_count()",  # Workers otimizados
                "max_requests = 1000",                    # Memory leak prevention
                "preload_app = True",                     # Performance
                "errorlog =",                             # Logging configurado
                "timeout = 30"                            # Timeout apropriado
            ]
            
            config_score = sum(
                100 for config in production_configs 
                if config in gunicorn_content
            ) / len(production_configs)
            
            self.results.append(TestResult(
                "gunicorn_production_config",
                config_score >= 80,
                f"Configurações de produção: {config_score:.1f}%",
                config_score,
                category
            ))
    
    def _test_supervisor_config(self):
        """Testa configuração do Supervisor"""
        category = "6.1_SUPERVISOR"
        
        supervisor_conf_path = self.base_path / "docker" / "supervisord.conf"
        if supervisor_conf_path.exists():
            with open(supervisor_conf_path) as f:
                supervisor_content = f.read()
            
            required_programs = [
                "[program:gunicorn]",  # Gunicorn gerenciado
                "[program:nginx]",     # Nginx gerenciado
                "autorestart=true",    # Auto restart
                "redirect_stderr=true" # Log management
            ]
            
            program_score = sum(
                100 for program in required_programs 
                if program in supervisor_content
            ) / len(required_programs)
            
            self.results.append(TestResult(
                "supervisor_process_management",
                program_score >= 75,
                f"Gerenciamento de processos: {program_score:.1f}%",
                program_score,
                category
            ))
    
    def _test_backup_system(self):
        """Testa sistema de backup"""
        category = "6.1_BACKUP_SYSTEM"
        
        backup_script_path = self.base_path / "docker" / "backup.sh"
        if backup_script_path.exists():
            with open(backup_script_path) as f:
                backup_content = f.read()
            
            backup_features = [
                "pg_dump",                    # Database backup
                "gzip",                       # Compression
                "RETENTION_DAYS",             # Retention policy
                "find.*-mtime.*-delete",      # Cleanup old backups
                "stat -c%s"                   # Size verification
            ]
            
            feature_score = sum(
                100 for feature in backup_features 
                if feature in backup_content
            ) / len(backup_features)
            
            self.results.append(TestResult(
                "backup_automation",
                feature_score >= 80,
                f"Features de backup: {feature_score:.1f}%",
                feature_score,
                category
            ))
    
    def _test_security_headers(self):
        """Testa headers de segurança"""
        category = "6.1_SECURITY"
        
        # Verificar se headers de segurança estão configurados
        nginx_files = [
            self.base_path / "docker" / "nginx.conf",
            self.base_path / "docker" / "app.conf"
        ]
        
        security_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy"
        ]
        
        total_headers_found = 0
        for nginx_file in nginx_files:
            if nginx_file.exists():
                with open(nginx_file) as f:
                    content = f.read()
                    total_headers_found += sum(
                        1 for header in security_headers 
                        if header in content
                    )
        
        security_score = (total_headers_found / len(security_headers)) * 100
        
        self.results.append(TestResult(
            "security_headers",
            security_score >= 80,
            f"Headers de segurança: {total_headers_found}/{len(security_headers)}",
            security_score,
            category
        ))
    
    def _test_performance_optimization(self):
        """Testa otimizações de performance"""
        category = "6.1_PERFORMANCE"
        
        # Verificar otimizações no Nginx
        nginx_conf_path = self.base_path / "docker" / "nginx.conf"
        if nginx_conf_path.exists():
            with open(nginx_conf_path) as f:
                nginx_content = f.read()
            
            performance_features = [
                "gzip on",                    # Compressão
                "expires",                    # Cache headers
                "keepalive",                  # Connection reuse
                "worker_connections",         # Connection limit
                "limit_req_zone"              # Rate limiting
            ]
            
            perf_score = sum(
                100 for feature in performance_features 
                if feature in nginx_content
            ) / len(performance_features)
            
            self.results.append(TestResult(
                "nginx_performance_optimization",
                perf_score >= 80,
                f"Otimizações de performance: {perf_score:.1f}%",
                perf_score,
                category
            ))
    
    def _test_monitoring_setup(self):
        """Testa configuração de monitoramento"""
        category = "6.1_MONITORING"
        
        # Verificar health checks
        dockerfile_path = self.base_path / "Dockerfile"
        has_healthcheck = False
        
        if dockerfile_path.exists():
            with open(dockerfile_path) as f:
                dockerfile_content = f.read()
                has_healthcheck = "HEALTHCHECK" in dockerfile_content
        
        # Verificar endpoint de health no Nginx
        app_conf_path = self.base_path / "docker" / "app.conf"
        has_health_endpoint = False
        
        if app_conf_path.exists():
            with open(app_conf_path) as f:
                app_conf_content = f.read()
                has_health_endpoint = "location /health" in app_conf_content
        
        monitoring_score = (
            (100 if has_healthcheck else 0) +
            (100 if has_health_endpoint else 0)
        ) / 2
        
        self.results.append(TestResult(
            "health_monitoring",
            monitoring_score >= 75,
            f"Health check: {has_healthcheck}, Health endpoint: {has_health_endpoint}",
            monitoring_score,
            category
        ))
    
    def _test_legacy_cleanup(self):
        """Testa limpeza de código legado"""
        category = "6.2_LEGACY_CLEANUP"
        
        # Verificar se diretórios legados ainda existem
        legacy_paths = [
            self.base_path / "app" / "peticionador",
            self.base_path / "archive" / "scripts",
            self.base_path / "backup_before_cleanup_20250625_232228.tar.gz"
        ]
        
        legacy_remaining = sum(1 for path in legacy_paths if path.exists())
        cleanup_score = max(0, (len(legacy_paths) - legacy_remaining) / len(legacy_paths) * 100)
        
        self.results.append(TestResult(
            "legacy_code_cleanup",
            cleanup_score >= 60,  # Permitir algum código legado ainda
            f"Código legado restante: {legacy_remaining}/{len(legacy_paths)} diretórios",
            cleanup_score,
            category
        ))
        
        # Verificar se feature flags estão ativas para nova API
        constants_path = self.base_path / "app" / "config" / "constants.py"
        if constants_path.exists():
            with open(constants_path) as f:
                constants_content = f.read()
            
            new_apis = [
                "'NEW_AUTH_API': True",
                "'NEW_CLIENTS_API': True", 
                "'NEW_TEMPLATES_API': True",
                "'NEW_FORMS_API': True",
                "'NEW_DOCUMENTS_API': True"
            ]
            
            active_apis = sum(
                1 for api in new_apis 
                if api in constants_content
            )
            
            api_score = (active_apis / len(new_apis)) * 100
            
            self.results.append(TestResult(
                "feature_flags_migration",
                api_score >= 80,
                f"APIs ativas: {active_apis}/{len(new_apis)}",
                api_score,
                category
            ))
    
    def _test_dependency_optimization(self):
        """Testa otimização de dependências"""
        category = "6.2_DEPENDENCIES"
        
        # Verificar requirements.txt
        requirements_path = self.base_path / "requirements.txt"
        if requirements_path.exists():
            with open(requirements_path) as f:
                requirements = f.read()
            
            # Contar linhas não vazias (dependências)
            deps_count = len([line for line in requirements.split('\n') if line.strip() and not line.startswith('#')])
            
            # Score baseado na quantidade (menos é melhor para dependencies cleanup)
            deps_score = max(0, 100 - (deps_count - 15) * 2)  # Ideal ~15 deps
            
            self.results.append(TestResult(
                "python_dependencies_optimization",
                deps_score >= 70,
                f"Dependências Python: {deps_count}",
                deps_score,
                category
            ))
        
        # Verificar package.json
        package_json_path = self.base_path / "package.json"
        if package_json_path.exists():
            with open(package_json_path) as f:
                package_data = json.load(f)
            
            deps = package_data.get('dependencies', {})
            dev_deps = package_data.get('devDependencies', {})
            total_js_deps = len(deps) + len(dev_deps)
            
            js_deps_score = max(0, 100 - (total_js_deps - 25) * 1.5)  # Ideal ~25 deps
            
            self.results.append(TestResult(
                "javascript_dependencies_optimization",
                js_deps_score >= 70,
                f"Dependências JS: {total_js_deps} (prod: {len(deps)}, dev: {len(dev_deps)})",
                js_deps_score,
                category
            ))
    
    def _test_code_quality(self):
        """Testa qualidade do código"""
        category = "6.2_CODE_QUALITY"
        
        # Verificar configuração de linting
        linting_configs = [
            self.base_path / ".flake8",
            self.base_path / "mypy.ini", 
            self.base_path / "pyproject.toml",
            self.base_path / "eslint.config.mjs"
        ]
        
        linting_score = sum(
            100 for config in linting_configs 
            if config.exists()
        ) / len(linting_configs)
        
        self.results.append(TestResult(
            "linting_configuration",
            linting_score >= 75,
            f"Arquivos de linting: {sum(1 for c in linting_configs if c.exists())}/{len(linting_configs)}",
            linting_score,
            category
        ))
        
        # Verificar cobertura de testes
        coverage_files = [
            self.base_path / ".coverage",
            self.base_path / "vitest.config.js"
        ]
        
        coverage_score = sum(
            100 for config in coverage_files 
            if config.exists()
        ) / len(coverage_files)
        
        self.results.append(TestResult(
            "test_coverage_setup",
            coverage_score >= 50,
            f"Configuração de cobertura: {sum(1 for c in coverage_files if c.exists())}/{len(coverage_files)}",
            coverage_score,
            category
        ))
    
    def _test_documentation_update(self):
        """Testa atualização da documentação"""
        category = "6.2_DOCUMENTATION"
        
        # Verificar arquivos de documentação
        doc_files = [
            self.base_path / "README.md",
            self.base_path / "docs" / "README.md",
            self.base_path / "RELATORIO_FINAL_QDD_TDD_FASES_4_5.md"
        ]
        
        docs_score = sum(
            100 for doc in doc_files 
            if doc.exists()
        ) / len(doc_files)
        
        self.results.append(TestResult(
            "documentation_completeness",
            docs_score >= 66,
            f"Documentação encontrada: {sum(1 for d in doc_files if d.exists())}/{len(doc_files)}",
            docs_score,
            category
        ))
    
    def _test_production_readiness(self):
        """Testa prontidão para produção"""
        category = "INTEGRATION_PRODUCTION"
        
        # Verificar arquivos essenciais de produção
        prod_files = [
            self.base_path / "docker-compose.yml",
            self.base_path / "Dockerfile", 
            self.base_path / "docker" / "nginx.conf",
            self.base_path / "docker" / "gunicorn.conf.py",
            self.base_path / "docker" / "supervisord.conf"
        ]
        
        prod_score = sum(
            100 for file in prod_files 
            if file.exists()
        ) / len(prod_files)
        
        self.results.append(TestResult(
            "production_files_completeness",
            prod_score >= 80,
            f"Arquivos de produção: {sum(1 for f in prod_files if f.exists())}/{len(prod_files)}",
            prod_score,
            category
        ))
    
    def _test_deployment_automation(self):
        """Testa automação de deployment"""
        category = "INTEGRATION_DEPLOYMENT"
        
        # Verificar scripts de deployment
        deployment_scripts = [
            self.base_path / "docker" / "start.sh",
            self.base_path / "docker" / "backup.sh",
            self.base_path / "install.sh"
        ]
        
        deployment_score = sum(
            100 for script in deployment_scripts 
            if script.exists()
        ) / len(deployment_scripts)
        
        self.results.append(TestResult(
            "deployment_automation",
            deployment_score >= 66,
            f"Scripts de deployment: {sum(1 for s in deployment_scripts if s.exists())}/{len(deployment_scripts)}",
            deployment_score,
            category
        ))
    
    def _generate_report(self) -> Dict:
        """Gera relatório final dos testes"""
        
        # Calcular scores por categoria
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = {'scores': [], 'passed': 0, 'total': 0}
            
            categories[result.category]['scores'].append(result.score)
            categories[result.category]['total'] += 1
            if result.passed:
                categories[result.category]['passed'] += 1
        
        # Calcular médias por categoria
        category_scores = {}
        for category, data in categories.items():
            avg_score = sum(data['scores']) / len(data['scores'])
            category_scores[category] = {
                'score': avg_score,
                'passed': data['passed'],
                'total': data['total'],
                'pass_rate': (data['passed'] / data['total']) * 100
            }
        
        # Score geral da Fase 6
        overall_score = sum(
            score['score'] for score in category_scores.values()
        ) / len(category_scores)
        
        # Determinar status geral
        if overall_score >= 90:
            status = "🚀 EXCELENTE"
        elif overall_score >= 80:
            status = "✅ BOM"
        elif overall_score >= 70:
            status = "⚠️ ACEITÁVEL"
        else:
            status = "❌ REQUER MELHORIAS"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'fase': 'FASE 6 - TRANSIÇÃO E LIMPEZA',
            'overall_score': overall_score,
            'status': status,
            'categories': category_scores,
            'detailed_results': [
                {
                    'test': r.test_name,
                    'passed': r.passed,
                    'score': r.score,
                    'details': r.details,
                    'category': r.category
                }
                for r in self.results
            ],
            'summary': {
                'total_tests': len(self.results),
                'passed_tests': sum(1 for r in self.results if r.passed),
                'failed_tests': sum(1 for r in self.results if not r.passed),
                'pass_rate': (sum(1 for r in self.results if r.passed) / len(self.results)) * 100
            }
        }
        
        return report

def main():
    """Função principal"""
    validator = Fase6QDDValidator()
    report = validator.run_all_tests()
    
    # Mostrar relatório
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL - FASE 6 QDD/TDD")
    print("=" * 60)
    
    print(f"\n🎯 **SCORE GERAL**: {report['overall_score']:.1f}% - {report['status']}")
    print(f"📋 **TESTES**: {report['summary']['passed_tests']}/{report['summary']['total_tests']} aprovados ({report['summary']['pass_rate']:.1f}%)")
    
    print(f"\n📈 **SCORES POR CATEGORIA**:")
    for category, data in report['categories'].items():
        print(f"  - {category}: {data['score']:.1f}% ({data['passed']}/{data['total']} testes)")
    
    print(f"\n🔍 **DETALHES DOS TESTES**:")
    for result in report['detailed_results']:
        status_icon = "✅" if result['passed'] else "❌"
        print(f"  {status_icon} {result['test']}: {result['score']:.1f}% - {result['details']}")
    
    # Salvar relatório
    report_file = f"test_results_fase6_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 **Relatório salvo**: {report_file}")
    
    # Recomendações
    print(f"\n💡 **PRÓXIMOS PASSOS**:")
    if report['overall_score'] >= 85:
        print("  🎉 Fase 6 implementada com sucesso!")
        print("  🚀 Sistema pronto para produção")
    else:
        failed_tests = [r for r in report['detailed_results'] if not r['passed']]
        print("  📋 Corrigir testes falhando:")
        for test in failed_tests[:3]:  # Top 3
            print(f"    - {test['test']}: {test['details']}")
    
    return report

if __name__ == "__main__":
    report = main() 