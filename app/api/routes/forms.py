"""
Forms API Routes - Rotas completas para formulários dinâmicos
============================================================

Endpoints para geração de schemas, validação e processamento de formulários dinâmicos.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.api.controllers.form_controller import FormController
from app.security.decorators import permission_required, require_api_key
from app.config.constants import API_RATE_LIMITS

# Blueprint para forms
forms_bp = Blueprint('forms_api', __name__, url_prefix='/api/forms')

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Controller instance
form_controller = FormController()


@forms_bp.route('/<int:template_id>/schema', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('forms_schema', "60/minute"))
@permission_required('forms:read')
def get_form_schema(template_id: int):
    """Gera schema do formulário baseado no template."""
    try:
        result = form_controller.get_form_schema(template_id)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_form_schema: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/<int:template_id>/validate', methods=['POST'])
@limiter.limit(API_RATE_LIMITS.get('forms_validate', "120/minute"))
@permission_required('forms:validate')
def validate_form_data(template_id: int):
    """Valida dados do formulário contra o schema do template."""
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
        
        result = form_controller.validate_form_data(template_id, data)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota validate_form_data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/<int:template_id>/validate-field', methods=['POST'])
@limiter.limit(API_RATE_LIMITS.get('forms_validate_field', "200/minute"))
@permission_required('forms:validate')
def validate_field(template_id: int):
    """Valida campo individual em tempo real."""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type deve ser application/json'
            }), 400
        
        data = request.get_json()
        field_name = data.get('field_name')
        field_value = data.get('field_value')
        
        if not field_name:
            return jsonify({
                'success': False,
                'message': 'field_name é obrigatório'
            }), 400
        
        result = form_controller.validate_field(template_id, field_name, field_value)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota validate_field: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/<int:template_id>/field-suggestions', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('forms_suggestions', "120/minute"))
@permission_required('forms:read')
def get_field_suggestions(template_id: int):
    """Retorna sugestões para autocomplete de campo."""
    try:
        field_name = request.args.get('field_name')
        query = request.args.get('query', '')
        
        if not field_name:
            return jsonify({
                'success': False,
                'message': 'field_name é obrigatório'
            }), 400
        
        result = form_controller.get_field_suggestions(template_id, field_name, query)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_field_suggestions: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/<int:template_id>/conditional-fields', methods=['POST'])
@limiter.limit(API_RATE_LIMITS.get('forms_conditional', "60/minute"))
@permission_required('forms:read')
def get_conditional_fields(template_id: int):
    """Retorna campos que devem ser exibidos baseado nos dados atuais."""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type deve ser application/json'
            }), 400
        
        current_data = request.get_json() or {}
        
        result = form_controller.get_conditional_fields(template_id, current_data)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_conditional_fields: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/<int:template_id>/submit', methods=['POST'])
@limiter.limit(API_RATE_LIMITS.get('forms_submit', "20/minute"))
@permission_required('forms:submit')
def process_form_submission(template_id: int):
    """Processa submissão completa do formulário."""
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
        
        result = form_controller.process_form_submission(template_id, data)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota process_form_submission: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/templates', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('forms_templates', "60/minute"))
@permission_required('forms:read')
def get_form_templates():
    """Lista templates disponíveis para formulários."""
    try:
        category = request.args.get('category')
        
        result = form_controller.get_form_templates(category)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_form_templates: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/<int:template_id>/field/<string:field_name>/metadata', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('forms_metadata', "60/minute"))
@permission_required('forms:read')
def get_field_metadata(template_id: int, field_name: str):
    """Retorna metadados detalhados de um campo."""
    try:
        result = form_controller.get_field_metadata(template_id, field_name)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_field_metadata: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/<int:template_id>/field/<string:field_name>/config', methods=['PUT'])
@limiter.limit(API_RATE_LIMITS.get('forms_config', "10/minute"))
@permission_required('forms:admin')
def update_field_configuration(template_id: int, field_name: str):
    """Atualiza configuração de um campo (apenas admins)."""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'message': 'Content-Type deve ser application/json'
            }), 400
        
        config = request.get_json()
        if not config:
            return jsonify({
                'success': False,
                'message': 'Configuração não fornecida'
            }), 400
        
        result = form_controller.update_field_configuration(template_id, field_name, config)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota update_field_configuration: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/<int:template_id>/export', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('forms_export', "10/minute"))
@permission_required('forms:read')
def export_form_schema(template_id: int):
    """Exporta schema do formulário em diferentes formatos."""
    try:
        format = request.args.get('format', 'json')
        
        result = form_controller.export_form_schema(template_id, format)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota export_form_schema: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/<int:template_id>/analytics', methods=['GET'])
@limiter.limit(API_RATE_LIMITS.get('forms_analytics', "20/minute"))
@permission_required('forms:analytics')
def get_form_analytics(template_id: int):
    """Retorna analytics de uso do formulário."""
    try:
        period = request.args.get('period', '30d')
        
        result = form_controller.get_form_analytics(template_id, period)
        return jsonify(result), result.get('status_code', 200)
        
    except Exception as e:
        current_app.logger.error(f"Erro na rota get_form_analytics: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Erro interno do servidor'
        }), 500


@forms_bp.route('/health', methods=['GET'])
@limiter.limit("30/minute")
def health_check():
    """Health check para o serviço de formulários."""
    try:
        return jsonify({
            'success': True,
            'service': 'forms_api',
            'status': 'healthy',
            'timestamp': current_app.config.get('SERVER_TIME_ZONE', 'UTC')
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro no health check: {str(e)}")
        return jsonify({
            'success': False,
            'service': 'forms_api',
            'status': 'unhealthy',
            'error': str(e)
        }), 500


# Registro de handlers de erro
@forms_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'message': 'Requisição inválida'
    }), 400


@forms_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'success': False,
        'message': 'Não autorizado'
    }), 401


@forms_bp.errorhandler(403)
def forbidden(error):
    return jsonify({
        'success': False,
        'message': 'Acesso negado'
    }), 403


@forms_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Recurso não encontrado'
    }), 404


@forms_bp.errorhandler(422)
def unprocessable_entity(error):
    return jsonify({
        'success': False,
        'message': 'Dados não processáveis'
    }), 422


@forms_bp.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({
        'success': False,
        'message': 'Limite de requisições excedido'
    }), 429 