"""
APIs Administrativas - Protegidas por JWT
========================================

Endpoints que exigem autenticação JWT:
- Gerenciamento de modelos
- Dashboard administrativo
- Formulários e configurações
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from pydantic import ValidationError
import logging
from datetime import datetime
from uuid import UUID

from app.extensions import db, limiter
from app.models.document_template import DocumentTemplate
from app.schemas.document_schema import (
    DocumentTemplateSchema,
    DocumentTemplateListSchema,
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
)
from app.config.jwt_config import require_role

admin_bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')
logger = logging.getLogger(__name__)

@admin_bp.route('/templates', methods=['GET'])
@jwt_required()
@limiter.limit("100 per minute")
def list_templates():
    """Listar templates de documentos com filtros e paginação."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', None, type=str)
        category = request.args.get('category', None, type=str)
        status = request.args.get('status', None, type=str)

        query = DocumentTemplate.query

        if search:
            query = query.filter(DocumentTemplate.name.ilike(f'%{search}%'))
        if category:
            query = query.filter_by(category=category)
        if status:
            query = query.filter_by(status=status)

        pagination = query.order_by(DocumentTemplate.updated_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        templates = pagination.items
        result = [DocumentTemplateListSchema.from_orm(t).dict() for t in templates]

        return jsonify({
            "templates": result,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
        })
    except Exception as e:
        logger.error(f"Erro ao listar templates: {e}", exc_info=True)
        return jsonify({"message": "Erro interno ao buscar templates"}), 500

@admin_bp.route('/templates', methods=['POST'])
@require_role('editor')
def create_template():
    """Cria um novo template de documento."""
    try:
        data = DocumentTemplateCreate(**request.json)
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 422

    new_template = DocumentTemplate(**data.dict())
    
    db.session.add(new_template)
    db.session.commit()
    db.session.refresh(new_template)
    
    return jsonify(DocumentTemplateSchema.from_orm(new_template).dict()), 201

@admin_bp.route('/templates/<uuid:template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id: UUID):
    """Obtém os detalhes de um template."""
    template = db.session.get(DocumentTemplate, template_id)
    if not template:
        return jsonify({"message": "Template não encontrado"}), 404
    return jsonify(DocumentTemplateSchema.from_orm(template).dict())

@admin_bp.route('/templates/<uuid:template_id>', methods=['PUT'])
@require_role('editor')
def update_template(template_id: UUID):
    """Atualiza um template de documento."""
    template = db.session.get(DocumentTemplate, template_id)
    if not template:
        return jsonify({"message": "Template não encontrado"}), 404
        
    try:
        update_data = DocumentTemplateUpdate(**request.json)
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 422

    update_values = update_data.dict(exclude_unset=True)
    for field, value in update_values.items():
        setattr(template, field, value)

    db.session.commit()
    db.session.refresh(template)

    return jsonify(DocumentTemplateSchema.from_orm(template).dict())

@admin_bp.route('/templates/<uuid:template_id>', methods=['DELETE'])
@require_role('admin')
def delete_template(template_id: UUID):
    """Deleta um template de documento."""
    template = db.session.get(DocumentTemplate, template_id)
    if not template:
        return jsonify({"message": "Template não encontrado"}), 404
        
    db.session.delete(template)
    db.session.commit()
    
    return jsonify({"message": "Template deletado com sucesso"}), 200

@admin_bp.route('/templates/<uuid:template_id>/sync', methods=['POST'])
@require_role('editor')
@limiter.limit("10 per hour")
def sync_template(template_id: UUID):
    """Sincroniza um template com o Google Drive (simulação)."""
    template = db.session.get(DocumentTemplate, template_id)
    if not template:
        return jsonify({'message': 'Template não encontrado'}), 404
    
    # Mock de campos detectados
    detected_fields = ["nome_cliente", "cpf", "numero_processo", "vara_judicial"]
    
    template.detected_fields = detected_fields
    template.last_sync = datetime.utcnow()
    db.session.commit()
    
    return jsonify(DocumentTemplateSchema.from_orm(template).dict())

@admin_bp.route('/templates/<uuid:template_id>/duplicate', methods=['POST'])
@require_role('editor')
@limiter.limit("20 per hour")
def duplicate_template(template_id: UUID):
    """Duplica um template."""
    original = db.session.get(DocumentTemplate, template_id)
    if not original:
        return jsonify({'message': 'Template não encontrado'}), 404

    new_template = DocumentTemplate(
        name=f"{original.name} (Cópia)",
        description=original.description,
        category=original.category,
        google_doc_id=original.google_doc_id,
        pasta_destino_id=original.pasta_destino_id,
        status='draft'
    )

    db.session.add(new_template)
    db.session.commit()
    db.session.refresh(new_template)
    
    return jsonify(DocumentTemplateSchema.from_orm(new_template).dict()), 201

@admin_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
@limiter.limit("60 per minute")
def dashboard_stats():
    """Retorna estatísticas para o dashboard administrativo."""
    try:
        total_templates = db.session.query(DocumentTemplate.id).count()
        active_templates = DocumentTemplate.query.filter_by(status='active').count()
        
        recent_templates = DocumentTemplate.query.order_by(
            DocumentTemplate.updated_at.desc()
        ).limit(5).all()

        return jsonify({
            'stats': {
                'total_templates': total_templates,
                'active_templates': active_templates,
            },
            'recent_templates': [DocumentTemplateListSchema.from_orm(t).dict() for t in recent_templates]
        })
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas do dashboard: {e}", exc_info=True)
        return jsonify({'message': 'Erro ao buscar estatísticas'}), 500

# Error handlers específicos para este blueprint
@admin_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handler para erros de validação."""
    return jsonify({
        'error': 'Dados inválidos',
        'message': 'Os dados enviados são inválidos.',
        'details': e.errors()
    }), 400

@admin_bp.errorhandler(403)
def handle_forbidden_error(e):
    """Handler para erros de permissão."""
    return jsonify({
        'error': 'Acesso negado',
        'message': 'Você não tem permissão para acessar este recurso.'
    }), 403 