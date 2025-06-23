"""Configura e expõe a instância Celery integrada ao contexto Flask.

Uso:
from app.celery_app import celery  # já configurado
"""

from __future__ import annotations

import os

from celery import Celery, Task
from flask import Flask


def make_celery(app: Flask) -> Celery:
    """Cria instância Celery acoplada ao contexto Flask.

    A configuração é lida de ``app.config`` e o contexto de aplicação é
    automaticamente empurrado para cada task, permitindo uso de ``current_app``
    e acesso ao banco de dados sem boilerplate extra.
    """
    broker_url = app.config.get("CELERY_BROKER_URL") or os.getenv(
        "CELERY_BROKER_URL", "redis://localhost:6379/0"
    )
    backend_url = app.config.get("CELERY_RESULT_BACKEND", broker_url)

    celery = Celery(
        app.import_name,
        broker=broker_url,
        backend=backend_url,
    )

    # Copia todas as configs começando com CELERY_ para o objeto Celery
    celery.conf.update({k: v for k, v in app.config.items() if k.startswith("CELERY_")})

    class AppContextTask(Task):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return super().__call__(*args, **kwargs)

    celery.Task = AppContextTask  # type: ignore
    return celery
