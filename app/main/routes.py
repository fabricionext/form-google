# Exemplo de require_api_key (simplificado, apenas para demonstração)
# Em um cenário real, isso viria de um local apropriado ou seria mais complexo.
import functools
import json
import re

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

from models import RespostaForm

# A task 'process_document_request_task' foi removida.
# A importação dela aqui deve ser removida para evitar ImportError.
# from app.tasks.document_generation import process_document_request_task

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
    Recebe a solicitação, valida completamente e enfileira a tarefa de processamento.
    """
    current_app.logger.info(f"Requisição recebida em /api/gerar-documento de IP: {request.remote_addr}")

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
    current_app.logger.debug(f"Payload recebido: {payload}")
    
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

    # Validação completa dos dados usando FormValidator
    from app.validators.form_validator import FormValidator
    
    validator = FormValidator()
    is_valid, errors = validator.validate_form_data(payload)
    
    if not is_valid:
        current_app.logger.warning(f"Dados inválidos recebidos: {errors}")
        return (
            jsonify(
                {
                    "status": "erro_validacao",
                    "mensagem": "Dados inválidos",
                    "erros": errors
                }
            ),
            400,
        )

    try:
        # --- NOVA ESTRATÉGIA DE SALVAMENTO ---
        # 1. Salvar o cliente completo no banco de dados primeiro.
        dados_cliente = payload.get("dadosCliente", {})
        
        # Normalizar CPF
        cpf_normalizado = re.sub(r'\\D', '', dados_cliente.get("cpf", ""))

        novo_cliente = RespostaForm(
            tipo_pessoa=payload.get("tipoPessoa"),
            cpf=cpf_normalizado,
            email=dados_cliente.get("email"),
            primeiro_nome=dados_cliente.get("primeiroNome"),
            sobrenome=dados_cliente.get("sobrenome"),
            nacionalidade=dados_cliente.get("nacionalidade"),
            estado_civil=dados_cliente.get("estadoCivil"),
            profissao=dados_cliente.get("profissao"),
            data_nascimento=dados_cliente.get("dataNascimento"),
            rg=dados_cliente.get("rg"),
            estado_emissor_rg=dados_cliente.get("estadoEmissorRg"),
            cnh=dados_cliente.get("cnh"),
            cep=dados_cliente.get("cep"),
            logradouro=dados_cliente.get("endereco") or dados_cliente.get("logradouro"),
            numero=dados_cliente.get("numero"),
            complemento=dados_cliente.get("complemento"),
            bairro=dados_cliente.get("bairro"),
            cidade=dados_cliente.get("cidade"),
            uf_endereco=dados_cliente.get("estado") or dados_cliente.get("uf"),
            telefone_celular=dados_cliente.get("telefoneCelular"),
            outro_telefone=dados_cliente.get("telefoneAdicional"),
            status_processamento="Recebido",
            submission_id=f"api-{datetime.now().isoformat()}"
        )
        
        db.session.add(novo_cliente)
        db.session.commit()
        
        current_app.logger.info(f"Cliente salvo no banco com ID: {novo_cliente.id}")

        # 2. Enfileirar a tarefa de geração de documentos passando apenas o ID.
        from app.tasks.document_generation import gerar_documentos_task
        from kombu.exceptions import KombuError

        try:
            task = gerar_documentos_task.delay(
                resposta_id=novo_cliente.id,
                documentos_requeridos=payload.get("documentosRequeridos")
            )
            current_app.logger.info(
                f"Tarefa de geração de documentos enfileirada para o cliente ID {novo_cliente.id} com a Task ID: {task.id}"
            )
        except KombuError as e:
            current_app.logger.error(f"ERRO DE SERIALIZAÇÃO/KOMBU AO ENFILEIRAR: {e}", exc_info=True)
            return jsonify({"status": "erro_fila_serializacao", "mensagem": "Erro interno ao processar a solicitação."}), 500
        except Exception as e:
             current_app.logger.error(f"Erro inesperado ao enfileirar tarefa: {e}", exc_info=True)
             return jsonify({"status": "erro_fila_inesperado", "mensagem": "Não foi possível iniciar o processamento."}), 500

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
@limiter.limit("60 per minute")  # Limite para polling
def task_status(task_id):
    """
    Consulta o status de uma tarefa Celery pelo seu ID.
    Inclui progresso detalhado e links de documentos gerados.
    """
    try:
        # Cria uma instância do Celery no contexto da requisição atual
        celery_app = make_celery(current_app._get_current_object())
        task = celery_app.AsyncResult(task_id)

        response_data = {
            "task_id": task_id,
            "status": task.state,
            "timestamp": datetime.now().isoformat()
        }

        if task.state == "PENDING":
            response_data["status_message"] = "Tarefa pendente ou não encontrada."
            response_data["progress"] = 0
        elif task.state == "PROGRESS":
            # Inclui informações de progresso se disponíveis
            info = task.info or {}
            response_data.update(info)
            response_data["progress"] = info.get("progress", 25)  # Default 25%
            response_data["status_message"] = info.get("message", "Processando...")
        elif task.state == "SUCCESS":
            result = task.result or {}
            response_data["result"] = result
            response_data["progress"] = 100
            response_data["status_message"] = "Tarefa concluída com sucesso."
            
            # Se houver resposta_id, buscar informações adicionais do banco
            if isinstance(result, dict) and result.get("resposta_id"):
                from models import RespostaForm
                resposta = RespostaForm.query.get(result["resposta_id"])
                if resposta:
                    response_data["cliente_nome"] = f"{resposta.primeiro_nome or ''} {resposta.sobrenome or ''}".strip()
                    response_data["link_pasta_cliente"] = resposta.link_pasta_cliente
                    if resposta.observacoes_processamento:
                        try:
                            import json
                            obs = json.loads(resposta.observacoes_processamento)
                            response_data["documentos_gerados"] = obs.get("links", [])
                        except:
                            pass
                            
        elif task.state == "FAILURE":
            response_data["error_message"] = str(task.info)
            response_data["traceback"] = task.traceback
            response_data["progress"] = 0
            response_data["status_message"] = "Erro no processamento"
            current_app.logger.error(f"Falha na tarefa {task_id}: {task.info}")
            return jsonify(response_data), 500
        else:
            response_data["status_message"] = f"A tarefa está no estado: {task.state}"
            response_data["progress"] = 50  # Estado intermediário

        current_app.logger.debug(f"Status da tarefa {task_id}: {task.state}")
        return jsonify(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Erro ao consultar status da tarefa {task_id}: {e}")
        return jsonify({
            "task_id": task_id,
            "status": "ERROR",
            "error_message": "Erro interno ao consultar status",
            "timestamp": datetime.now().isoformat()
        }), 500
