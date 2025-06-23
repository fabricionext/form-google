"""Tasks de geração de documentos Google Docs com controle de rate-limit e backoff."""

from __future__ import annotations

import json
import random
from datetime import datetime

from celery import shared_task
from celery.utils.log import get_task_logger
from flask import current_app
from googleapiclient.errors import HttpError

from app.peticionador.services import DocumentGenerationService
from extensions import db
from models import RespostaForm

logger = get_task_logger(__name__)

RATE_LIMIT = "20/m"  # conservador (Google Docs write quota 60/min)


@shared_task(bind=True, name="tasks.process_document_request")
def process_document_request_task(self, payload_json_str: str):
    """
    Tarefa orquestradora principal.
    Recebe o payload da API, valida, salva no DB e dispara a geração.
    """
    from document_generator import (
        _initialize_google_services,
        buscar_ou_criar_pasta_cliente,
    )

    payload = json.loads(payload_json_str)
    dados_cliente_payload = payload.get("dadosCliente", {})
    tipo_pessoa = payload.get("tipoPessoa", "pf")
    cpf = dados_cliente_payload.get("cpf")
    cnpj = dados_cliente_payload.get("cnpj")
    email = dados_cliente_payload.get("email")

    nova_resposta = RespostaForm(
        submission_id=f"task-{self.request.id}",
        tipo_pessoa=tipo_pessoa,
        cpf=cpf,
        cnpj=cnpj,
        email=email,
        primeiro_nome=dados_cliente_payload.get("nome"),
        status_processamento="Pendente",
    )
    with db.session.begin():
        db.session.add(nova_resposta)

    try:
        google_credentials_json_str = current_app.config.get(
            "GOOGLE_CREDENTIALS_AS_JSON_STR"
        )
        drive_service, _ = _initialize_google_services(google_credentials_json_str)

        # Corrigir mapeamento de campos para pasta
        primeiro_nome = (
            dados_cliente_payload.get("primeiroNome")
            or dados_cliente_payload.get("nome")
            or nova_resposta.primeiro_nome
            or "Cliente"
        )
        sobrenome = dados_cliente_payload.get("sobrenome") or "Sem Sobrenome"

        logger.info(
            f"Criando pasta para: primeiro_nome='{primeiro_nome}', sobrenome='{sobrenome}'"
        )

        id_pasta_cliente = buscar_ou_criar_pasta_cliente(
            drive_service, primeiro_nome, sobrenome, datetime.now().year
        )
        link_pasta = f"https://drive.google.com/drive/folders/{id_pasta_cliente}"

        with db.session.begin():
            nova_resposta.link_pasta_cliente = link_pasta
            nova_resposta.status_processamento = "Documentos_Enfileirados"

        documentos_requeridos = payload.get("documentosRequeridos")
        gerar_documentos_task.delay(
            resposta_id=nova_resposta.id,
            dados_cliente_json=json.dumps(dados_cliente_payload),
            tipo_pessoa=tipo_pessoa,
            documentos_requeridos=documentos_requeridos,
        )

        return {"status": "Enfileirado", "resposta_id": nova_resposta.id}

    except Exception as e:
        logger.error(
            f"Falha na tarefa orquestradora para resposta {nova_resposta.id}: {e}",
            exc_info=True,
        )
        with db.session.begin():
            nova_resposta.status_processamento = "Falha_orquestracao"
            nova_resposta.observacoes_processamento = str(e)
        raise
    finally:
        db.session.remove()


@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    rate_limit=RATE_LIMIT,
    name="tasks.generate_final_documents",
)
def gerar_documentos_task(
    self,
    resposta_id: int,
    dados_cliente_json: str,
    tipo_pessoa: str,
    documentos_requeridos: dict | None = None,
):
    """Gera documentos para o RespostaForm indicado.

    A task atualiza o status_processamento em RespostaForm:
    - Processando
    - Concluido
    - Falha
    """
    logger.info(f"Iniciando gerar_documentos_task para resposta_id: {resposta_id}")

    # Debug: Log dos dados recebidos
    logger.debug("[CELERY_DEBUG] resposta_id: %s", resposta_id)
    logger.debug("[CELERY_DEBUG] tipo_pessoa: %s", tipo_pessoa)
    logger.debug("[CELERY_DEBUG] dados_cliente_json (tipo): %s", type(dados_cliente_json))
    logger.debug("[CELERY_DEBUG] dados_cliente_json (conteúdo): %s", dados_cliente_json)
    logger.debug("[CELERY_DEBUG] documentos_requeridos: %s", documentos_requeridos)

    resposta = RespostaForm.query.get(resposta_id)
    if not resposta:
        logger.error(f"TASK ABORTADA: RespostaForm {resposta_id} não encontrada.")
        return

    try:
        logger.info(
            f"Atualizando status para 'Processando' para resposta_id: {resposta_id}"
        )
        with db.session.begin():
            resposta.status_processamento = "Processando"

        google_credentials_json_str = current_app.config.get(
            "GOOGLE_CREDENTIALS_AS_JSON_STR"
        )
        logger.info("Criando instância do DocumentGenerationService.")
        service = DocumentGenerationService()

        # Debug: Verificar se dados_cliente_json é string ou dict
        if isinstance(dados_cliente_json, str):
            dados_cliente = json.loads(dados_cliente_json)
            logger.debug("[CELERY_DEBUG] dados_cliente_json era string, convertido para dict")
            logger.debug("[CELERY_DEBUG] dados_cliente (após conversão): %s", dados_cliente)
        else:
            dados_cliente = dados_cliente_json
            logger.debug("[CELERY_DEBUG] dados_cliente_json já era dict")
            logger.debug("[CELERY_DEBUG] dados_cliente: %s", dados_cliente)

        current_app.logger.info(
            "Chamando service.generate_documents para tipo_pessoa='%s' com documentos: %s",
            tipo_pessoa,
            documentos_requeridos,
        )
        links = service.generate_documents(
            dados_cliente, tipo_pessoa, documentos_requeridos
        )
        logger.info(f"service.generate_documents retornou: {links}")

        if links:
            pasta_id = links[0].split("/")[5]
            resposta.link_pasta_cliente = (
                f"https://drive.google.com/drive/folders/{pasta_id}"
            )
        with db.session.begin():
            resposta.status_processamento = "Concluido"
            resposta.observacoes_processamento = json.dumps(
                {"links": links}, ensure_ascii=False
            )

    except HttpError as e:
        if e.resp.status in (429, 500, 503):
            delay = (2**self.request.retries) * 60 + random.uniform(1, 10)
            logger.warning(
                "Rate limit/erro 5xx ao gerar docs (tentativa %s). Retentativa em %.1fs",
                self.request.retries + 1,
                delay,
            )
            raise self.retry(exc=e, countdown=delay)
        with db.session.begin():
            resposta.status_processamento = "Falha"
            resposta.observacoes_processamento = str(e)
        raise
    except Exception as e:
        logger.error(
            f"ERRO FATAL na gerar_documentos_task para resposta_id {resposta_id}",
            exc_info=True,
        )
        with db.session.begin():
            resposta.status_processamento = "Falha"
            resposta.observacoes_processamento = str(e)
        raise
    finally:
        db.session.remove()
