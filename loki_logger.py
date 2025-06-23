"""
Logger personalizado para enviar logs para Grafana Loki
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, Optional

import requests


class LokiHandler(logging.Handler):
    """
    Handler personalizado para enviar logs para Loki
    """

    def __init__(
        self,
        loki_url: str = "http://localhost:3100",
        application: str = "form-google",
        environment: str = "development",
    ):
        super().__init__()
        self.loki_url = loki_url.rstrip("/")
        self.application = application
        self.environment = environment

    def emit(self, record):
        try:
            # Preparar os labels
            labels = {
                "application": self.application,
                "environment": self.environment,
                "level": record.levelname.lower(),
                "logger": record.name,
            }

            # Adicionar labels extras se disponíveis
            if hasattr(record, "user_id"):
                labels["user_id"] = str(record.user_id)
            if hasattr(record, "form_id"):
                labels["form_id"] = str(record.form_id)
            if hasattr(record, "operation"):
                labels["operation"] = record.operation

            # Preparar a mensagem
            log_entry = {
                "timestamp": int(time.time() * 1e9),  # Nanoseconds
                "line": self.format(record),
            }

            # Enviar para Loki
            payload = {
                "streams": [
                    {
                        "stream": labels,
                        "values": [[str(log_entry["timestamp"]), log_entry["line"]]],
                    }
                ]
            }

            response = requests.post(
                f"{self.loki_url}/loki/api/v1/push",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=5,
            )

            if response.status_code != 204:
                print(
                    f"Erro ao enviar log para Loki: {response.status_code} - {response.text}"
                )

        except Exception as e:
            # Fallback para console se Loki não estiver disponível
            print(f"Erro ao enviar log para Loki: {e}")
            print(f"Log original: {self.format(record)}")


def setup_loki_logging(
    loki_url: str = "http://localhost:3100",
    application: str = "form-google",
    environment: str = "development",
    level: int = logging.INFO,
) -> Optional[LokiHandler]:
    """
    Configura o logging para Loki

    Args:
        loki_url: URL do Loki
        application: Nome da aplicação
        environment: Ambiente (development, production, etc.)
        level: Nível de log

    Returns:
        LokiHandler se configurado com sucesso, None caso contrário
    """
    try:
        # Testar conexão com Loki
        response = requests.get(f"{loki_url}/ready", timeout=5)
        if response.status_code != 200:
            print(f"⚠️  Loki não está disponível em {loki_url}")
            return None

        # Criar handler
        loki_handler = LokiHandler(loki_url, application, environment)
        loki_handler.setLevel(level)

        # Configurar formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        loki_handler.setFormatter(formatter)

        # Adicionar ao logger raiz
        logging.getLogger().addHandler(loki_handler)

        print(f"✅ Loki logging configurado: {loki_url}")
        return loki_handler

    except Exception as e:
        print(f"❌ Erro ao configurar Loki logging: {e}")
        return None


def log_google_api_operation(
    operation: str, status: str, details: Dict[str, Any] = None
):
    """
    Log específico para operações da API do Google
    """
    logger = logging.getLogger("google_api")

    # Adicionar contexto extra
    extra = {"operation": operation, "component": "google_api"}
    if details:
        extra.update(details)

    log_record = logger.makeRecord(
        "google_api",
        logging.INFO,
        "",
        0,
        f"Google API {operation}: {status}",
        (),
        None,
        extra=extra,
    )

    logger.handle(log_record)


def log_document_generation(
    form_id: int, user_id: int, status: str, details: Dict[str, Any] = None
):
    """
    Log específico para geração de documentos
    """
    logger = logging.getLogger("document_generation")

    # Adicionar contexto extra
    extra = {
        "form_id": form_id,
        "user_id": user_id,
        "operation": "document_generation",
        "component": "document_generation",
    }
    if details:
        extra.update(details)

    log_record = logger.makeRecord(
        "document_generation",
        logging.INFO,
        "",
        0,
        f"Document generation {form_id}: {status}",
        (),
        None,
        extra=extra,
    )

    logger.handle(log_record)
