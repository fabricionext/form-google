#!/usr/bin/env python3
"""
Debug script para verificar integração com Google Drive
"""
import os
import sys
import json
sys.path.insert(0, '/var/www/estevaoalmeida.com.br/form-google')

from app import create_app
from app.extensions import db
from app.peticionador.models import Cliente, TipoPessoaEnum
from app.services.google_service_account import GoogleServiceAccountAuth
from datetime import datetime

def debug_google_drive():
    """Debug da integração com Google Drive"""
    app = create_app()
    
    with app.app_context():
        print("=== DEBUG GOOGLE DRIVE INTEGRATION ===")
        
        # 1. Verificar credenciais da conta de serviço
        print("\n--- 1. VERIFICAÇÃO DAS CREDENCIAIS ---")
        try:
            google_service = GoogleServiceAccountAuth()
            print(f"✅ Service Account Email: {google_service.SERVICE_ACCOUNT_EMAIL}")
            print(f"✅ Service Account ID: {google_service.SERVICE_ACCOUNT_ID}")
            print(f"✅ Credentials file found and loaded")
        except Exception as e:
            print(f"❌ Erro ao carregar credenciais: {e}")
            return

        # 2. Testar conexão básica
        print("\n--- 2. TESTE DE CONEXÃO BÁSICA ---")
        try:
            connection_info = google_service.test_connection()
            if connection_info['authenticated']:
                print(f"✅ Conexão bem-sucedida")
                print(f"   Email: {connection_info['service_account']['email']}")
                print(f"   ID: {connection_info['service_account']['id']}")
                print(f"   Pode listar arquivos: {connection_info['access_test']['can_list_files']}")
            else:
                print(f"❌ Falha na conexão: {connection_info['error']}")
                return
        except Exception as e:
            print(f"❌ Erro no teste de conexão: {e}")
            return

        # 3. Testar acesso à pasta "Clientes"
        print("\n--- 3. TESTE DE ACESSO À PASTA CLIENTES ---")
        try:
            clientes_folder_id = "1sTSGNuAP81x_3Vtq3FCC8xdqfM1rqzdx"
            folder_info = google_service.get_file_info(clientes_folder_id)
            if folder_info['success']:
                print(f"✅ Pasta Clientes acessível: {folder_info['file'].get('name')}")
                print(f"   ID: {folder_info['file'].get('id')}")
                print(f"   Tipo: {folder_info['file'].get('mimeType')}")
            else:
                print(f"❌ Pasta Clientes não acessível: {folder_info['message']}")
        except Exception as e:
            print(f"❌ Erro ao acessar pasta Clientes: {e}")

        # 4. Testar templates individuais
        print("\n--- 4. TESTE DE ACESSO AOS TEMPLATES ---")
        templates = {
            "PF_FICHA_CADASTRAL": "11SLeHknGT1Hy6mUwYgZyhlXJKb1ukcpENfVoF-yNCm8",
            "PF_CONTRATO_HONORARIOS": "1LO2VmP048PMK0rlbLH6oFduV2nOJFj-5lIxlmXUbUis", 
            "PF_PROCURACAO_JUDICIAL": "1C4bJIe-pTMTa4lmMzQ565IXT8b6h9ylj8F27bnngZgE",
            "PJ_FICHA_CADASTRAL": "1pEgnOukv8VsivXkonUEJOudpILEkc_t_C0LtN0b7UYE",
            "PJ_CONTRATO_HONORARIOS": "1ox0ZSUuHyrf37o1EExr7lwZ6Sycf7vClHFpZ65VECIQ",
            "PJ_PROCURACAO_JUDICIAL": "1-LbSJzhT2Y7oHf_WXUofVBHfNutHKwtDnqN17c6HAoQ"
        }
        
        accessible_templates = []
        inaccessible_templates = []
        
        for template_name, template_id in templates.items():
            try:
                template_info = google_service.get_file_info(template_id)
                if template_info['success']:
                    print(f"✅ {template_name}: {template_info['file'].get('name')}")
                    accessible_templates.append(template_name)
                else:
                    print(f"❌ {template_name}: {template_info['message']}")
                    inaccessible_templates.append(template_name)
            except Exception as e:
                print(f"❌ {template_name}: Erro - {e}")
                inaccessible_templates.append(template_name)

        # 5. Teste de criação de pasta para cliente
        print("\n--- 5. TESTE DE CRIAÇÃO DE PASTA ---")
        try:
            drive_service = google_service.get_drive_service()
            
            test_folder_name = f"[TEST]-Debug-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            clientes_folder_id = "1sTSGNuAP81x_3Vtq3FCC8xdqfM1rqzdx"
            
            folder_metadata = {
                'name': test_folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [clientes_folder_id]
            }
            
            test_folder = drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            test_folder_id = test_folder.get('id')
            
            if test_folder_id:
                print(f"✅ Pasta de teste criada: {test_folder_name}")
                print(f"   ID: {test_folder_id}")
                
                # Criar subpasta de teste
                subfolder_metadata = {
                    'name': "Teste_Subpasta",
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [test_folder_id]
                }
                
                subfolder = drive_service.files().create(
                    body=subfolder_metadata,
                    fields='id'
                ).execute()
                
                subfolder_id = subfolder.get('id')
                if subfolder_id:
                    print(f"✅ Subpasta criada: {subfolder_id}")
                
                # Limpar - deletar pasta de teste
                try:
                    drive_service.files().delete(fileId=test_folder_id).execute()
                    print(f"✅ Pasta de teste removida")
                except:
                    print(f"⚠️  Pasta de teste não foi removida (ID: {test_folder_id})")
            else:
                print("❌ Falha ao criar pasta de teste")
        except Exception as e:
            print(f"❌ Erro no teste de criação de pasta: {e}")

        # 6. Resumo e diagnóstico
        print("\n--- 6. DIAGNÓSTICO FINAL ---")
        print(f"Templates acessíveis: {len(accessible_templates)}")
        print(f"Templates inacessíveis: {len(inaccessible_templates)}")
        
        if inaccessible_templates:
            print(f"\n❌ PROBLEMA IDENTIFICADO:")
            print(f"Os seguintes templates precisam ser compartilhados com:")
            print(f"Email: {google_service.SERVICE_ACCOUNT_EMAIL}")
            print(f"ID: {google_service.SERVICE_ACCOUNT_ID}")
            print("\nTemplates inacessíveis:")
            for template in inaccessible_templates:
                template_id = templates[template]
                print(f"  - {template}: {template_id}")
            
            print(f"\n📋 AÇÃO NECESSÁRIA:")
            print(f"1. Abra cada template no Google Drive")
            print(f"2. Clique em 'Compartilhar'")
            print(f"3. Adicione: {google_service.SERVICE_ACCOUNT_EMAIL}")
            print(f"4. Defina permissão como 'Editor' ou 'Visualizador'")
        else:
            print(f"✅ Todos os templates estão acessíveis!")
            
        # Teste adicional: Verificar se consegue criar documentos
        print("\n--- 7. TESTE DE CÓPIA DE TEMPLATE ---")
        if accessible_templates:
            try:
                # Pegar o primeiro template acessível
                first_template = accessible_templates[0]
                template_id = templates[first_template]
                
                # Tentar copiar para a pasta de clientes
                copy_metadata = {
                    'name': f'[TEST] Cópia de {first_template} - {datetime.now().strftime("%Y%m%d_%H%M%S")}',
                    'parents': [clientes_folder_id]
                }
                
                copied_file = drive_service.files().copy(
                    fileId=template_id,
                    body=copy_metadata,
                    fields='id,name,webViewLink'
                ).execute()
                
                print(f"✅ Template copiado com sucesso!")
                print(f"   Template: {first_template}")
                print(f"   ID da cópia: {copied_file['id']}")
                print(f"   Nome: {copied_file['name']}")
                
                # Limpar - deletar cópia
                try:
                    drive_service.files().delete(fileId=copied_file['id']).execute()
                    print(f"✅ Cópia de teste removida")
                except:
                    print(f"⚠️  Cópia de teste não foi removida (ID: {copied_file['id']})")
                    
            except Exception as e:
                print(f"❌ Erro ao copiar template: {e}")
        else:
            print("⚠️  Nenhum template acessível para testar cópia")

        print("\n=== DEBUG CONCLUÍDO ===")

if __name__ == '__main__':
    debug_google_drive()