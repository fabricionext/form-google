#!/usr/bin/env python3
"""
Teste de autenticação Google Drive
"""
import os
import sys

# Adicionar o diretório da aplicação ao path
sys.path.append('/home/app')

from app.adapters.enhanced_google_drive import EnhancedGoogleDriveAdapter

def test_auth():
    print("=== Teste de Autenticação Google Drive ===")
    
    # Verificar variável de ambiente
    service_account_path = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    print(f"Service Account Path: {service_account_path}")
    
    if service_account_path and os.path.exists(service_account_path):
        print(f"✅ Arquivo encontrado: {service_account_path}")
    else:
        print(f"❌ Arquivo não encontrado: {service_account_path}")
        return
    
    try:
        # Testar autenticação
        adapter = EnhancedGoogleDriveAdapter()
        print("✅ Adapter criado com sucesso")
        
        # Testar acesso à pasta raiz
        root_folder = "1yH19w1RMjmxEghpZQj5HpYb9LxmJ0gz-"
        print(f"Testando acesso à pasta: {root_folder}")
        
        if adapter.service:
            result = adapter.service.files().get(fileId=root_folder).execute()
            print(f"✅ Pasta acessível: {result.get('name', 'N/A')}")
        else:
            print("❌ Service não inicializado")
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")

if __name__ == "__main__":
    test_auth()