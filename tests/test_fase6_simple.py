#!/usr/bin/env python3
"""
TESTE FASE 6 QDD/TDD - Arquitetura e Limpeza
"""

import os
import json
from pathlib import Path
from datetime import datetime

def test_fase6():
    """Testa implementação da Fase 6"""
    
    print("🧪 INICIANDO TESTE FASE 6 - QDD/TDD")
    print("=" * 50)
    
    results = []
    
    # Test 1: Docker Architecture
    docker_files = ['docker-compose.yml', 'Dockerfile', 'docker/nginx.conf', 'docker/gunicorn.conf.py']
    docker_score = sum(100 for f in docker_files if Path(f).exists()) / len(docker_files)
    
    print(f"🐳 Docker Architecture: {docker_score:.1f}%")
    results.append({'test': 'docker_architecture', 'score': docker_score, 'passed': docker_score >= 75})
    
    # Test 2: Feature Flags
    try:
        with open('app/config/constants.py') as f:
            content = f.read()
        
        flags = ['NEW_AUTH_API', 'NEW_CLIENTS_API', 'NEW_TEMPLATES_API', 'NEW_FORMS_API', 'NEW_DOCUMENTS_API']
        active_flags = sum(1 for flag in flags if f"'{flag}': True" in content)
        flags_score = (active_flags / len(flags)) * 100
        
        print(f"🚩 Feature Flags: {active_flags}/{len(flags)} ativas ({flags_score:.1f}%)")
        results.append({'test': 'feature_flags', 'score': flags_score, 'passed': flags_score >= 80})
        
    except Exception as e:
        print(f"❌ Feature Flags: Erro - {e}")
        results.append({'test': 'feature_flags', 'score': 0, 'passed': False})
    
    # Test 3: Legacy Cleanup
    legacy_items = ['app/peticionador']
    legacy_remaining = sum(1 for item in legacy_items if Path(item).exists())
    cleanup_score = max(0, (len(legacy_items) - legacy_remaining) / len(legacy_items) * 100)
    
    print(f"🧹 Legacy Cleanup: {legacy_remaining} itens restantes ({cleanup_score:.1f}% limpo)")
    results.append({'test': 'legacy_cleanup', 'score': cleanup_score, 'passed': cleanup_score >= 25})
    
    # Test 4: Production Files
    prod_files = ['docker/supervisord.conf', 'docker/backup.sh', 'docker/app.conf']
    prod_score = sum(100 for f in prod_files if Path(f).exists()) / len(prod_files)
    
    print(f"🚀 Production Files: {prod_score:.1f}%")
    results.append({'test': 'production_files', 'score': prod_score, 'passed': prod_score >= 75})
    
    # Test 5: Security Headers
    try:
        security_score = 0
        if Path('docker/nginx.conf').exists():
            with open('docker/nginx.conf') as f:
                nginx_content = f.read()
            
            headers = ['X-Frame-Options', 'X-Content-Type-Options', 'X-XSS-Protection']
            found_headers = sum(1 for h in headers if h in nginx_content)
            security_score = (found_headers / len(headers)) * 100
        
        print(f"🔒 Security Headers: {security_score:.1f}%")
        results.append({'test': 'security_headers', 'score': security_score, 'passed': security_score >= 60})
        
    except Exception as e:
        print(f"❌ Security Headers: Erro - {e}")
        results.append({'test': 'security_headers', 'score': 0, 'passed': False})
    
    # Calculate overall score
    overall_score = sum(r['score'] for r in results) / len(results)
    passed_tests = sum(1 for r in results if r['passed'])
    
    # Generate status
    if overall_score >= 85:
        status = "🚀 EXCELENTE"
    elif overall_score >= 75:
        status = "✅ BOM"
    elif overall_score >= 65:
        status = "⚠️ ACEITÁVEL"
    else:
        status = "❌ PRECISA MELHORAR"
    
    print(f"\n📊 RESULTADO FINAL:")
    print(f"Score Geral: {overall_score:.1f}% - {status}")
    print(f"Testes Aprovados: {passed_tests}/{len(results)}")
    
    # Save report
    report = {
        'timestamp': datetime.now().isoformat(),
        'fase': 'FASE 6 - TRANSIÇÃO E LIMPEZA',
        'overall_score': overall_score,
        'status': status,
        'results': results,
        'passed_tests': passed_tests,
        'total_tests': len(results)
    }
    
    report_file = f"fase6_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Relatório salvo: {report_file}")
    
    return report

if __name__ == "__main__":
    test_fase6() 