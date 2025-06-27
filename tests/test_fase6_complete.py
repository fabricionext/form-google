#!/usr/bin/env python3
"""
TESTE FASE 6 - QDD/TDD ARQUITETURA E LIMPEZA
============================================

Validação da Fase 6 do framework Quality-Driven Development:
- 6.1: Transição para Nova Arquitetura
- 6.2: Limpeza e Reorganização Final
"""

import os
import json
import yaml
from pathlib import Path
from datetime import datetime

def test_fase6_architecture():
    """Testa arquitetura de produção da Fase 6.1"""
    results = []
    
    print("🧪 TESTANDO FASE 6.1 - ARQUITETURA DE PRODUÇÃO")
    print("-" * 50)
    
    # Test 1: Docker Compose
    try:
        with open("docker-compose.yml") as f:
            compose = yaml.safe_load(f)
        
        required_services = ['app', 'db', 'redis']
        has_services = all(s in compose.get('services', {}) for s in required_services)
        
        print(f"✅ Docker Compose: {has_services}")
        results.append({"test": "docker_compose", "passed": has_services, "score": 100 if has_services else 0})
        
    except Exception as e:
        print(f"❌ Docker Compose: {e}")
        results.append({"test": "docker_compose", "passed": False, "score": 0})
    
    # Test 2: Nginx Configuration
    try:
        with open("docker/nginx.conf") as f:
            nginx_content = f.read()
        
        nginx_features = ["gzip on", "limit_req_zone", "add_header X-Frame-Options"]
        nginx_score = sum(100 for f in nginx_features if f in nginx_content) / len(nginx_features)
        
        print(f"✅ Nginx Config: {nginx_score:.1f}%")
        results.append({"test": "nginx_config", "passed": nginx_score >= 75, "score": nginx_score})
        
    except Exception as e:
        print(f"❌ Nginx Config: {e}")
        results.append({"test": "nginx_config", "passed": False, "score": 0})
    
    # Test 3: Gunicorn Configuration
    try:
        with open("docker/gunicorn.conf.py") as f:
            gunicorn_content = f.read()
        
        gunicorn_features = ["workers = multiprocessing", "max_requests = 1000", "preload_app = True"]
        gunicorn_score = sum(100 for f in gunicorn_features if f in gunicorn_content) / len(gunicorn_features)
        
        print(f"✅ Gunicorn Config: {gunicorn_score:.1f}%")
        results.append({"test": "gunicorn_config", "passed": gunicorn_score >= 75, "score": gunicorn_score})
        
    except Exception as e:
        print(f"❌ Gunicorn Config: {e}")
        results.append({"test": "gunicorn_config", "passed": False, "score": 0})
    
    # Test 4: Supervisor Configuration
    try:
        with open("docker/supervisord.conf") as f:
            supervisor_content = f.read()
        
        supervisor_features = ["[program:gunicorn]", "[program:nginx]", "autorestart=true"]
        supervisor_score = sum(100 for f in supervisor_features if f in supervisor_content) / len(supervisor_features)
        
        print(f"✅ Supervisor Config: {supervisor_score:.1f}%")
        results.append({"test": "supervisor_config", "passed": supervisor_score >= 75, "score": supervisor_score})
        
    except Exception as e:
        print(f"❌ Supervisor Config: {e}")
        results.append({"test": "supervisor_config", "passed": False, "score": 0})
    
    # Test 5: Backup System
    try:
        with open("docker/backup.sh") as f:
            backup_content = f.read()
        
        backup_features = ["pg_dump", "gzip", "RETENTION_DAYS"]
        backup_score = sum(100 for f in backup_features if f in backup_content) / len(backup_features)
        
        print(f"✅ Backup System: {backup_score:.1f}%")
        results.append({"test": "backup_system", "passed": backup_score >= 75, "score": backup_score})
        
    except Exception as e:
        print(f"❌ Backup System: {e}")
        results.append({"test": "backup_system", "passed": False, "score": 0})
    
    return results

