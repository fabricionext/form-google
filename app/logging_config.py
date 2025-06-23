"""
Configuração de logging estruturado para melhor monitoramento e debugging.
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """Formatter que gera logs em formato JSON estruturado"""

    def format(self, record: logging.LogRecord) -> str:
        """Formata o log record em JSON estruturado"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Adicionar campos extras se existirem
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # Adicionar exceção se existir
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class RequestFormatter(logging.Formatter):
    """Formatter específico para logs de requisições HTTP"""

    def format(self, record: logging.LogRecord) -> str:
        """Formata logs de requisições com informações contextuais"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "type": "request",
            "ip": getattr(record, "ip", "unknown"),
            "method": getattr(record, "method", "unknown"),
            "path": getattr(record, "path", "unknown"),
            "status_code": getattr(record, "status_code", "unknown"),
            "duration": getattr(record, "duration", 0),
            "user_agent": getattr(record, "user_agent", "unknown"),
            "request_id": getattr(record, "request_id", "unknown"),
        }

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(app, log_level: str = "INFO"):
    """Configura o sistema de logging estruturado"""

    # Configurar nível de log
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Criar diretório de logs se não existir
    import os

    if not os.path.exists("logs"):
        os.makedirs("logs")

    # Configurar logger principal
    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    # Limpar handlers existentes
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Handler para console (desenvolvimento)
    if app.debug:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # Handler para arquivo de logs estruturados
    file_handler = logging.handlers.RotatingFileHandler(
        "logs/app_structured.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(StructuredFormatter())
    logger.addHandler(file_handler)

    # Handler para logs de erro
    error_handler = logging.handlers.RotatingFileHandler(
        "logs/app_error.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    logger.addHandler(error_handler)

    # Handler para logs de requisições
    request_handler = logging.handlers.RotatingFileHandler(
        "logs/app_requests.log", maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    request_handler.setLevel(logging.INFO)
    request_handler.setFormatter(RequestFormatter())
    logger.addHandler(request_handler)

    # Configurar loggers específicos
    loggers_to_configure = [
        "app.services.document_service",
        "app.validators.cliente_validator",
        "app.api.document_api",
        "document_generator",
    ]

    for logger_name in loggers_to_configure:
        specific_logger = logging.getLogger(logger_name)
        specific_logger.setLevel(numeric_level)
        # Não propagar para o logger raiz para evitar duplicação
        specific_logger.propagate = False

        # Adicionar handlers específicos se necessário
        specific_handler = logging.handlers.RotatingFileHandler(
            f'logs/{logger_name.replace(".", "_")}.log',
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
        )
        specific_handler.setLevel(numeric_level)
        specific_handler.setFormatter(StructuredFormatter())
        specific_logger.addHandler(specific_handler)

    # Log de inicialização
    app.logger.info(
        "Sistema de logging estruturado configurado",
        extra={
            "extra_fields": {
                "log_level": log_level,
                "handlers": len(logger.handlers),
                "debug_mode": app.debug,
            }
        },
    )


def log_request_info(request, response, duration: float):
    """Loga informações estruturadas sobre uma requisição"""
    logger = logging.getLogger("app.requests")

    log_data = {
        "ip": request.remote_addr,
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "duration": round(duration, 3) if duration is not None else None,
        "user_agent": request.headers.get("User-Agent", ""),
        "content_length": len(response.get_data()),
        "query_string": (
            request.query_string.decode("utf-8") if request.query_string else ""
        ),
    }

    # Adicionar headers relevantes
    relevant_headers = ["Referer", "Origin", "X-Forwarded-For", "X-Real-IP"]
    for header in relevant_headers:
        if header in request.headers:
            log_data[f'header_{header.lower().replace("-", "_")}'] = request.headers[
                header
            ]

    logger.info("Requisição processada", extra={"extra_fields": log_data})


def log_document_generation(
    cliente_data, resultados, duration: float, request_id: str = None
):
    """Loga informações estruturadas sobre geração de documentos"""
    logger = logging.getLogger("app.services.document_service")

    sucessos = [r for r in resultados if r.sucesso]
    erros = [r for r in resultados if not r.sucesso]

    log_data = {
        "cliente_nome": f"{cliente_data.primeiro_nome} {cliente_data.sobrenome}",
        "tipo_pessoa": cliente_data.tipo_pessoa,
        "email": cliente_data.email,
        "documentos_solicitados": len(resultados),
        "documentos_sucesso": len(sucessos),
        "documentos_erro": len(erros),
        "duration": round(duration, 3),
        "request_id": request_id,
    }

    if erros:
        log_data["erros"] = [r.erro for r in erros]

    if sucessos:
        log_data["documentos_gerados"] = [r.tipo_documento for r in sucessos]

    level = (
        logging.ERROR
        if erros and not sucessos
        else logging.WARNING if erros else logging.INFO
    )
    logger.log(
        level, "Geração de documentos concluída", extra={"extra_fields": log_data}
    )
