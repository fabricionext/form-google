"""
API refatorada para geração de documentos com melhorias de performance e tratamento de erros.
"""

import logging
import re
import time
from datetime import datetime
from typing import Dict
from uuid import uuid4

from flask import current_app, jsonify, request

from app.placeholder_mapping import PLACEHOLDER_MAPPING_PF, PLACEHOLDER_MAPPING_PJ
from app.services.document_service import DocumentResult, DocumentService
from app.validators.cliente_validator import ClienteData, validar_dados_cliente
from config import CONFIG

logger = logging.getLogger(__name__)


def get_user_identifier():
    """Identifica usuário para rate limiting"""
    # Usar IP + User-Agent para identificação mais precisa
    user_agent = request.headers.get("User-Agent", "")
    return f"{request.remote_addr}:{hash(user_agent) % 1000}"


def _create_error_response(
    message: str, status_code: int, request_id: str = None
) -> tuple:
    """Cria resposta de erro padronizada"""
    response = {
        "status": "erro",
        "mensagem": message,
        "timestamp": datetime.utcnow().isoformat(),
    }
    if request_id:
        response["request_id"] = request_id

    return jsonify(response), status_code


def _serialize_document_result(result: DocumentResult) -> Dict[str, str]:
    """Serializa resultado do documento para JSON"""
    return {
        "tipo_documento": result.tipo_documento,
        "link": result.link,
        "id": result.id,
        "nome_arquivo": result.nome_arquivo,
    }


def _mapear_dados_entrada(data: Dict) -> Dict:
    """Mapeia dados da entrada da API para formato do validador"""

    def camel_to_snake(name: str) -> str:
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    tipo_pessoa = data.get("tipoPessoa", "pf")
    mapping = PLACEHOLDER_MAPPING_PF if tipo_pessoa == "pf" else PLACEHOLDER_MAPPING_PJ

    resultado = {"tipoPessoa": tipo_pessoa}
    for field_key in mapping.keys():
        attr = camel_to_snake(field_key)
        resultado[attr] = data.get(field_key)

    return resultado


def gerar_documento_api_refatorada():
    """API refatorada para geração de documentos com melhorias"""

    request_id = str(uuid4())
    start_time = time.time()

    logger.info(
        "Iniciando geração de documento",
        extra={
            "request_id": request_id,
            "ip": request.remote_addr,
            "user_agent": request.headers.get("User-Agent", ""),
            "method": request.method,
            "path": request.path,
        },
    )

    try:
        # 1. Validar entrada
        if not request.is_json:
            return _create_error_response("Conteúdo deve ser JSON", 400, request_id)

        data = request.get_json()
        if not data:
            return _create_error_response("Dados JSON vazios", 400, request_id)

        # 2. Mapear dados de entrada
        dados_mapeados = _mapear_dados_entrada(data)

        # 3. Validar e sanitizar dados
        try:
            cliente_data = validar_dados_cliente(dados_mapeados)
        except ValueError as e:
            logger.warning(
                "Dados inválidos recebidos",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "data_keys": list(data.keys()),
                },
            )
            return _create_error_response(str(e), 400, request_id)

        # 4. Processar geração de documentos
        try:
            document_service = DocumentService(CONFIG)
            sucessos, erros = document_service.gerar_documentos_cliente(cliente_data)
        except Exception as e:
            logger.error(
                "Erro no serviço de documentos",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "cliente": f"{cliente_data.primeiro_nome} {cliente_data.sobrenome}",
                },
                exc_info=True,
            )
            return _create_error_response(
                "Erro interno no processamento de documentos", 500, request_id
            )

        # 5. Preparar resposta
        duration = time.time() - start_time

        if erros and not sucessos:
            # Todos falharam
            logger.error(
                "Falha total na geração",
                extra={
                    "request_id": request_id,
                    "erros": erros,
                    "cliente": f"{cliente_data.primeiro_nome} {cliente_data.sobrenome}",
                    "duration": duration,
                },
            )
            return (
                jsonify(
                    {
                        "status": "erro_multiplo",
                        "erros": erros,
                        "request_id": request_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                500,
            )

        elif erros and sucessos:
            # Sucesso parcial
            logger.warning(
                "Sucesso parcial na geração",
                extra={
                    "request_id": request_id,
                    "sucessos": len(sucessos),
                    "erros": len(erros),
                    "cliente": f"{cliente_data.primeiro_nome} {cliente_data.sobrenome}",
                    "duration": duration,
                },
            )
            return (
                jsonify(
                    {
                        "status": "parcialmente_ok",
                        "documentos_gerados": [
                            _serialize_document_result(s) for s in sucessos
                        ],
                        "erros": erros,
                        "request_id": request_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                207,
            )

        else:
            # Sucesso total
            logger.info(
                "Sucesso total na geração",
                extra={
                    "request_id": request_id,
                    "documentos": len(sucessos),
                    "cliente": f"{cliente_data.primeiro_nome} {cliente_data.sobrenome}",
                    "duration": duration,
                },
            )
            return (
                jsonify(
                    {
                        "status": "ok",
                        "documentos_gerados": [
                            _serialize_document_result(s) for s in sucessos
                        ],
                        "request_id": request_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                ),
                200,
            )

    except Exception as e:
        logger.error(
            "Erro interno não tratado",
            extra={"request_id": request_id, "error": str(e), "traceback": True},
            exc_info=True,
        )
        return _create_error_response("Erro interno do servidor", 500, request_id)


# Função para registrar a rota (será chamada pelo blueprint)
def register_document_api_routes(app, limiter, require_api_key):
    """Registra as rotas da API de documentos"""

    @app.route("/api/gerar-documento-v2", methods=["POST"])
    @limiter.limit("5 per minute", key_func=get_user_identifier)
    @require_api_key
    def gerar_documento_v2():
        """Nova versão da API para geração de documentos"""
        return gerar_documento_api_refatorada()

    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Endpoint de health check"""
        return (
            jsonify(
                {
                    "status": "ok",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0",
                }
            ),
            200,
        )
