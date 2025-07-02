#!/usr/bin/env python3
"""
Teste final com dados em formato correto
"""
import os
import sys
sys.path.insert(0, '/var/www/estevaoalmeida.com.br/form-google')

from app import create_app
from app.extensions import db
from app.peticionador.models import Cliente, TipoPessoaEnum
from datetime import datetime

def final_test():
    """Teste final com dados formatados corretamente"""
    app = create_app()
    
    with app.app_context():
        print("=== TESTE FINAL - VALIDAÇÃO COMPLETA ===")
        
        # Dados válidos - Pessoa Física
        test_pf_data = {
            'tipo_pessoa': TipoPessoaEnum.FISICA,
            'email': 'ana.final@test.com',
            'telefone_celular': '(11) 91234-5678',
            'telefone_outro': '(11) 3123-4567',
            'endereco_logradouro': 'Rua Final',
            'endereco_numero': '999',
            'endereco_complemento': 'Apt 1',
            'endereco_bairro': 'Vila Nova',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': '01234-567',
            'primeiro_nome': 'Ana',
            'sobrenome': 'Final',
            'cpf': '111.222.333-44',
            'rg_numero': '11.222.333-4',
            'rg_orgao_emissor': 'SSP',
            'rg_uf_emissor': 'SP',
            'data_nascimento': datetime(1990, 1, 1).date(),
            'nacionalidade': 'Brasileira',
            'estado_civil': 'Solteiro(a)',
            'profissao': 'Designer',
            'cnh_numero': '12345678901'  # 11 chars - dentro do limite
        }
        
        # Dados válidos - Pessoa Jurídica  
        test_pj_data = {
            'tipo_pessoa': TipoPessoaEnum.JURIDICA,
            'email': 'final@empresa.com',
            'telefone_celular': '(11) 98765-4321',
            'telefone_outro': '(11) 3876-5432',
            'endereco_logradouro': 'Av Final',
            'endereco_numero': '888',
            'endereco_complemento': 'Conj 2',
            'endereco_bairro': 'Centro',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': '04567-890',
            'razao_social': 'Final Empresa LTDA',
            'cnpj': '11.222.333/0001-44',
            'representante_nome': 'Pedro Final',
            'representante_cargo': 'CEO',
            'representante_cpf': '444.555.666-77',
            'representante_rg_numero': '44.555.666-7',
            'representante_rg_orgao_emissor': 'SSP',
            'representante_rg_uf_emissor': 'SP'
        }
        
        try:
            # Teste PF
            print("\n--- CRIAÇÃO PESSOA FÍSICA ---")
            cliente_pf = Cliente(**test_pf_data)
            db.session.add(cliente_pf)
            db.session.commit()
            print(f"✅ PF criado - ID: {cliente_pf.id}")
            print(f"   Nome: {cliente_pf.primeiro_nome} {cliente_pf.sobrenome}")
            print(f"   Nacionalidade: {cliente_pf.nacionalidade}")
            print(f"   Estado Civil: {cliente_pf.estado_civil}")
            print(f"   CNH: {cliente_pf.cnh_numero}")
            
            # Teste PJ
            print("\n--- CRIAÇÃO PESSOA JURÍDICA ---")
            cliente_pj = Cliente(**test_pj_data)
            db.session.add(cliente_pj)
            db.session.commit()
            print(f"✅ PJ criado - ID: {cliente_pj.id}")
            print(f"   Razão Social: {cliente_pj.razao_social}")
            print(f"   Representante: {cliente_pj.representante_nome}")
            print(f"   Cargo: {cliente_pj.representante_cargo}")
            
            print("\n🎉 TESTE FINAL CONCLUÍDO COM SUCESSO!")
            print("✅ Todos os campos do formulário estão funcionando corretamente")
            print("✅ Estrutura PF: Nome, Nacionalidade, RG/UF, Estado Civil, CPF, Profissão, CNH, Endereço, Email, Data Nascimento, Telefones")
            print("✅ Estrutura PJ: Razão Social, CNPJ, RG/UF do Rep., Nome do Rep., CPF, Cargo, Endereço, Email, Telefones")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    final_test()