def test_fase6_cleanup():
    """Testa limpeza de código da Fase 6.2"""
    results = []
    
    print("\n🧹 TESTANDO FASE 6.2 - LIMPEZA E ORGANIZAÇÃO")
    print("-" * 50)
    
    # Test 1: Feature Flags Migration
    try:
        with open("app/config/constants.py") as f:
            constants_content = f.read()
        
        new_apis = [
            "'NEW_AUTH_API': True",
            "'NEW_CLIENTS_API': True", 
            "'NEW_TEMPLATES_API': True",
            "'NEW_FORMS_API': True",
            "'NEW_DOCUMENTS_API': True"
        ]
        
        active_apis = sum(1 for api in new_apis if api in constants_content)
        api_score = (active_apis / len(new_apis)) * 100
        
        print(f"✅ Feature Flags: {active_apis}/{len(new_apis)} ativas ({api_score:.1f}%)")
        results.append({"test": "feature_flags", "passed": api_score >= 80, "score": api_score})
        
    except Exception as e:
        print(f"❌ Feature Flags: {e}")
        results.append({"test": "feature_flags", "passed": False, "score": 0})
    
    # Test 2: Legacy Code Cleanup
    legacy_paths = [
        "app/peticionador",
        "backup_before_cleanup_20250625_232228.tar.gz"
    ]
    
    legacy_remaining = sum(1 for path in legacy_paths if Path(path).exists())
    cleanup_score = max(0, (len(legacy_paths) - legacy_remaining) / len(legacy_paths) * 100)
    
    print(f"⚠️ Código Legado: {legacy_remaining}/{len(legacy_paths)} restantes ({cleanup_score:.1f}% limpo)")
    results.append({"test": "legacy_cleanup", "passed": cleanup_score >= 50, "score": cleanup_score})
    
    # Test 3: Dependencies Optimization
    try:
        with open("requirements.txt") as f:
            requirements = f.read()
        
        deps_count = len([line for line in requirements.split('\n') if line.strip() and not line.startswith('#')])
        deps_score = max(0, 100 - (deps_count - 15) * 2)  # Ideal ~15 deps
        
        print(f"✅ Python Dependencies: {deps_count} dependências ({deps_score:.1f}% otimizado)")
        results.append({"test": "python_deps", "passed": deps_score >= 70, "score": deps_score})
        
    except Exception as e:
        print(f"❌ Python Dependencies: {e}")
        results.append({"test": "python_deps", "passed": False, "score": 0})
    
    # Test 4: Test Coverage
    coverage_files = [".coverage", "vitest.config.js"]
    coverage_exists = sum(1 for f in coverage_files if Path(f).exists())
    coverage_score = (coverage_exists / len(coverage_files)) * 100
    
    print(f"✅ Test Coverage: {coverage_exists}/{len(coverage_files)} configurados ({coverage_score:.1f}%)")
    results.append({"test": "test_coverage", "passed": coverage_score >= 50, "score": coverage_score})
    
    return results

def test_production_readiness():
    """Testa prontidão geral para produção"""
    results = []
    
    print("\n🚀 TESTANDO PRONTIDÃO PARA PRODUÇÃO")
    print("-" * 50)
    
    # Test 1: Essential Production Files
    prod_files = [
        "docker-compose.yml",
        "Dockerfile", 
        "docker/nginx.conf",
        "docker/gunicorn.conf.py",
        "docker/supervisord.conf"
    ]
    
    prod_exists = sum(1 for f in prod_files if Path(f).exists())
    prod_score = (prod_exists / len(prod_files)) * 100
    
    print(f"✅ Arquivos de Produção: {prod_exists}/{len(prod_files)} ({prod_score:.1f}%)")
    results.append({"test": "production_files", "passed": prod_score >= 80, "score": prod_score})
    
    # Test 2: Health Monitoring
    has_healthcheck = False
    has_health_endpoint = False
    
    try:
        with open("Dockerfile") as f:
            dockerfile_content = f.read()
            has_healthcheck = "HEALTHCHECK" in dockerfile_content
        
        with open("docker/app.conf") as f:
            app_conf_content = f.read()
            has_health_endpoint = "location /health" in app_conf_content
        
        monitoring_score = ((100 if has_healthcheck else 0) + (100 if has_health_endpoint else 0)) / 2
        
        print(f"✅ Health Monitoring: Docker={has_healthcheck}, Nginx={has_health_endpoint} ({monitoring_score:.1f}%)")
        results.append({"test": "health_monitoring", "passed": monitoring_score >= 75, "score": monitoring_score})
        
    except Exception as e:
        print(f"❌ Health Monitoring: {e}")
        results.append({"test": "health_monitoring", "passed": False, "score": 0})
    
    # Test 3: Security Headers
    try:
        security_files = ["docker/nginx.conf", "docker/app.conf"]
        security_headers = ["X-Frame-Options", "X-Content-Type-Options", "X-XSS-Protection"]
        
        total_headers = 0
        for security_file in security_files:
            if Path(security_file).exists():
                with open(security_file) as f:
                    content = f.read()
                    total_headers += sum(1 for h in security_headers if h in content)
        
        security_score = (total_headers / (len(security_headers) * len(security_files))) * 100
        
        print(f"✅ Security Headers: {total_headers} headers configurados ({security_score:.1f}%)")
        results.append({"test": "security_headers", "passed": security_score >= 60, "score": security_score})
        
    except Exception as e:
        print(f"❌ Security Headers: {e}")
        results.append({"test": "security_headers", "passed": False, "score": 0})
    
    return results

