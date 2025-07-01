"""
Script para verificar a sanidade dos modelos da aplicação.

Este script tenta importar todos os modelos e enums definidos no pacote
app.models para garantir que não há erros de importação (como imports
circulares ou nomes incorretos). Ele também realiza asserções para
validar configurações críticas, como os nomes das tabelas.
"""
import sys
import os
import traceback

# Adiciona o diretório raiz do projeto ao PYTHONPATH para que `app` seja encontrável
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("--- Iniciando verificação de sanidade dos modelos ---")

try:
    print("Importando todos os modelos e enums de app.models...")
    from app.models import (
        Base, BaseModel,
        AuditLog, Notification, AuditAction, NotificationType,
        Client, TipoPessoaEnum,
        DocumentTemplate, DocumentTemplateVersion,
        FieldType, DocumentStatus, TemplateStatus, EnumValidator,
        FormSubmission, GeneratedForm,
        TemplateCategory, TemplatePlaceholder
    )
    print("-> [SUCESSO] Todas as entidades foram importadas corretamente.")

    print("\nVerificando configurações críticas dos modelos...")
    assert Client.__tablename__ == "clientes", (
        f"Erro de configuração: Client.__tablename__ é '{Client.__tablename__}', "
        "mas o esperado é 'clientes'"
    )
    print("-> [SUCESSO] __tablename__ do modelo Client está correto.")
    
    # Futuramente, outras verificações podem ser adicionadas aqui.

    print("\n--- Verificação de sanidade concluída com sucesso! ---")

except ImportError as e:
    print(f"\n--- [ERRO] Falha na importação ---")
    print(f"Erro: {e}")
    print("Causa provável: Uma importação circular ou um nome incorreto no "
          "arquivo 'app/models/__init__.py' ou em um dos arquivos de modelo.")
    traceback.print_exc()
    sys.exit(1)
except AssertionError as e:
    print(f"\n--- [ERRO] Falha na asserção de configuração ---")
    print(f"Erro: {e}")
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"\n--- [ERRO] Um erro inesperado ocorreu durante a verificação ---")
    print(f"Erro: {e}")
    traceback.print_exc()
    sys.exit(1) 