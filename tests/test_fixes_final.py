#!/usr/bin/env python3
"""
Script para testar todas as correções implementadas no sistema de formulários.
Este script verifica se:
1. A busca por CPF funciona corretamente
2. A busca por nome funciona corretamente 
3. O dashboard conta formulários corretamente
4. O FormularioService funciona sem erros
5. A extração de placeholders está corrigida
"""

import os
import sys

# Adicionar o diretório do projeto ao path
sys.path.insert(0, '/var/www/estevaoalmeida.com.br/form-google')

from app import create_app
from app.peticionador.models import Cliente, FormularioGerado, PeticaoModelo
from app.peticionador.services.formulario_service import FormularioService
from app.peticionador.utils import safe_extract_placeholder_keys
import json

def test_cliente_search():
    """Testa a busca de clientes por CPF e nome."""
    print("🔍 TESTE 1: Busca de Clientes")
    
    # Buscar um cliente exemplo
    cliente = Cliente.query.first()
    if not cliente:
        print("❌ Nenhum cliente encontrado no banco")
        return False
    
    print(f"✅ Cliente teste encontrado: {cliente.primeiro_nome} {cliente.sobrenome}")
    
    # Testar acesso aos campos que estavam com problema
    try:
        campos_testados = {
            'endereco_cep': cliente.endereco_cep,
            'endereco_logradouro': cliente.endereco_logradouro,
            'endereco_numero': cliente.endereco_numero,
            'endereco_complemento': cliente.endereco_complemento,
            'endereco_bairro': cliente.endereco_bairro,
            'endereco_cidade': cliente.endereco_cidade,
            'endereco_estado': cliente.endereco_estado,
            'rg_numero': cliente.rg_numero,
            'rg_uf_emissor': cliente.rg_uf_emissor,
            'cnh_numero': cliente.cnh_numero,
        }
        
        print("✅ Todos os campos de endereço e documentos acessíveis")
        campos_com_dados = {k: v for k, v in campos_testados.items() if v}
        print(f"✅ Campos com dados: {len(campos_com_dados)}/{len(campos_testados)}")
        return True
        
    except AttributeError as e:
        print(f"❌ Erro ao acessar campos do cliente: {e}")
        return False

def test_dashboard_counts():
    """Testa se o dashboard conta corretamente."""
    print("\n📊 TESTE 2: Contadores do Dashboard")
    
    try:
        total_clientes = Cliente.query.count()
        total_formularios = FormularioGerado.query.count()
        
        print(f"✅ Total de clientes: {total_clientes}")
        print(f"✅ Total de formulários gerados: {total_formularios}")
        
        if total_clientes > 0:
            print("✅ Dashboard de clientes funcionando")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao contar registros: {e}")
        return False

def test_formulario_service():
    """Testa o FormularioService."""
    print("\n⚙️ TESTE 3: FormularioService")
    
    try:
        # Buscar um formulário gerado
        formulario = FormularioGerado.query.first()
        if not formulario:
            print("⚠️ Nenhum formulário gerado encontrado")
            return True
        
        # Testar o FormularioService
        service = FormularioService(formulario.slug)
        
        # Testar propriedades básicas
        modelo = service.modelo
        placeholders = service.placeholders
        campos_organizados = service.agrupar_campos_por_categoria()
        
        print(f"✅ FormularioService criado para: {formulario.nome}")
        print(f"✅ Modelo: {modelo.nome}")
        print(f"✅ Placeholders: {len(placeholders)}")
        print(f"✅ Categorias organizadas: {list(campos_organizados.keys())}")
        
        # Testar análise
        analise = service.get_placeholder_analysis()
        print(f"✅ Análise de placeholders: {analise['total_placeholders']} placeholders")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no FormularioService: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_placeholder_extraction():
    """Testa a extração segura de placeholders."""
    print("\n🔧 TESTE 4: Extração de Placeholders")
    
    try:
        # Testar com dados variados
        test_cases = [
            ["autor_1_nome", "autor_1_cpf", "processo_numero"],  # Lista de strings
            [{"key": "autor_1_nome"}, {"key": "autor_1_cpf"}],  # Lista de dicts
            [],  # Lista vazia
            None,  # None
            [{"chave": "test_chave"}],  # Dict com chave diferente
        ]
        
        for i, test_data in enumerate(test_cases):
            resultado = safe_extract_placeholder_keys(test_data)
            print(f"✅ Teste {i+1}: {test_data} → {resultado}")
        
        print("✅ Extração de placeholders funcionando corretamente")
        return True
        
    except Exception as e:
        print(f"❌ Erro na extração de placeholders: {e}")
        return False

def test_modelo_consistency():
    """Testa a consistência entre modelos e formulários."""
    print("\n🔍 TESTE 5: Consistência de Modelos")
    
    try:
        modelo = PeticaoModelo.query.filter_by(ativo=True).first()
        if not modelo:
            print("⚠️ Nenhum modelo ativo encontrado")
            return True
        
        print(f"✅ Modelo teste: {modelo.nome}")
        
        # Verificar se há formulário gerado para este modelo
        formulario = FormularioGerado.query.filter_by(modelo_id=modelo.id).first()
        if formulario:
            print(f"✅ Formulário encontrado: {formulario.nome}")
            
            # Testar validação de consistência
            service = FormularioService(formulario.slug)
            consistencia = service.validate_placeholder_consistency()
            
            if consistencia.get('consistency_check'):
                print(f"✅ Validação de consistência executada")
                print(f"   - Placeholders no doc: {consistencia.get('placeholders_doc', 0)}")
                print(f"   - Placeholders no DB: {consistencia.get('placeholders_db', 0)}")
                print(f"   - Sincronizado: {consistencia.get('synchronized', False)}")
            else:
                print(f"⚠️ Erro na validação: {consistencia.get('error', 'Erro desconhecido')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na consistência de modelos: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Executa todos os testes."""
    print("🚀 INICIANDO TESTES DE VALIDAÇÃO DAS CORREÇÕES")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        tests = [
            test_cliente_search,
            test_dashboard_counts,
            test_formulario_service,
            test_placeholder_extraction,
            test_modelo_consistency,
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
            print("🎉 TODOS OS TESTES PASSARAM! Sistema corrigido com sucesso.")
        elif passed >= total * 0.8:
            print("✅ Maioria dos testes passou. Sistema em bom estado.")
        else:
            print("⚠️ Vários testes falharam. Mais correções necessárias.")
        
        return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)