def generate_final_report(arch_results, cleanup_results, prod_results):
    """Gera relatório final da Fase 6"""
    
    all_results = arch_results + cleanup_results + prod_results
    
    # Calcular scores
    total_score = sum(r['score'] for r in all_results) / len(all_results)
    passed_tests = sum(1 for r in all_results if r['passed'])
    total_tests = len(all_results)
    pass_rate = (passed_tests / total_tests) * 100
    
    # Determinar status
    if total_score >= 90:
        status = "🚀 EXCELENTE"
        recommendation = "Sistema pronto para produção!"
    elif total_score >= 80:
        status = "✅ BOM"
        recommendation = "Pequenos ajustes recomendados"
    elif total_score >= 70:
        status = "⚠️ ACEITÁVEL"
        recommendation = "Algumas melhorias necessárias"
    else:
        status = "❌ REQUER MELHORIAS"
        recommendation = "Correções importantes necessárias"
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'fase': 'FASE 6 - TRANSIÇÃO E LIMPEZA',
        'overall_score': total_score,
        'status': status,
        'recommendation': recommendation,
        'summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'pass_rate': pass_rate
        },
        'detailed_results': all_results,
        'phase_scores': {
            'fase_6_1_architecture': sum(r['score'] for r in arch_results) / len(arch_results),
            'fase_6_2_cleanup': sum(r['score'] for r in cleanup_results) / len(cleanup_results),
            'production_readiness': sum(r['score'] for r in prod_results) / len(prod_results)
        }
    }
    
    return report

def main():
    """Função principal"""
    print("🔬 TESTE FASE 6 - QDD/TDD COMPLETE")
    print("=" * 60)
    
    # Executar testes
    arch_results = test_fase6_architecture()
    cleanup_results = test_fase6_cleanup()
    prod_results = test_production_readiness()
    
    # Gerar relatório
    report = generate_final_report(arch_results, cleanup_results, prod_results)
    
    # Mostrar relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL - FASE 6")
    print("=" * 60)
    
    print(f"\n🎯 SCORE GERAL: {report['overall_score']:.1f}% - {report['status']}")
    print(f"📋 TESTES: {report['summary']['passed_tests']}/{report['summary']['total_tests']} aprovados ({report['summary']['pass_rate']:.1f}%)")
    
    print(f"\n📈 SCORES POR FASE:")
    print(f"  - Fase 6.1 (Arquitetura): {report['phase_scores']['fase_6_1_architecture']:.1f}%")
    print(f"  - Fase 6.2 (Limpeza): {report['phase_scores']['fase_6_2_cleanup']:.1f}%")
    print(f"  - Prontidão Produção: {report['phase_scores']['production_readiness']:.1f}%")
    
    print(f"\n💡 RECOMENDAÇÃO: {report['recommendation']}")
    
    # Salvar relatório
    report_file = f"test_results_fase6_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Relatório salvo: {report_file}")
    
    return report

if __name__ == "__main__":
    main() 