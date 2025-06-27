"""
Templates API Routes - Rotas completas para gerenciamento de templates
====================================================================

Endpoints para CRUD de templates, sincronização de placeholders e funcionalidades avançadas.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.api.controllers.template_controller import TemplateController
from app.security.decorators import permission_required, require_api_key
from app.config.constants import API_RATE_LIMITS

# Blueprint para templates
templates_bp = Blueprint('templates_api', __name__, url_prefix='/api/templates')

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Controller instance
template_controller = TemplateController()


@templates_bp.route('/', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('templates_list', "60/minute"))
@permission_required('templates:read')
def list_templates():
    """Lista templates com filtros e paginação."""
    try:
        # Parâmetros de consulta
        filters = {}
        
        # Filtros disponíveis
        if request.args.get('tipo'):
            filters['tipo'] = request.args.get('tipo')
        if request.args.get('categoria'):
            filters['categoria'] = request.args.get('categoria')
        if request.args.get('ativo'):
            filters['ativo'] = request.args.get('ativo').lower() == 'true'
        if request.args.get('search'):
            filters['search'] = request.args.get('search')
        
        # Paginação
        pagination = {
            'page': int(request.args.get('page', 1)),
            'per_page': min(int(request.args.get('per_page', 20)), 100)
        }
        
        result = template_controller.list_templates(filters, pagination)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota list_templates: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@templates_bp.route('/<int:template_id>', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('templates_get', "120/minute"))
@permission_required('templates:read')
def get_template(template_id: int):
    """Busca template por ID com placeholders."""
    try:
        result = template_controller.get_template(template_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_template: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@templates_bp.route('/', methods=['POST'])
@limiter.limit(API_RATE_LIMITS.get('templates_create', "10/minute"))
@permission_required('templates:create')
def create_template():
    """Cria novo template."""
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
        
        # Adicionar ID do usuário criador
        data['created_by'] = getattr(request, 'user_id', None)
        
        result = template_controller.create_template(data)
        return jsonify(result), result.get('status_code', 201)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota create_template: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@templates_bp.route('/<int:template_id>', methods=['PUT'])
@limiter.limit(API_RATE_LIMITS.get('templates_update', "20/minute"))
@permission_required('templates:update')
def update_template(template_id: int):
    """Atualiza template existente."""
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
        
        # Adicionar ID do usuário que fez a atualização
        data['updated_by'] = getattr(request, 'user_id', None)
        
        result = template_controller.update_template(template_id, data)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota update_template: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@templates_bp.route('/<int:template_id>', methods=['DELETE'])
@limiter.limit(API_RATE_LIMITS.get('templates_delete', "5/minute"))
@permission_required('templates:delete')
def delete_template(template_id: int):
    """Remove template (soft delete)."""
    try:
        result = template_controller.delete_template(template_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota delete_template: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@templates_bp.route('/<int:template_id>/sync-placeholders', methods=['POST'])
@limiter.limit(API_RATE_LIMITS.get('templates_sync', "5/minute"))
@permission_required('templates:sync')
def sync_placeholders(template_id: int):
    """Sincroniza placeholders do Google Docs."""
    try:
        result = template_controller.sync_placeholders(template_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota sync_placeholders: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@templates_bp.route('/<int:template_id>/preview', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('templates_preview', "30/minute"))
@permission_required('templates:read')
def get_template_preview(template_id: int):
    """Gera preview do template com dados fictícios."""
    try:
        result = template_controller.get_template_preview(template_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_template_preview: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@templates_bp.route('/<int:template_id>/statistics', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('templates_stats', "20/minute"))
@permission_required('templates:read')
def get_template_statistics(template_id: int):
    """Retorna estatísticas de uso do template."""
    try:
        result = template_controller.get_template_statistics(template_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_template_statistics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@templates_bp.route('/categories', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('templates_list', "60/minute"))
@permission_required('templates:read')
def list_categories():
    """Lista categorias disponíveis de templates."""
    try:
        # Categorias fixas (podem vir do banco posteriormente)
        categories = [
            {
                'id': 'peticoes',
                'name': 'Petições',
                'description': 'Templates para petições judiciais'
            },
            {
                'id': 'contratos',
                'name': 'Contratos',
                'description': 'Templates para contratos diversos'
            },
            {
                'id': 'procuracoes',
                'name': 'Procurações',
                'description': 'Templates para procurações'
            },
            {
                'id': 'recursos',
                'name': 'Recursos',
                'description': 'Templates para recursos judiciais'
            },
            {
                'id': 'outros',
                'name': 'Outros',
                'description': 'Outros tipos de documentos'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': {'categories': categories},
            'message': 'Categorias obtidas com sucesso'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota list_categories: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@templates_bp.route('/types', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('templates_list', "60/minute"))
@permission_required('templates:read')
def list_types():
    """Lista tipos disponíveis de templates."""
    try:
        # Tipos baseados no FORM_CONFIG
        from app.config.constants import FORM_CONFIG
        
        types = []
        for type_key, type_info in FORM_CONFIG.get('TEMPLATE_TYPES', {}).items():
            types.append({
                'id': type_key,
                'name': type_info.get('name', type_key),
                'description': type_info.get('description', ''),
                'icon': type_info.get('icon', 'document')
            })
        
        return jsonify({
            'success': True,
            'data': {'types': types},
            'message': 'Tipos obtidos com sucesso'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota list_types: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


# Registro de handlers de erro
@templates_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': 'Requisição inválida'
    }), 400


@templates_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'message': 'Não autorizado'
    }), 401


@templates_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'message': 'Acesso negado'
    }), 403


@templates_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Template não encontrado'
    }), 404


@templates_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'message': 'Limite de requisições excedido'
    }), 429 