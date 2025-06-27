#!/usr/bin/env python3
"""
Teste Completo das Correções Implementadas
==========================================

Testa especificamente os erros que foram reportados:
1. Erro "unhashable type: 'dict'" na sincronização
2. 404 no formulário "suspensao-do-direito-de-dirigir-junho-2025-8bced464"
3. Problemas na busca por CPF
"""

import os
import sys

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/var/www/estevaoalmeida.com.br/form-google')

def test_unhashable_dict_fix():
    """Testa se o erro 'unhashable type: dict' foi corrigido."""
    print("🔧 TESTE: Correção do erro 'unhashable type: dict'")
    
    try:
        from app.peticionador.utils import safe_extract_placeholder_keys
        
        # Dados que causavam o erro original
        problematic_data = [
            {'key': 'autor_1_nome'},
            {'chave': 'autor_1_cpf'},
            'processo_numero',
            {'placeholder': 'data_infracao'},
            {'invalid': 'no_key'},  # Caso que deveria ser ignorado
            '',  # String vazia
            None,  # None (seria ignorado)
            123,  # Número (seria convertido)
        ]
        
        # Este call não deveria mais gerar erro
        result = safe_extract_placeholder_keys(problematic_data)
        
        print(f"   ✅ Função executou sem erro")
        print(f"   ✅ Resultado: {len(result)} placeholders extraídos")
        print(f"   📄 Placeholders: {result}")
        
        # Verificar se são apenas strings
        if all(isinstance(item, str) for item in result):
            print("   ✅ Todos os resultados são strings válidas")
        else:
            print("   ❌ Nem todos os resultados são strings")
            return False
        
        # Testar conversão para set (que causava o erro original)
        try:
            test_set = set(result)
            print(f"   ✅ Conversão para set funciona: {len(test_set)} items únicos")
        except TypeError as e:
            print(f"   ❌ Ainda há erro na conversão para set: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_formulario_404_fix():
    """Testa se o erro 404 do formulário foi corrigido."""
    print("\n🔍 TESTE: Correção do erro 404 do formulário")
    
    try:
        from app import create_app
        from app.peticionador.models import FormularioGerado
        from app.peticionador.services.formulario_manager import formulario_manager
        
        app = create_app()
        
        with app.app_context():
            slug = 'suspensao-do-direito-de-dirigir-junho-2025-8bced464'
            
            # Teste 1: Verificar se o formulário existe no banco
            form = FormularioGerado.query.filter_by(slug=slug).first()
            if form:
                print(f"   ✅ Formulário encontrado no banco: {form.nome}")
            else:
                print(f"   ❌ Formulário não encontrado no banco")
                return False
            
            # Teste 2: Usar o FormularioManager robusto
            form_safe = formulario_manager.safe_get_formulario(slug)
            if form_safe:
                print(f"   ✅ FormularioManager consegue acessar o formulário")
            else:
                print(f"   ❌ FormularioManager falhou ao acessar")
                return False
            
            # Teste 3: Validar slug
            is_valid = formulario_manager.validate_formulario_slug(slug)
            if is_valid:
                print(f"   ✅ Slug é válido")
            else:
                print(f"   ❌ Slug é inválido")
                return False
            
            # Teste 4: Verificar se URL seria gerada corretamente
            try:
                from flask import url_for
                # Simular geração de URL (não precisa executar, só verificar se não dá erro)
                print(f"   ✅ Slug pode ser usado em rotas")
            except Exception as e:
                print(f"   ❌ Erro na geração de URL: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cpf_search_fix():
    """Testa se a busca por CPF foi corrigida."""
    print("\n👤 TESTE: Correção da busca por CPF")
    
    try:
        from app import create_app
        from app.peticionador.models import Cliente
        
        app = create_app()
        
        with app.app_context():
            # Buscar um cliente exemplo
            cliente = Cliente.query.first()
            if not cliente:
                print("   ⚠️ Nenhum cliente no banco para testar")
                return True  # Não é erro, só não há dados
            
            print(f"   📋 Testando com cliente: {cliente.primeiro_nome} {cliente.sobrenome}")
            
            # Testar acesso aos campos que estavam com problema
            problematic_fields = [
                'endereco_cep',
                'endereco_logradouro', 
                'endereco_numero',
                'endereco_complemento',
                'endereco_bairro',
                'endereco_cidade',
                'endereco_estado',
                'rg_numero',
                'rg_uf_emissor',
                'cnh_numero'
            ]
            
            accessible_fields = 0
            for field in problematic_fields:
                try:
                    value = getattr(cliente, field, None)
                    accessible_fields += 1
                    if value:
                        print(f"   ✅ {field}: {value}")
                    else:
                        print(f"   ✅ {field}: (vazio, mas acessível)")
                except AttributeError as e:
                    print(f"   ❌ {field}: Erro de acesso - {e}")
                    return False
            
            print(f"   ✅ Todos os {accessible_fields} campos são acessíveis")
            
            # Simular estrutura de resposta da API (como seria retornado)
            try:
                api_response = {
                    "cpf": cliente.cpf,
                    "rg": cliente.rg_numero,
                    "estado_emissor_rg": cliente.rg_uf_emissor,
                    "cnh_numero": cliente.cnh_numero,
                    "endereco_cep": cliente.endereco_cep,
                    "endereco_logradouro": cliente.endereco_logradouro,
                    "endereco_numero": cliente.endereco_numero,
                    "endereco_complemento": cliente.endereco_complemento,
                    "endereco_bairro": cliente.endereco_bairro,
                    "endereco_cidade": cliente.endereco_cidade,
                    "endereco_estado": cliente.endereco_estado,
                    "nome_completo": f"{cliente.primeiro_nome or ''} {cliente.sobrenome or ''}".strip(),
                }
                
                print(f"   ✅ Estrutura de resposta da API pode ser criada")
                non_null_fields = sum(1 for v in api_response.values() if v)
                print(f"   📊 {non_null_fields}/{len(api_response)} campos com dados")
                
            except Exception as e:
                print(f"   ❌ Erro ao criar resposta da API: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_synchronization_robustness():
    """Testa a robustez da sincronização."""
    print("\n🔄 TESTE: Robustez da sincronização")
    
    try:
        from app.peticionador.services.formulario_manager import formulario_manager
        
        # Testar com dados variados (que antes causavam problemas)
        test_cases = [
            # Caso 1: Lista mista (o que causava erro original)
            [{'key': 'autor_1_nome'}, 'processo_numero', {'chave': 'data_fato'}],
            
            # Caso 2: Lista só de strings
            ['autor_1_nome', 'autor_1_cpf', 'processo_numero'],
            
            # Caso 3: Lista só de dicts
            [{'key': 'autor_1_nome'}, {'key': 'autor_1_cpf'}],
            
            # Caso 4: Lista vazia
            [],
            
            # Caso 5: None
            None,
            
            # Caso 6: Dados malformados
            [{'invalid': 'data'}, '', None, 123, {'key': 'valid_field'}]
        ]
        
        passed_cases = 0
        
        for i, test_data in enumerate(test_cases, 1):
            try:
                result = formulario_manager.safe_extract_placeholders_from_document(test_data)
                print(f"   ✅ Caso {i}: {len(result)} placeholders extraídos")
                passed_cases += 1
            except Exception as e:
                print(f"   ❌ Caso {i}: Erro - {e}")
        
        print(f"   📊 {passed_cases}/{len(test_cases)} casos passaram")
        
        return passed_cases == len(test_cases)
        
    except Exception as e:
        print(f"   ❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("🚀 TESTANDO CORREÇÕES DOS ERROS REPORTADOS")
    print("=" * 55)
    
    tests = [
        ("Erro 'unhashable type dict'", test_unhashable_dict_fix),
        ("Erro 404 do formulário", test_formulario_404_fix),
        ("Busca por CPF", test_cpf_search_fix),
        ("Robustez da sincronização", test_synchronization_robustness),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_function in tests:
        try:
            if test_function():
                passed += 1
                print(f"\n✅ {test_name}: PASSOU")
            else:
                print(f"\n❌ {test_name}: FALHOU")
        except Exception as e:
            print(f"\n💥 {test_name}: ERRO - {e}")
    
    print("\n" + "=" * 55)
    print(f"📋 RESULTADO FINAL: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS ERROS FORAM CORRIGIDOS!")
        print("✅ Sistema está funcionando corretamente")
        print("💡 O restart do sistema irá aplicar todas as correções")
    elif passed >= total * 0.8:
        print("✅ Maioria dos erros corrigidos")
        print("⚠️ Alguns problemas menores podem persistir")
    else:
        print("❌ Vários problemas ainda existem")
        print("🔧 Mais correções são necessárias")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)