#!/usr/bin/env python3
"""
Teste detalhado de acesso ao Google Drive
"""
import os
import sys

# Adicionar o diretório da aplicação ao path
sys.path.append('/home/app')

from app.adapters.enhanced_google_drive import EnhancedGoogleDriveAdapter

def test_detailed():
    print("=== Teste Detalhado Google Drive ===")
    
    try:
        adapter = EnhancedGoogleDriveAdapter()
        print("✅ Adapter criado com sucesso")
        
        if not adapter.service:
            print("❌ Service não inicializado")
            return
            
        print("✅ Service inicializado")
        
        # Testar listagem de arquivos na raiz
        print("\n🔍 Testando listagem de arquivos na raiz...")
        try:
            results = adapter.service.files().list(
                pageSize=10,
                fields="nextPageToken, files(id, name, mimeType)"
            ).execute()
            
            items = results.get('files', [])
            print(f"✅ Encontrados {len(items)} arquivos/pastas na raiz:")
            
            for item in items:
                print(f"  - {item['name']} (ID: {item['id']}) - {item['mimeType']}")
                
                # Se for uma pasta chamada "Clientes", mostrar detalhes
                if 'Clientes' in item['name'] or 'clientes' in item['name'].lower():
                    print(f"    🎯 PASTA CLIENTES ENCONTRADA: {item['id']}")
                    
        except Exception as e:
            print(f"❌ Erro na listagem: {e}")
            
        # Testar criação de pasta de teste
        print("\n🔨 Testando criação de pasta de teste...")
        try:
            folder_metadata = {
                'name': 'TESTE_CONTA_SERVICO_' + str(int(time.time())),
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = adapter.service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            print(f"✅ Pasta de teste criada com ID: {folder.get('id')}")
            
            # Deletar a pasta de teste
            adapter.service.files().delete(fileId=folder.get('id')).execute()
            print("✅ Pasta de teste removida")
            
        except Exception as e:
            print(f"❌ Erro na criação de pasta: {e}")
            
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import time
    test_detailed()