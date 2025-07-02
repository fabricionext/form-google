#!/usr/bin/env python3
"""
Debug script para testar criação de cliente e documentos via formulário público
"""
import os
import sys
import json

# Set environment
os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'] = '/var/www/estevaoalmeida.com.br/form-google/app-script-459322-990ad4e6c8ea.json'

sys.path.append('.')

from app.adapters.enhanced_google_drive import EnhancedGoogleDriveAdapter
from app.services.document_generation_service import DocumentGenerationService

def test_client_folder_creation():
    """Testa criação de pasta de cliente"""
    print("=== Teste de Criação de Pasta de Cliente ===")
    
    try:
        adapter = EnhancedGoogleDriveAdapter()
        
        # Teste 1: Criar pasta de cliente
        client_name = "João Teste Santos"
        client_cpf = "12345678901"
        
        print(f"🔨 Criando pasta para cliente: {client_name}")
        folder_id = adapter.organize_by_client(client_name, client_cpf)
        print(f"✅ Pasta criada com ID: {folder_id}")
        
        # Verificar se a pasta foi criada
        folder_info = adapter.service.files().get(fileId=folder_id, fields='name,parents').execute()
        print(f"📁 Nome da pasta: {folder_info['name']}")
        print(f"📂 Pasta pai: {folder_info.get('parents', [])}")
        
        return folder_id
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_document_generation():
    """Testa geração de documentos"""
    print("\n=== Teste de Geração de Documentos ===")
    
    try:
        doc_service = DocumentGenerationService()
        
        # Dados de teste
        cliente_data = {
            'tipo_pessoa': 'FISICA',
            'primeiro_nome': 'João',
            'sobrenome': 'Teste Santos',
            'cpf': '123.456.789-01',
            'email': 'joao.teste@example.com',
            'telefone_celular': '(11) 99999-9999',
            'endereco_logradouro': 'Rua de Teste',
            'endereco_numero': '123',
            'endereco_bairro': 'Centro',
            'endereco_cidade': 'São Paulo',
            'endereco_estado': 'SP',
            'endereco_cep': '01000-000'
        }
        
        # Teste geração de ficha cadastral
        document_type = 'FICHA_CADASTRAL'
        print(f"📄 Gerando documento: {document_type}")
        
        result = doc_service.generate_document(cliente_data, document_type)
        
        if result['success']:
            print(f"✅ Documento gerado com sucesso!")
            print(f"   - ID: {result['document_id']}")
            print(f"   - Nome: {result['document_name']}")
            print(f"   - Pasta do cliente: {result['client_folder_id']}")
            print(f"   - URL: https://docs.google.com/document/d/{result['document_id']}/edit")
        else:
            print(f"❌ Erro na geração: {result['error']}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoint():
    """Simula uma chamada para o endpoint de criação de cliente"""
    print("\n=== Teste do Endpoint API ===")
    
    try:
        from app import create_app
        
        app = create_app()
        
        with app.test_client() as client:
            # Dados para teste
            data = {
                'primeiro_nome': 'Maria',
                'sobrenome': 'Silva Teste',
                'email': 'maria.silva@test.com',
                'cpf': '987.654.321-00',
                'telefone_celular': '(11) 88888-8888',
                'tipo_pessoa': 'FISICA',
                'endereco_logradouro': 'Av. Teste',
                'endereco_numero': '456',
                'endereco_bairro': 'Vila Teste',
                'endereco_cidade': 'São Paulo',
                'endereco_estado': 'SP',
                'endereco_cep': '02000-000',
                'documentos_gerar': ['FICHA_CADASTRAL']
            }
            
            print(f"📡 Enviando requisição para /api/public/clientes")
            response = client.post('/api/public/clientes', 
                                 json=data,
                                 content_type='application/json')
                                 
            print(f"🔍 Status: {response.status_code}")
            
            if response.status_code == 201:
                result = response.get_json()
                print(f"✅ Cliente criado com sucesso!")
                print(f"   - ID: {result['cliente']['id']}")
                print(f"   - Email: {result['cliente']['email']}")
                print(f"   - Documentos gerados: {len(result['documentos'])}")
                
                for doc in result['documentos']:
                    if doc['status'] == 'success':
                        print(f"   - ✅ {doc['type']}: {doc['view_url']}")
                    else:
                        print(f"   - ❌ {doc['type']}: {doc['error']}")
            else:
                print(f"❌ Erro: {response.get_json()}")
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Iniciando testes de integração Google Drive...")
    
    # Testar criação de pasta
    folder_id = test_client_folder_creation()
    
    # Testar geração de documentos
    if folder_id:
        test_document_generation()
    
    # Testar endpoint completo
    test_api_endpoint()
    
    print("\n✅ Testes concluídos!")