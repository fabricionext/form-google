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
    Blueprint,
    flash,
    session,
)
from flask_wtf import FlaskForm
from flask_wtf.csrf import (  # Manter generate_csrf se usado, remover CSRFProtect e a instanciação local
    generate_csrf,
)
from werkzeug.utils import secure_filename
from flask_login import current_user, login_required

# RespostaForm não está mais disponível - removido

# A task 'process_document_request_task' foi removida.
# A importação dela aqui deve ser removida para evitar ImportError.
# from app.tasks.document_generation import process_document_request_task

# TODO: Importar funções de geração de documentos quando necessário
# from document_generator import (...)  # Removido temporariamente

# Importar extensões centralizadas
from app.extensions import csrf, db, limiter

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



# @main_bp.route("/")
# @limiter.limit("100 per day") 
# @csrf.exempt  # Página inicial pode ser acessada sem CSRF
# def home():
#     """Rota principal que redireciona para o formulário de cadastro."""
#     return redirect(url_for("main.cadastro_de_cliente"))
# COMENTADO: A rota raiz agora é servida pelo Vue.js frontend


# Definição do formulário para carregar o token CSRF
class ClientForm(FlaskForm):
    dummy = None  # Campo mínimo para evitar classe vazia


@main_bp.route("/cadastrodecliente")
@limiter.limit("100 per hour")
def cadastro_de_cliente():
    """Serve a aplicação Vue.js para cadastro de cliente."""
    return serve_vue_app()

# Rotas adicionais que devem servir a mesma aplicação Vue.js (SPA routing)
@main_bp.route("/clientes/novo")
@main_bp.route("/modelos")
@main_bp.route("/admin/formularios")  # Prefixo /admin para evitar conflito
@main_bp.route("/admin/formularios/<path:subpath>")
@limiter.limit("100 per hour")
def vue_spa_routes(subpath=None):
    """Serve a aplicação Vue.js para rotas do SPA."""
    return serve_vue_app()


def serve_vue_app():
    """
    Serve a aplicação Vue.js construída.
    
    Lê o arquivo index.html da pasta html/ (build do frontend)
    e retorna com headers apropriados para SPA.
    """
    import os
    from flask import current_app, send_file, Response
    
    try:
        # Caminho para o build do frontend
        html_path = os.path.join(current_app.root_path, '..', 'html', 'index.html')
        
        if not os.path.exists(html_path):
            current_app.logger.error(f"Arquivo Vue.js não encontrado: {html_path}")
            return "Aplicação frontend não encontrada", 404
            
        # Ler o conteúdo do arquivo
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Criar resposta com headers apropriados
        response = Response(content, mimetype='text/html')
        
        # Headers para SPA - não cachear o index.html
        response.cache_control.no_store = True
        response.cache_control.max_age = 0
        response.cache_control.must_revalidate = True
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Erro ao servir aplicação Vue.js: {str(e)}")
        return "Erro interno do servidor", 500


@main_bp.route("/assets/<path:filename>")
def vue_assets(filename):
    """Serve arquivos estáticos do Vue.js (CSS, JS, etc.)."""
    import os
    from flask import current_app, send_file, abort
    
    try:
        # Caminho para a pasta de assets do build
        assets_path = os.path.join(current_app.root_path, '..', 'html', 'assets', filename)
        
        if not os.path.exists(assets_path):
            current_app.logger.warning(f"Asset não encontrado: {filename}")
            abort(404)
            
        # Enviar arquivo com cache longo (assets têm hash no nome)
        response = send_file(assets_path)
        response.cache_control.max_age = 31536000  # 1 ano
        response.cache_control.public = True
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Erro ao servir asset {filename}: {str(e)}")
        abort(500)


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

        # TODO: Substituir por novo modelo quando necessário
        # Por enquanto, esta funcionalidade está sendo refatorada
        current_app.logger.warning("Funcionalidade de geração de documentos temporariamente desabilitada")
        return jsonify({
            "status": "temporariamente_indisponivel",
            "mensagem": "Esta funcionalidade está sendo atualizada"
        }), 503
        
        # Esta funcionalidade será implementada posteriormente
        # quando o novo modelo estiver disponível

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
                # TODO: Atualizar quando novo modelo estiver disponível
                resposta = None
                if resposta:
                    response_data["cliente_nome"] = "Cliente"
                    response_data["link_pasta_cliente"] = ""
                    response_data["documentos_gerados"] = []
                            
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


@main_bp.route("/health", methods=["GET"])
@limiter.exempt  # Health check não precisa de rate limiting
def health_check():
    """
    Endpoint de health check para monitoramento da aplicação.
    Verifica conectividade com banco de dados e status geral.
    """
    try:
        # Testa conexão com banco de dados
        db.session.execute("SELECT 1")
        db.session.commit()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "version": "1.0"
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }), 503
