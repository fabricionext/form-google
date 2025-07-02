#!/usr/bin/env python3
"""
Test script para verificar funcionalidade do formulário de cliente
"""
import os
import sys
sys.path.insert(0, '/var/www/estevaoalmeida.com.br/form-google')

from app import create_app
from app.extensions import db
from app.peticionador.models import Cliente, TipoPessoaEnum, User
from datetime import datetime

def test_client_creation():
    """Testa criação de clientes PF e PJ"""
    app = create_app()
    
    with app.app_context():
        print("=== TESTE FORMULÁRIO CLIENTE ===")
        
        # Verificar clientes existentes
        total_clients = Cliente.query.count()
        print(f"Total de clientes no banco: {total_clients}")
        
        # Dados de teste - Pessoa Física
        test_pf_data = {
            'tipo_pessoa': TipoPessoaEnum.FISICA,
            'email': 'test.pf@example.com',
            'telefone_celular': '(11) 99999-9999',
            'telefone_outro': '(11) 3333-3333',
            'endereco_logradouro': 'Rua das Flores',
            'endereco_numero': '123',
            'endereco_complemento': 'Apto 45',
            'endereco_bairro': 'Centro',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': '01234-567',
            'primeiro_nome': 'João',
            'sobrenome': 'Silva',
            'cpf': '123.456.789-00',
            'rg_numero': '12.345.678-9',
            'rg_orgao_emissor': 'SSP',
            'rg_uf_emissor': 'SP',
            'data_nascimento': datetime(1990, 5, 15).date(),
            'nacionalidade': 'Brasileira',
            'estado_civil': 'Solteiro(a)',
            'profissao': 'Engenheiro',
            'cnh_numero': '12345678901'
        }
        
        # Dados de teste - Pessoa Jurídica
        test_pj_data = {
            'tipo_pessoa': TipoPessoaEnum.JURIDICA,
            'email': 'contato@empresa.com',
            'telefone_celular': '(11) 88888-8888',
            'telefone_outro': '(11) 2222-2222',
            'endereco_logradouro': 'Avenida Paulista',
            'endereco_numero': '1000',
            'endereco_complemento': 'Sala 100',
            'endereco_bairro': 'Bela Vista',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': '01310-100',
            'razao_social': 'Empresa Teste LTDA',
            'cnpj': '12.345.678/0001-99',
            'representante_nome': 'Maria Santos',
            'representante_cargo': 'Diretora',
            'representante_cpf': '987.654.321-00',
            'representante_rg_numero': '98.765.432-1',
            'representante_rg_orgao_emissor': 'SSP',
            'representante_rg_uf_emissor': 'SP'
        }
        
        try:
            # Teste 1: Criar Pessoa Física
            print("\n--- TESTE 1: Criação Pessoa Física ---")
            cliente_pf = Cliente(**test_pf_data)
            db.session.add(cliente_pf)
            db.session.commit()
            print(f"✅ Cliente PF criado com ID: {cliente_pf.id}")
            print(f"   Nome: {cliente_pf.primeiro_nome} {cliente_pf.sobrenome}")
            print(f"   CPF: {cliente_pf.cpf}")
            print(f"   Email: {cliente_pf.email}")
            
            # Teste 2: Criar Pessoa Jurídica
            print("\n--- TESTE 2: Criação Pessoa Jurídica ---")
            cliente_pj = Cliente(**test_pj_data)
            db.session.add(cliente_pj)
            db.session.commit()
            print(f"✅ Cliente PJ criado com ID: {cliente_pj.id}")
            print(f"   Razão Social: {cliente_pj.razao_social}")
            print(f"   CNPJ: {cliente_pj.cnpj}")
            print(f"   Representante: {cliente_pj.representante_nome}")
            
            # Teste 3: Verificar dados salvos
            print("\n--- TESTE 3: Verificação dos dados salvos ---")
            
            # Buscar cliente PF
            pf_saved = Cliente.query.filter_by(email='test.pf@example.com').first()
            if pf_saved:
                print(f"✅ Cliente PF encontrado no banco:")
                print(f"   ID: {pf_saved.id}")
                print(f"   Nome completo: {pf_saved.primeiro_nome} {pf_saved.sobrenome}")
                print(f"   Endereço: {pf_saved.endereco_logradouro}, {pf_saved.endereco_numero}")
                print(f"   Telefones: {pf_saved.telefone_celular} / {pf_saved.telefone_outro}")
                print(f"   Profissão: {pf_saved.profissao}")
                print(f"   CNH: {pf_saved.cnh_numero}")
            else:
                print("❌ Cliente PF não encontrado")
            
            # Buscar cliente PJ
            pj_saved = Cliente.query.filter_by(email='contato@empresa.com').first()
            if pj_saved:
                print(f"✅ Cliente PJ encontrado no banco:")
                print(f"   ID: {pj_saved.id}")
                print(f"   Razão Social: {pj_saved.razao_social}")
                print(f"   CNPJ: {pj_saved.cnpj}")
                print(f"   Representante: {pj_saved.representante_nome} ({pj_saved.representante_cargo})")
                print(f"   CPF Rep.: {pj_saved.representante_cpf}")
                print(f"   RG Rep.: {pj_saved.representante_rg_numero} - {pj_saved.representante_rg_orgao_emissor}/{pj_saved.representante_rg_uf_emissor}")
            else:
                print("❌ Cliente PJ não encontrado")
                
            print(f"\n--- RESUMO ---")
            total_after = Cliente.query.count()
            print(f"Total de clientes após testes: {total_after}")
            print(f"Clientes criados neste teste: {total_after - total_clients}")
            
            # Listar todos os clientes
            print("\n--- LISTA DE TODOS OS CLIENTES ---")
            all_clients = Cliente.query.all()
            for client in all_clients:
                name = client.primeiro_nome if client.tipo_pessoa == TipoPessoaEnum.FISICA else client.razao_social
                tipo = "PF" if client.tipo_pessoa == TipoPessoaEnum.FISICA else "PJ"
                print(f"  ID {client.id}: {name} ({tipo}) - {client.email}")
                
        except Exception as e:
            print(f"❌ Erro durante o teste: {str(e)}")
            db.session.rollback()
            raise
            
        print("\n=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    test_client_creation()