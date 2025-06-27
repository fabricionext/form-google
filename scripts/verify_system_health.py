#!/usr/bin/env python3
"""
Script de Verificação da Saúde do Sistema
=========================================

Verifica se o sistema está funcionando corretamente e se precisa de restart.
Criado para resolver os erros reportados de forma proativa.
"""

import os
import sys

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/var/www/estevaoalmeida.com.br/form-google')

def main():
    print("🔍 VERIFICANDO SAÚDE DO SISTEMA")
    print("=" * 50)
    
    try:
        from app import create_app
        from app.peticionador.services.system_monitor import check_system_and_recommend_action
        
        app = create_app()
        
        with app.app_context():
            result = check_system_and_recommend_action()
            
            print(result['summary'])
            print()
            
            # Detalhes das verificações
            health = result['health']
            print("📋 DETALHES DAS VERIFICAÇÕES:")
            for check_name, check_result in health['checks'].items():
                status_icon = {
                    'ok': '✅',
                    'warning': '⚠️',
                    'critical': '🚨',
                    'error': '❌'
                }.get(check_result['status'], '❓')
                
                print(f"  {status_icon} {check_name.upper()}: {check_result['message']}")
            
            # Recomendações
            if result['should_restart']:
                print()
                print("🔄 AÇÃO RECOMENDADA:")
                print(f"   {result['restart_command']}")
                print()
                print("💡 MOTIVOS PARA RESTART:")
                for reason in result['restart_reasons']:
                    print(f"   - {reason}")
            
            # Status dos erros reportados
            print()
            print("🎯 STATUS DOS ERROS REPORTADOS:")
            
            # Verificar se o formulário existe
            from app.peticionador.models import FormularioGerado
            form = FormularioGerado.query.filter_by(
                slug='suspensao-do-direito-de-dirigir-junho-2025-8bced464'
            ).first()
            
            if form:
                print("   ✅ Formulário 'suspensao-do-direito-de-dirigir-junho-2025-8bced464' existe no banco")
                print(f"      Nome: {form.nome}")
                print(f"      Modelo ID: {form.modelo_id}")
            else:
                print("   ❌ Formulário 'suspensao-do-direito-de-dirigir-junho-2025-8bced464' NÃO encontrado")
            
            # Verificar se as correções estão implementadas
            try:
                from app.peticionador.services.formulario_manager import formulario_manager
                print("   ✅ FormularioManager robusto implementado")
            except Exception as e:
                print(f"   ❌ FormularioManager não disponível: {e}")
            
            try:
                from app.peticionador.utils import safe_extract_placeholder_keys
                # Testar com dados que causavam erro
                test_data = [{'key': 'test'}, 'string_test']
                result_test = safe_extract_placeholder_keys(test_data)
                print("   ✅ Função safe_extract_placeholder_keys funcionando")
            except Exception as e:
                print(f"   ❌ Função safe_extract_placeholder_keys com erro: {e}")
            
            # Status final
            print()
            if result['should_restart']:
                print("🔄 CONCLUSÃO: RESTART DO SISTEMA RECOMENDADO")
                print(f"   Execute: {result['restart_command']}")
                return 1
            else:
                print("✅ CONCLUSÃO: SISTEMA FUNCIONANDO CORRETAMENTE")
                print("   Nenhuma ação necessária no momento")
                return 0
    
    except Exception as e:
        print(f"❌ ERRO CRÍTICO na verificação do sistema: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("🔄 RESTART URGENTE RECOMENDADO devido a erro crítico")
        return 2

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)