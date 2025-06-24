# Exemplo de require_api_key (simplificado, apenas para demonstração)
# Em um cenário real, isso viria de um local apropriado ou seria mais complexo.
import functools
import json

# Importações do sistema
# Importações para integração Google Docs (se ainda forem usadas diretamente aqui, caso contrário, podem ser removidas se document_generator lida com tudo)
# from app.peticionador.google_services import get_drive_service, get_docs_service, copy_template_and_fill, find_or_create_client_folder, get_current_date_extenso
import os
import traceback
from datetime import datetime

import requests
from flask import (
    current_app,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import (  # Manter generate_csrf se usado, remover CSRFProtect e a instanciação local
    generate_csrf,
)
from werkzeug.utils import secure_filename

from app.tasks.document_generation import process_document_request_task

# Importar funções de geração de documentos e modelos
from document_generator import (
    _initialize_google_services,
    buscar_ou_criar_pasta_cliente,
    gerar_documento_cliente,
)

# Importar extensões centralizadas
from extensions import csrf, db, limiter

# Importar o blueprint 'main_bp' de app.main.__init__
from . import main_bp

# Idealmente, a chave de API e sua verificação seriam gerenciadas de forma mais robusta
# Por agora, vamos assumir que require_api_key é um decorador que pode ser importado
# ou que a lógica será integrada diretamente se for simples.
# from ...security_middleware import require_api_key # Exemplo se estivesse em outro lugar



def require_api_key(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        api_key_received = request.headers.get("X-API-KEY")
        expected_api_key = current_app.config.get("INTERNAL_API_KEY")

        if not expected_api_key:
            current_app.logger.error(
                "CRÍTICO: INTERNAL_API_KEY não está configurada no servidor!"
            )
            return (
                jsonify(
                    {
                        "message": "Erro de configuração do servidor: Chave de API interna não definida."
                    }
                ),
                500,
            )

        if api_key_received and api_key_received == expected_api_key:
            current_app.logger.info("Chave de API validada com sucesso.")
            return f(*args, **kwargs)

        current_app.logger.warning(
            f"Tentativa de acesso com chave de API inválida ou ausente. Chave recebida: '{api_key_received}'"
        )
        return jsonify({"message": "Chave de API inválida ou ausente"}), 401

    return decorated_function



@main_bp.route("/")
@limiter.limit("100 per day")
@csrf.exempt  # Página inicial pode ser acessada sem CSRF
def home():
    """Rota principal que redireciona para o formulário de cadastro."""
    return redirect(url_for("main.cadastro_de_cliente"))


# Definição do formulário para carregar o token CSRF
class ClientForm(FlaskForm):
    dummy = None  # Campo mínimo para evitar classe vazia


@main_bp.route("/cadastrodecliente")
@limiter.limit("100 per hour")
def cadastro_de_cliente():
    """Exibe o formulário de cadastro de cliente com proteção CSRF."""
    form = ClientForm()
    return render_template("index.html", form=form)


@main_bp.route("/api/cep/<cep>")
@limiter.limit("10 per minute")
def cep_lookup(cep):
    """Consulta CEP com validação e tratamento de erros."""
    try:
        if not cep.isdigit() or len(cep) != 8:
            return jsonify({"status": "erro", "mensagem": "CEP inválido"}), 400

        response = requests.get(f"https://viacep.com.br/ws/{cep}/json/", timeout=5)
        response.raise_for_status()
        return jsonify(response.json())

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Erro ao consultar CEP {cep}: {str(e)}")
        return (
            jsonify(
                {
                    "status": "erro",
                    "mensagem": "Erro ao consultar CEP. Tente novamente mais tarde.",
                }
            ),
            500,
        )


@main_bp.route("/api/gerar-documento", methods=["POST"])
@csrf.exempt  # Manter isenção de CSRF para este teste
def gerar_documento_api():
    """
    Recebe a solicitação, valida o básico e enfileira a tarefa de processamento.
    """
    current_app.logger.info("Requisição recebida em /api/gerar-documento")

    if not request.is_json:
        return (
            jsonify(
                {
                    "status": "erro",
                    "mensagem": "O Content-Type deve ser application/json",
                }
            ),
            400,
        )

    payload = request.get_json()
    if not payload.get("dadosCliente"):
        return (
            jsonify(
                {
                    "status": "erro_validacao",
                    "mensagem": "O objeto 'dadosCliente' é obrigatório.",
                }
            ),
            400,
        )

    try:
        # Passa o payload completo como uma string JSON para a tarefa
        payload_json_str = json.dumps(payload)
        task = process_document_request_task.delay(payload_json_str)

        current_app.logger.info(
            f"Tarefa de processamento de documentos enfileirada com ID: {task.id}"
        )

        # Responde imediatamente com HTTP 202 Accepted
        return (
            jsonify(
                {
                    "status": "sucesso_enfileirado",
                    "mensagem": "Solicitação recebida e está sendo processada em segundo plano.",
                    "task_id": task.id,
                }
            ),
            202,
        )

    except Exception as e:
        current_app.logger.error(
            f"Erro ao enfileirar tarefa Celery: {str(e)}", exc_info=True
        )
        return (
            jsonify(
                {
                    "status": "erro_fila",
                    "mensagem": "Não foi possível iniciar o processamento.",
                }
            ),
            500,
        )


from app.celery_app import make_celery


@main_bp.route("/api/task-status/<task_id>", methods=["GET"])
def task_status(task_id):
    """Consulta o status de uma tarefa Celery pelo seu ID."""
    # Cria uma instância do Celery no contexto da requisição atual
    celery_app = make_celery(current_app._get_current_object())
    task = celery_app.AsyncResult(task_id)

    response_data = {
        "task_id": task_id,
        "status": task.state,
    }

    if task.state == "PENDING":
        response_data["status_message"] = "Tarefa pendente ou não encontrada."
    elif task.state == "PROGRESS":
        response_data.update(task.info)
    elif task.state == "SUCCESS":
        response_data["result"] = task.result
        response_data["status_message"] = "Tarefa concluída com sucesso."
    elif task.state == "FAILURE":
        response_data["error_message"] = str(task.info)
        response_data["traceback"] = task.traceback
        return jsonify(response_data), 500
    else:
        response_data["status_message"] = f"A tarefa está no estado: {task.state}"

    return jsonify(response_data)
