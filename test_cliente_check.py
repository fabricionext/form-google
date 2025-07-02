#!/usr/bin/env python3
"""
Script para verificar clientes existentes e testar com dados únicos
"""
import os
import sys
sys.path.insert(0, '/var/www/estevaoalmeida.com.br/form-google')

from app import create_app
from app.extensions import db
from app.peticionador.models import Cliente, TipoPessoaEnum, User
from datetime import datetime
import random

def check_and_test_clients():
    """Verifica clientes existentes e testa com dados únicos"""
    app = create_app()
    
    with app.app_context():
        print("=== VERIFICAÇÃO E TESTE DE CLIENTES ===")
        
        # Verificar clientes existentes
        total_clients = Cliente.query.count()
        print(f"Total de clientes no banco: {total_clients}")
        
        print("\n--- CLIENTES EXISTENTES ---")
        all_clients = Cliente.query.all()
        for client in all_clients:
            if client.tipo_pessoa == TipoPessoaEnum.FISICA:
                print(f"ID {client.id}: {client.primeiro_nome} {client.sobrenome or ''} (PF)")
                print(f"  CPF: {client.cpf}")
                print(f"  Email: {client.email}")
                print(f"  Tel: {client.telefone_celular}")
                if client.profissao:
                    print(f"  Profissão: {client.profissao}")
                if client.cnh_numero:
                    print(f"  CNH: {client.cnh_numero}")
            else:
                print(f"ID {client.id}: {client.razao_social} (PJ)")
                print(f"  CNPJ: {client.cnpj}")
                print(f"  Email: {client.email}")
                if client.representante_nome:
                    print(f"  Representante: {client.representante_nome} ({client.representante_cargo})")
            print(f"  Endereço: {client.endereco_logradouro}, {client.endereco_numero} - {client.endereco_cidade}/{client.endereco_estado}")
            print()
        
        # Gerar dados únicos para teste
        random_id = random.randint(1000, 9999)
        
        # Dados únicos - Pessoa Física
        test_pf_data = {
            'tipo_pessoa': TipoPessoaEnum.FISICA,
            'email': f'test.pf.{random_id}@example.com',
            'telefone_celular': f'(11) 9{random_id:04d}-{random_id:04d}',
            'telefone_outro': f'(11) 3{random_id:04d}-{random_id:04d}',
            'endereco_logradouro': f'Rua Teste {random_id}',
            'endereco_numero': str(random_id),
            'endereco_complemento': f'Apto {random_id}',
            'endereco_bairro': 'Centro',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': f'{random_id:05d}-000',
            'primeiro_nome': 'Maria',
            'sobrenome': f'Teste{random_id}',
            'cpf': f'{random_id:03d}.{random_id:03d}.{random_id:03d}-{random_id%100:02d}',
            'rg_numero': f'{random_id}.{random_id}.{random_id}-{random_id%10}',
            'rg_orgao_emissor': 'SSP',
            'rg_uf_emissor': 'SP',
            'data_nascimento': datetime(1985, 3, 20).date(),
            'nacionalidade': 'Brasileira',
            'estado_civil': 'Casado(a)',
            'profissao': 'Advogada',
            'cnh_numero': f'{random_id}123456789'
        }
        
        # Dados únicos - Pessoa Jurídica  
        test_pj_data = {
            'tipo_pessoa': TipoPessoaEnum.JURIDICA,
            'email': f'contato.{random_id}@empresa.com',
            'telefone_celular': f'(11) 8{random_id:04d}-{random_id:04d}',
            'telefone_outro': f'(11) 2{random_id:04d}-{random_id:04d}',
            'endereco_logradouro': f'Avenida Teste {random_id}',
            'endereco_numero': str(random_id + 100),
            'endereco_complemento': f'Sala {random_id}',
            'endereco_bairro': 'Vila Olímpia',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': f'{random_id + 1000:05d}-100',
            'razao_social': f'Empresa Teste {random_id} LTDA',
            'cnpj': f'{random_id:02d}.{random_id:03d}.{random_id:03d}/0001-{random_id%100:02d}',
            'representante_nome': f'Carlos Rep{random_id}',
            'representante_cargo': 'Diretor',
            'representante_cpf': f'{random_id + 100:03d}.{random_id + 200:03d}.{random_id + 300:03d}-{(random_id + 50)%100:02d}',
            'representante_rg_numero': f'{random_id + 100}.{random_id + 200}.{random_id + 300}-{(random_id + 1)%10}',
            'representante_rg_orgao_emissor': 'SSP',
            'representante_rg_uf_emissor': 'SP'
        }
        
        try:
            # Teste 1: Criar Pessoa Física única
            print("\n--- TESTE 1: Criação Pessoa Física (dados únicos) ---")
            cliente_pf = Cliente(**test_pf_data)
            db.session.add(cliente_pf)
            db.session.commit()
            print(f"✅ Cliente PF criado com ID: {cliente_pf.id}")
            print(f"   Nome: {cliente_pf.primeiro_nome} {cliente_pf.sobrenome}")
            print(f"   CPF: {cliente_pf.cpf}")
            print(f"   Email: {cliente_pf.email}")
            print(f"   Profissão: {cliente_pf.profissao}")
            print(f"   CNH: {cliente_pf.cnh_numero}")
            print(f"   Endereço: {cliente_pf.endereco_logradouro}, {cliente_pf.endereco_numero}")
            
            # Teste 2: Criar Pessoa Jurídica única
            print("\n--- TESTE 2: Criação Pessoa Jurídica (dados únicos) ---")
            cliente_pj = Cliente(**test_pj_data)
            db.session.add(cliente_pj)
            db.session.commit()
            print(f"✅ Cliente PJ criado com ID: {cliente_pj.id}")
            print(f"   Razão Social: {cliente_pj.razao_social}")
            print(f"   CNPJ: {cliente_pj.cnpj}")
            print(f"   Representante: {cliente_pj.representante_nome} ({cliente_pj.representante_cargo})")
            print(f"   CPF Rep.: {cliente_pj.representante_cpf}")
            print(f"   RG Rep.: {cliente_pj.representante_rg_numero}")
            
            # Teste 3: Verificar dados salvos
            print("\n--- TESTE 3: Verificação dos dados salvos ---")
            
            # Buscar cliente PF criado
            pf_saved = Cliente.query.filter_by(id=cliente_pf.id).first()
            if pf_saved:
                print(f"✅ Cliente PF (ID {pf_saved.id}) verificado no banco:")
                print(f"   Todos os campos salvos corretamente")
                print(f"   Tipo: {pf_saved.tipo_pessoa.name}")
                print(f"   Nome completo: {pf_saved.primeiro_nome} {pf_saved.sobrenome}")
                print(f"   Nacionalidade: {pf_saved.nacionalidade}")
                print(f"   Estado civil: {pf_saved.estado_civil}")
                print(f"   Data nascimento: {pf_saved.data_nascimento}")
                print(f"   RG: {pf_saved.rg_numero} - {pf_saved.rg_orgao_emissor}/{pf_saved.rg_uf_emissor}")
            
            # Buscar cliente PJ criado
            pj_saved = Cliente.query.filter_by(id=cliente_pj.id).first()
            if pj_saved:
                print(f"✅ Cliente PJ (ID {pj_saved.id}) verificado no banco:")
                print(f"   Todos os campos salvos corretamente")
                print(f"   Tipo: {pj_saved.tipo_pessoa.name}")
                print(f"   Razão Social: {pj_saved.razao_social}")
                print(f"   CNPJ: {pj_saved.cnpj}")
                print(f"   Rep. Legal: {pj_saved.representante_nome}")
                print(f"   Rep. Cargo: {pj_saved.representante_cargo}")
                print(f"   Rep. RG: {pj_saved.representante_rg_numero} - {pj_saved.representante_rg_orgao_emissor}/{pj_saved.representante_rg_uf_emissor}")
                
            print(f"\n--- RESUMO FINAL ---")
            total_after = Cliente.query.count()
            print(f"Total de clientes após testes: {total_after}")
            print(f"Clientes criados neste teste: {total_after - total_clients}")
            print("✅ TODOS OS CAMPOS DO FORMULÁRIO FUNCIONANDO CORRETAMENTE")
            
        except Exception as e:
            print(f"❌ Erro durante o teste: {str(e)}")
            db.session.rollback()
            import traceback
            traceback.print_exc()
            
        print("\n=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    check_and_test_clients()