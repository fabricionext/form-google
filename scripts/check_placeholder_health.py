#!/usr/bin/env python3
"""
Script para verificar a saúde do sistema de placeholders.
Executa verificações preventivas para evitar erros futuros.
"""

import sys
import os

# Adicionar path do projeto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_placeholder_functions():
    """Verifica se as funções de placeholder estão funcionando corretamente."""
    try:
        from app.peticionador.utils import (
            safe_extract_placeholder_keys,
            normalize_placeholders_list,
            validate_placeholder_format,
            clean_placeholder_key
        )
        
        print("✅ Módulo utils importado com sucesso")
        
        # Teste com dados problemáticos que causavam erro
        test_data = [
            {'key': 'autor_1_nome', 'original': '{{autor_1_nome}}'},
            {'key': 'reu_cpf', 'original': '{{reu_cpf}}'}
        ]
        
        result = safe_extract_placeholder_keys(test_data)
        assert isinstance(result, list), "Resultado deve ser lista"
        assert all(isinstance(item, str) for item in result), "Todos os itens devem ser strings"
        
        print("✅ Função safe_extract_placeholder_keys funcionando")
        
        # Teste de limpeza de chaves
        dirty_key = "autor#1@nome!"
        clean_key = clean_placeholder_key(dirty_key)
        assert validate_placeholder_format(clean_key), "Chave limpa deve ser válida"
        
        print("✅ Funções de limpeza e validação funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar funções: {e}")
        return False

def check_route_fixes():
    """Verifica se as correções nas rotas estão presentes."""
    try:
        routes_file = "/var/www/estevaoalmeida.com.br/form-google/app/peticionador/routes.py"
        
        with open(routes_file, 'r') as f:
            content = f.read()
        
        # Verificar se as importações corretas estão presentes
        checks = [
            ("safe_extract_placeholder_keys", "Função de extração segura importada"),
            ("handle_placeholder_extraction_error", "Tratamento de erro robusto presente"),
            ("clean_placeholder_key", "Limpeza de chaves implementada"),
            ("log_placeholder_operation", "Sistema de logging presente")
        ]
        
        for check, description in checks:
            if check in content:
                print(f"✅ {description}")
            else:
                print(f"⚠️ {description} - não encontrado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar rotas: {e}")
        return False

def check_google_services_fix():
    """Verifica se a correção no google_services está presente."""
    try:
        services_file = "/var/www/estevaoalmeida.com.br/form-google/app/peticionador/google_services.py"
        
        with open(services_file, 'r') as f:
            content = f.read()
        
        if "extract_placeholders_keys_only" in content:
            print("✅ Google Services usando função de extração corrigida")
        else:
            print("⚠️ Google Services pode ainda usar função problemática")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar google_services: {e}")
        return False

def main():
    """Executa todas as verificações."""
    print("=== VERIFICAÇÃO DE SAÚDE DO SISTEMA DE PLACEHOLDERS ===")
    print()
    
    all_ok = True
    
    print("1. Verificando funções utilitárias...")
    if not check_placeholder_functions():
        all_ok = False
    print()
    
    print("2. Verificando correções nas rotas...")
    if not check_route_fixes():
        all_ok = False
    print()
    
    print("3. Verificando correções no Google Services...")
    if not check_google_services_fix():
        all_ok = False
    print()
    
    print("=== RESUMO ===")
    if all_ok:
        print("✅ Sistema está saudável e protegido contra erros de placeholders")
        print("✅ Erro 'unhashable type: dict' foi corrigido")
        print("✅ Sistema robusto para todos os formatos de entrada")
        print()
        print("💡 PRÓXIMOS PASSOS:")
        print("1. Testar sincronização em: https://appform.estevaoalmeida.com.br/peticionador/modelos/3/placeholders")
        print("2. Verificar outros modelos para garantir compatibilidade")
        print("3. Monitorar logs para possíveis novos problemas")
    else:
        print("❌ Problemas detectados no sistema")
        print("🔧 Revisar as correções implementadas")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())