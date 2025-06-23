#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar a solução de duplicação de documentos.
Este script testa a função check_document_exists e copy_template_and_fill
para garantir que documentos não sejam duplicados.
"""

import pytest

pytest.skip("requires Google services", allow_module_level=True)

import logging
import os
import sys

from dotenv import load_dotenv

from app.peticionador.google_services import (
    check_document_exists,
    copy_template_and_fill,
    get_docs_service,
    get_drive_service,
)
from config import CONFIG

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def main():
    """Função principal para testar a solução de duplicação de documentos."""
    # Carregar variáveis de ambiente
    load_dotenv()

    # Obter serviços do Google
    drive_service = get_drive_service()
    docs_service = get_docs_service()

    if not drive_service or not docs_service:
        logger.error("Não foi possível obter os serviços do Google Drive ou Docs.")
        return

    # Obter configurações necessárias
    try:
        template_id = CONFIG["TEMPLATES"]["pet"]["Suspensao Direito Dirigir"]
        parent_folder_id = CONFIG.get("PARENT_FOLDER_ID")

        if not template_id or not parent_folder_id:
            logger.error("Template ID ou Parent Folder ID não configurados.")
            return
    except KeyError as e:
        logger.error(f"Erro ao obter configurações: {e}")
        return

    # Nome da pasta de teste
    test_folder_name = "2025-Cliente Teste"

    # Criar pasta de teste se não existir
    from app.peticionador.google_services import find_or_create_client_folder

    test_folder_id = find_or_create_client_folder(drive_service, test_folder_name)

    if not test_folder_id:
        logger.error("Não foi possível criar ou encontrar a pasta de teste.")
        return

    # Nome do documento de teste
    test_document_name = f"{test_folder_name}-Suspensão do Direito de Dirigir-12345"

    # Dados de teste para substituição
    test_replacements = {
        "proprietario.nome_completo": "Cliente Teste",
        "proprietario.primeiro_nome": "Cliente",
        "proprietario.sobrenome": "Teste",
        "proprietario.nacionalidade": "Brasileiro",
        "proprietario.estado_civil": "Solteiro",
        "proprietario.profissao": "Desenvolvedor",
        "proprietario.rg": "1234567",
        "proprietario.rg_emissor": "SSP/SP",
        "proprietario.cpf": "123.456.789-00",
        "proprietario.endereco_completo": "Rua Teste, 123 - Bairro Teste - Cidade Teste/SP - CEP: 12345-678",
        "proprietario.cnh": "98765432",
        "processo.numero": "12345",
        "processo.total_pontos_cnh": "30",
        "data.atual_extenso": "17 de junho de 2025",
    }

    # Teste 1: Verificar se o documento já existe
    logger.info("Teste 1: Verificando se o documento já existe...")
    exists, doc_id, doc_link = check_document_exists(
        drive_service, test_document_name, test_folder_id
    )

    if exists:
        logger.info(f"Documento já existe: ID={doc_id}, Link={doc_link}")
    else:
        logger.info("Documento não existe. Criando novo documento...")

    # Teste 2: Tentar criar o documento duas vezes
    logger.info("Teste 2: Tentando criar o documento pela primeira vez...")
    doc_id1, doc_link1 = copy_template_and_fill(
        drive_service,
        docs_service,
        template_id,
        test_document_name,
        test_folder_id,
        test_replacements,
    )

    if not doc_id1 or not doc_link1:
        logger.error("Falha ao criar o documento pela primeira vez.")
        return

    logger.info(
        f"Documento criado/encontrado na primeira tentativa: ID={doc_id1}, Link={doc_link1}"
    )

    # Tentar criar o mesmo documento novamente
    logger.info("Teste 3: Tentando criar o mesmo documento novamente...")
    doc_id2, doc_link2 = copy_template_and_fill(
        drive_service,
        docs_service,
        template_id,
        test_document_name,
        test_folder_id,
        test_replacements,
    )

    if not doc_id2 or not doc_link2:
        logger.error("Falha ao processar a segunda tentativa.")
        return

    logger.info(f"Resultado da segunda tentativa: ID={doc_id2}, Link={doc_link2}")

    # Verificar se os IDs são iguais (não houve duplicação)
    if doc_id1 == doc_id2:
        logger.info("SUCESSO: Não houve duplicação! Os IDs dos documentos são iguais.")
    else:
        logger.warning("FALHA: Houve duplicação! Os IDs dos documentos são diferentes.")

    logger.info("Teste concluído.")


if __name__ == "__main__":
    main()
