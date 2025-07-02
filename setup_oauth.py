#!/usr/bin/env python3
"""
Script para configurar autenticação OAuth com Google Drive
"""
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Escopos necessários
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents'
]

def setup_oauth():
    """Configura autenticação OAuth e salva tokens."""
    creds = None
    
    # Arquivo para salvar tokens
    token_file = 'token.json'
    credentials_file = 'client_secret.json'
    
    # Verifica se já existe token válido
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # Se não há credenciais válidas, inicia fluxo OAuth
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token expirado...")
            creds.refresh(Request())
        else:
            print("🔐 Iniciando fluxo de autenticação OAuth...")
            print("📋 Escopos solicitados:")
            for scope in SCOPES:
                print(f"   - {scope}")
            print()
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            
            # Usar porta específica para callback
            creds = flow.run_local_server(
                port=8080,
                prompt='consent',
                authorization_prompt_message='Abrindo navegador para autenticação...',
                success_message='Autenticação concluída! Pode fechar esta janela.'
            )
        
        # Salva as credenciais para próximas execuções
        with open(token_file, 'w') as token:
            token.write(creds.to_json())
        print(f"✅ Token salvo em: {token_file}")
    
    return creds

def test_access(creds):
    """Testa acesso ao Google Drive e lista arquivos."""
    try:
        # Constroi serviço do Drive
        service = build('drive', 'v3', credentials=creds)
        
        print("\n=== TESTANDO ACESSO AO GOOGLE DRIVE ===")
        
        # Lista arquivos
        results = service.files().list(
            pageSize=10,
            fields="files(id, name, mimeType)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print("❌ Nenhum arquivo encontrado")
            return False
        
        print(f"✅ {len(items)} arquivo(s) encontrado(s):")
        for item in items:
            print(f"   📄 {item['name']} (ID: {item['id']})")
        
        # Testa criação de pasta
        print("\n=== TESTANDO CRIAÇÃO DE PASTA ===")
        folder_metadata = {
            'name': '[TEST-OAUTH] Teste OAuth',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        folder_id = folder.get('id')
        
        print(f"✅ Pasta de teste criada: {folder_id}")
        
        # Remove pasta de teste
        service.files().delete(fileId=folder_id).execute()
        print("✅ Pasta de teste removida")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    print("=== CONFIGURAÇÃO OAUTH GOOGLE DRIVE ===")
    print()
    
    # Verifica se arquivo de credenciais existe
    if not os.path.exists('client_secret.json'):
        print("❌ Arquivo client_secret.json não encontrado!")
        print("   Certifique-se de que o arquivo está na pasta raiz do projeto.")
        return
    
    try:
        # Configura OAuth
        creds = setup_oauth()
        
        # Testa acesso
        if test_access(creds):
            print("\n🎉 CONFIGURAÇÃO OAUTH CONCLUÍDA COM SUCESSO!")
            print()
            print("📁 Arquivos criados:")
            print("   - token.json (tokens de acesso)")
            print("   - client_secret.json (credenciais OAuth)")
            print()
            print("🔄 Próximos passos:")
            print("1. Copie os arquivos para o container Docker")
            print("2. Reinicie a aplicação")
            print("3. Teste o cadastro de cliente")
        else:
            print("\n❌ Erro na configuração. Verifique as permissões.")
            
    except Exception as e:
        print(f"❌ Erro na configuração OAuth: {e}")
        print()
        print("🔧 Possíveis soluções:")
        print("1. Verifique se o Client ID e Secret estão corretos")
        print("2. Certifique-se de que os redirect URIs estão configurados")
        print("3. Verifique se você está na lista de usuários de teste")

if __name__ == '__main__':
    main() 