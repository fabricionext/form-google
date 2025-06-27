"""
Documents API Routes - Rotas completas para gerenciamento de documentos
======================================================================

Endpoints para geração, monitoramento e gestão de documentos gerados.
"""

from flask import Blueprint, request, jsonify, current_app, redirect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.api.controllers.document_controller import DocumentController
from app.security.decorators import permission_required, require_api_key
from app.config.constants import API_RATE_LIMITS

# Blueprint para documents
documents_bp = Blueprint('documents_api', __name__, url_prefix='/api/documents')

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Controller instance
document_controller = DocumentController()


@documents_bp.route('/generate/<int:template_id>', methods=['POST'])
@limiter.limit(API_RATE_LIMITS.get('documents_generate', "10/minute"))
@permission_required('documents:create')
def generate_document(template_id: int):
    """Inicia geração de documento (processamento assíncrono)."""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type deve ser application/json'
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados não fornecidos'
            }), 400
        
        result = document_controller.generate_document(template_id, data)
        return jsonify(result), result.get('status_code', 202)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota generate_document: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/status/<string:task_id>', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('documents_status', "120/minute"))
@permission_required('documents:read')
def get_document_status(task_id: str):
    """Consulta status da geração de documento."""
    try:
        result = document_controller.get_document_status(task_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_document_status: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('documents_list', "60/minute"))
@permission_required('documents:read')
def list_documents():
    """Lista documentos gerados com filtros."""
    try:
        # Parâmetros de consulta
        filters = {}
        
        # Filtros disponíveis
        if request.args.get('status'):
            filters['status'] = request.args.get('status')
        if request.args.get('template_id'):
            filters['template_id'] = int(request.args.get('template_id'))
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        # Paginação
        pagination = {
            'page': int(request.args.get('page', 1)),
            'per_page': min(int(request.args.get('per_page', 20)), 100)
        }
        
        result = document_controller.list_documents(filters, pagination)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota list_documents: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/<int:document_id>', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('documents_get', "120/minute"))
@permission_required('documents:read')
def get_document(document_id: int):
    """Busca documento por ID."""
    try:
        result = document_controller.get_document(document_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_document: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/<int:document_id>/download', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('documents_download', "30/minute"))
@permission_required('documents:download')
def download_document(document_id: int):
    """Download do documento gerado."""
    try:
        result = document_controller.download_document(document_id)
        
        # Se for redirect, fazer redirect
        if isinstance(result, dict) and 'redirect_url' in result:
            return redirect(result['redirect_url'])
        
        # Se for arquivo direto, já é retornado pelo controller
        return result
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota download_document: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/<int:document_id>/regenerate', methods=['POST'])
@limiter.limit(API_RATE_LIMITS.get('documents_regenerate', "5/minute"))
@permission_required('documents:create')
def regenerate_document(document_id: int):
    """Regenera documento com dados atualizados."""
    try:
        data = request.get_json() if request.is_json else None
        
        result = document_controller.regenerate_document(document_id, data)
        return jsonify(result), result.get('status_code', 202)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota regenerate_document: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/<int:document_id>', methods=['DELETE'])
@limiter.limit(API_RATE_LIMITS.get('documents_delete', "10/minute"))
@permission_required('documents:delete')
def delete_document(document_id: int):
    """Remove documento (soft delete)."""
    try:
        result = document_controller.delete_document(document_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota delete_document: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/history', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('documents_history', "30/minute"))
@permission_required('documents:read')
def get_generation_history():
    """Retorna histórico de gerações."""
    try:
        template_id = request.args.get('template_id', type=int)
        user_id = request.args.get('user_id', type=int)
        
        result = document_controller.get_generation_history(template_id, user_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_generation_history: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/statistics', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('documents_stats', "20/minute"))
@permission_required('documents:admin')
def get_document_statistics():
    """Retorna estatísticas gerais de documentos."""
    try:
        result = document_controller.get_document_statistics()
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_document_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/statuses', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('documents_list', "60/minute"))
@permission_required('documents:read')
def list_document_statuses():
    """Lista possíveis status de documentos."""
    try:
        statuses = [
            {
                'id': 'queued',
                'name': 'Na Fila',
                'description': 'Aguardando processamento'
            },
            {
                'id': 'processing',
                'name': 'Processando',
                'description': 'Gerando documento'
            },
            {
                'id': 'completed',
                'name': 'Concluído',
                'description': 'Documento gerado com sucesso'
            },
            {
                'id': 'failed',
                'name': 'Falhou',
                'description': 'Erro na geração'
            },
            {
                'id': 'cancelled',
                'name': 'Cancelado',
                'description': 'Geração cancelada'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {'statuses': statuses},
            'message': 'Status obtidos com sucesso'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota list_document_statuses: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@documents_bp.route('/health', methods=['GET'])
@limiter.limit("30/minute")
def health_check():
    """Health check para o serviço de documentos."""
    try:
        return jsonify({
            'success': True,
            'service': 'documents_api',
            'status': 'healthy',
            'timestamp': current_app.config.get('SERVER_TIME_ZONE', 'UTC')
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no health check: {str(e)}")
        return jsonify({
            'success': False,
            'service': 'documents_api',
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# Registro de handlers de erro
@documents_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': 'Requisição inválida'
    }), 400


@documents_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'message': 'Não autorizado'
    }), 401


@documents_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'message': 'Acesso negado'
    }), 403


@documents_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Documento não encontrado'
    }), 404


@documents_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'message': 'Limite de requisições excedido'
    }), 429 