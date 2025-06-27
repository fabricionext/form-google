#!/usr/bin/env python3
"""
Script simplificado para testar as correções básicas implementadas.
"""

import os
import sys

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/var/www/estevaoalmeida.com.br/form-google')

def test_imports():
    """Testa se os imports básicos funcionam."""
    print("🔍 TESTE 1: Imports Básicos")
    
    try:
        from app.peticionador.models import Cliente, FormularioGerado, PeticaoModelo
        print("✅ Models importados com sucesso")
        
        from app.peticionador.utils import safe_extract_placeholder_keys
        print("✅ Utils importados com sucesso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nos imports: {e}")
        return False

def test_placeholder_extraction():
    """Testa a extração segura de placeholders."""
    print("\n🔧 TESTE 2: Extração de Placeholders")
    
    try:
        from app.peticionador.utils import safe_extract_placeholder_keys
        
        # Testar com dados variados
        test_cases = [
            (["autor_1_nome", "autor_1_cpf", "processo_numero"], 3),
            ([{"key": "autor_1_nome"}, {"key": "autor_1_cpf"}], 2),
            ([], 0),
            (None, 0),
            ([{"chave": "test_chave"}], 1),
        ]
        
        all_passed = True
        for i, (test_data, expected_count) in enumerate(test_cases):
            resultado = safe_extract_placeholder_keys(test_data)
            if len(resultado) == expected_count:
                print(f"✅ Teste {i+1}: PASSOU - {len(resultado)} placeholders extraídos")
            else:
                print(f"❌ Teste {i+1}: FALHOU - Esperado {expected_count}, obtido {len(resultado)}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Erro na extração de placeholders: {e}")
        return False

def test_client_field_mappings():
    """Testa se os campos do cliente estão corretos."""
    print("\n👤 TESTE 3: Campos do Cliente")
    
    try:
        # Simular a lógica da API de busca CPF
        from app.peticionador.models import Cliente
        
        # Campos que estavam com problema na API
        required_fields = [
            'endereco_cep', 'endereco_logradouro', 'endereco_numero',
            'endereco_complemento', 'endereco_bairro', 'endereco_cidade',
            'endereco_estado', 'rg_numero', 'rg_uf_emissor', 'cnh_numero'
        ]
        
        # Verificar se o modelo Cliente tem esses campos
        all_fields_exist = True
        for field in required_fields:
            if hasattr(Cliente, field):
                print(f"✅ Campo {field}: Presente")
            else:
                print(f"❌ Campo {field}: AUSENTE")
                all_fields_exist = False
        
        return all_fields_exist
        
    except Exception as e:
        print(f"❌ Erro ao verificar campos do cliente: {e}")
        return False

def test_formulario_service_import():
    """Testa se o FormularioService pode ser importado."""
    print("\n⚙️ TESTE 4: FormularioService")
    
    try:
        from app.peticionador.services.formulario_service import FormularioService
        print("✅ FormularioService importado com sucesso")
        
        # Verificar se os métodos principais existem
        methods_to_check = [
            'agrupar_campos_por_categoria',
            'get_placeholder_analysis',
            'validate_placeholder_consistency'
        ]
        
        all_methods_exist = True
        for method in methods_to_check:
            if hasattr(FormularioService, method):
                print(f"✅ Método {method}: Presente")
            else:
                print(f"❌ Método {method}: AUSENTE")
                all_methods_exist = False
        
        return all_methods_exist
        
    except Exception as e:
        print(f"❌ Erro ao importar FormularioService: {e}")
        return False

def test_utils_functions():
    """Testa as funções de utils."""
    print("\n🛠️ TESTE 5: Funções Utils")
    
    try:
        from app.peticionador.utils import (
            normalize_placeholders_list,
            safe_extract_placeholder_keys,
            validate_placeholder_format,
            clean_placeholder_key,
            get_enum_display_name
        )
        
        print("✅ Todas as funções utils importadas")
        
        # Testar função de validação
        assert validate_placeholder_format("autor_1_nome") == True
        assert validate_placeholder_format("campo!@#") == False
        print("✅ validate_placeholder_format funcionando")
        
        # Testar função de limpeza
        cleaned = clean_placeholder_key("campo!@# inválido")
        assert "_" in cleaned and "!" not in cleaned
        print("✅ clean_placeholder_key funcionando")
        
        # Testar enum display
        result = get_enum_display_name(None)
        assert result == ""
        print("✅ get_enum_display_name funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro nas funções utils: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🚀 INICIANDO TESTES SIMPLIFICADOS DAS CORREÇÕES")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_placeholder_extraction,
        test_client_field_mappings,
        test_formulario_service_import,
        test_utils_functions,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Teste falhou com exceção: {e}")
    
    print("\n" + "=" * 50)
    print(f"📋 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM! Correções implementadas corretamente.")
    elif passed >= total * 0.8:
        print("✅ Maioria dos testes passou. Sistema em bom estado.")
    else:
        print("⚠️ Vários testes falharam. Mais correções necessárias.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)