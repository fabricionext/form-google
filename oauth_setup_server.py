#!/usr/bin/env python3
"""
Script para configurar OAuth no servidor e testar acesso aos templates
"""
import os
import sys
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Adicionar path da aplicação
sys.path.insert(0, '/var/www/estevaoalmeida.com.br/form-google')

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

def test_template_access_with_oauth():
    """Testa acesso ao template usando OAuth se disponível."""
    print("=== TESTE DE ACESSO AO TEMPLATE COM OAUTH ===")
    print()
    
    template_id = '11SLeHknGT1Hy6mUwYgZyhlXJKb1ukcpENfVoF-yNCm8'
    
    # Verificar se tem credenciais OAuth
    credentials_file = '/home/app/client_secret.json' if os.path.exists('/home/app/client_secret.json') else 'client_secret.json'
    token_file = '/home/app/token.json' if os.path.exists('/home/app/token.json') else 'token.json'
    
    if not os.path.exists(credentials_file):
        print(f"❌ Arquivo de credenciais não encontrado: {credentials_file}")
        return False
    
    print(f"✅ Credenciais OAuth encontradas: {credentials_file}")
    
    # Para OAuth funcionar no servidor, precisaríamos de um token pré-autorizado
    # Como não temos isso, vamos mostrar as instruções
    
    print()
    print("📋 INSTRUÇÕES PARA CONFIGURAR OAUTH:")
    print("1. Execute localmente (em sua máquina):")
    print("   python3 setup_oauth.py")
    print()
    print("2. Copie o arquivo token.json gerado para o servidor:")
    print("   docker cp token.json form-google-app:/home/app/")
    print()
    print("3. Reinicie a aplicação:")
    print("   docker restart form-google-app")
    print()
    
    return False

def test_template_sharing_status():
    """Verifica status do compartilhamento do template."""
    print("=== VERIFICAÇÃO DE COMPARTILHAMENTO ===")
    print()
    
    template_id = '11SLeHknGT1Hy6mUwYgZyhlXJKb1ukcpENfVoF-yNCm8'
    service_account_email = 'ubuntu-server@app-script-459322.iam.gserviceaccount.com'
    
    print(f"📄 Template ID: {template_id}")
    print(f"🤖 Service Account: {service_account_email}")
    print()
    
    print("📋 PASSOS PARA COMPARTILHAR O TEMPLATE:")
    print(f"1. Acesse: https://docs.google.com/document/d/{template_id}/edit")
    print("2. Clique em 'Compartilhar' (botão azul no canto superior direito)")
    print("3. No campo 'Adicionar pessoas e grupos', cole:")
    print(f"   {service_account_email}")
    print("4. Selecione permissão: 'Editor'")
    print("5. Clique em 'Enviar'")
    print()
    
    print("⚠️  IMPORTANTE:")
    print("- Certifique-se de usar EXATAMENTE este email")
    print("- Aguarde 2-3 minutos após compartilhar")
    print("- Teste novamente após compartilhar")
    
def create_test_template():
    """Cria um template de teste usando Service Account."""
    print("=== CRIANDO TEMPLATE DE TESTE ===")
    print()
    
    try:
        from app.services.google_service_account import GoogleServiceAccountAuth
        
        google_service = GoogleServiceAccountAuth()
        docs_service = google_service.get_docs_service()
        
        # Criar documento de teste
        document = {
            'title': '[TEMPLATE TEST] PF - Ficha Cadastral'
        }
        
        created_doc = docs_service.documents().create(body=document).execute()
        doc_id = created_doc['documentId']
        
        # Adicionar conteúdo básico
        requests = [
            {
                'insertText': {
                    'location': {'index': 1},
                    'text': '''FICHA CADASTRAL - PESSOA FÍSICA

Nome: {{cliente_nome}}
Email: {{cliente_email}}
CPF: {{cliente_cpf}}
Telefone: {{cliente_telefone}}

Data: {{data_atual}}

Este é um template de teste criado automaticamente.'''
                }
            }
        ]
        
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        print(f"✅ Template de teste criado!")
        print(f"   ID: {doc_id}")
        print(f"   Nome: [TEMPLATE TEST] PF - Ficha Cadastral")
        print(f"   URL: https://docs.google.com/document/d/{doc_id}/edit")
        print()
        print("🔄 Para usar este template:")
        print(f"1. Substitua o ID no código por: {doc_id}")
        print("2. Teste o cadastro de cliente")
        
        return doc_id
        
    except Exception as e:
        print(f"❌ Erro ao criar template de teste: {e}")
        return None

def main():
    print("=== DIAGNÓSTICO DE ACESSO AOS TEMPLATES ===")
    print()
    
    # Teste 1: Verificar OAuth
    test_template_access_with_oauth()
    
    print()
    print("="*50)
    print()
    
    # Teste 2: Instruções de compartilhamento
    test_template_sharing_status()
    
    print()
    print("="*50)
    print()
    
    # Teste 3: Criar template de teste
    test_template_id = create_test_template()
    
    if test_template_id:
        print()
        print("🎯 PRÓXIMO PASSO:")
        print("Execute este comando para testar o novo template:")
        print(f"curl -X POST https://appform.estevaoalmeida.com.br/api/public/clientes \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d '{")
        print('    "tipo_pessoa": "FISICA",')
        print('    "primeiro_nome": "Teste",')
        print('    "sobrenome": "Template",')
        print('    "email": "teste@template.com",')
        print('    "cpf": "123.456.789-01",')
        print('    "telefone_celular": "(11) 99999-9999",')
        print('    "documentos_gerar": ["FICHA_CADASTRAL"]')
        print("  }'")

if __name__ == '__main__':
    main() 