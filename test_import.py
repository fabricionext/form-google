#!/usr/bin/env python3

import os
import sys

import pytest

pytest.skip("requires Google credentials", allow_module_level=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Testando importação do DocumentGenerationService...")

try:
    from app.peticionador.services import DocumentGenerationService

    print("✅ DocumentGenerationService importado com sucesso")

    # Testar inicialização
    print("🧪 Testando inicialização...")
    service = DocumentGenerationService()
    print("✅ DocumentGenerationService inicializado com sucesso")

    # Testar obtenção de credenciais
    print("🧪 Testando obtenção de credenciais...")
    credentials = service._get_credentials()
    print("✅ Credenciais obtidas com sucesso")

    # Testar inicialização do Drive service
    print("🧪 Testando inicialização do Drive service...")
    drive_service = service.drive_service
    print("✅ Drive service inicializado com sucesso")

    # Testar inicialização do Docs service
    print("🧪 Testando inicialização do Docs service...")
    docs_service = service.docs_service
    print("✅ Docs service inicializado com sucesso")

    print("🎉 Todos os testes passaram!")

except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback

    traceback.print_exc()
