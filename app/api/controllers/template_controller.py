#!/usr/bin/env python3
"""
Template Controller - Integração com ENUMs Fase 1.5.2
Implementação para fazer testes TDD passarem (Green phase)
"""

from typing import Dict, Any, List, Optional
from flask import request, jsonify
from sqlalchemy.exc import IntegrityError
from app.models.enums import FieldType, TemplateStatus, EnumValidator
from app.models.document_template import DocumentTemplate
from app.models.template_placeholder import TemplatePlaceholder
from app.extensions import db
import logging

logger = logging.getLogger(__name__)

class TemplateController:
    """
    Controller para Templates com integração de ENUMs.
    Segue padrões REST e valida usando ENUMs da Fase 1.5.2.
    """
    
    def create_template(self) -> Dict[str, Any]:
        """
        Criar novo template validando ENUMs.
        POST /api/templates/
        """
        try:
            data = request.get_json()
            
            # Validar dados obrigatórios
            if not data or 'name' not in data:
                return {'error': 'Template name is required'}, 400
            
            # Validar status se fornecido
            status = data.get('status', TemplateStatus.DRAFT.value)
            if not EnumValidator.validate_template_status(status):
                return {'error': f'Invalid template status: {status}'}, 400
            
            # Validar campos se fornecidos
            fields = data.get('fields', [])
            for field in fields:
                if 'type' in field:
                    field_type = field['type']
                    if not EnumValidator.validate_field_type(field_type):
                        return {'error': f'Invalid field type: {field_type}'}, 400
            
            # Criar template
            template = DocumentTemplate(
                name=data['name'],
                description=data.get('description', ''),
                status=status,
                is_active=True
            )
            
            db.session.add(template)
            db.session.flush()  # Para obter ID
            
            # Criar placeholders para cada campo
            for i, field in enumerate(fields):
                placeholder = TemplatePlaceholder(
                    template_id=template.id,
                    name=field['name'],
                    label=field.get('label', field['name']),
                    field_type=field['type'],
                    required=field.get('required', False),
                    field_order=field.get('order', i + 1)
                )
                db.session.add(placeholder)
            
            db.session.commit()
            
            # Retornar template criado
            result = self._serialize_template(template)
            logger.info(f"Template created: {template.id}")
            
            return result, 201
            
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Integrity error creating template: {e}")
            return {'error': 'Template name already exists'}, 400
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating template: {e}")
            return {'error': 'Internal server error'}, 500
    
    def get_template(self, template_id: int) -> Dict[str, Any]:
        """
        Obter template específico.
        GET /api/templates/<id>
        """
        try:
            template = DocumentTemplate.query.get(template_id)
            if not template:
                return {'error': 'Template not found'}, 404
            
            result = self._serialize_template(template)
            return result, 200
            
        except Exception as e:
            logger.error(f"Error getting template {template_id}: {e}")
            return {'error': 'Internal server error'}, 500
    
    def list_templates(self) -> Dict[str, Any]:
        """
        Listar templates com filtros opcionais.
        GET /api/templates/
        """
        try:
            # Parâmetros de filtro
            status_filter = request.args.get('status')
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            
            # Query base
            query = DocumentTemplate.query.filter_by(is_active=True)
            
            # Filtrar por status se fornecido
            if status_filter:
                if not EnumValidator.validate_template_status(status_filter):
                    return {'error': f'Invalid status filter: {status_filter}'}, 400
                query = query.filter_by(status=status_filter)
            
            # Paginação
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            # Serializar templates
            templates = [
                self._serialize_template(template) 
                for template in pagination.items
            ]
            
            result = {
                'templates': templates,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
            
            return result, 200
            
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return {'error': 'Internal server error'}, 500
    
    def update_template_status(self, template_id: int) -> Dict[str, Any]:
        """
        Atualizar status do template validando transições.
        PATCH /api/templates/<id>/status
        """
        try:
            data = request.get_json()
            new_status = data.get('status')
            
            if not new_status:
                return {'error': 'Status is required'}, 400
            
            if not EnumValidator.validate_template_status(new_status):
                return {'error': f'Invalid status: {new_status}'}, 400
            
            template = DocumentTemplate.query.get(template_id)
            if not template:
                return {'error': 'Template not found'}, 404
            
            # Validar transição de status
            current_status = TemplateStatus(template.status)
            new_status_enum = TemplateStatus(new_status)
            
            if not EnumValidator.validate_status_transition(
                current_status.value, new_status_enum.value, 'template'
            ):
                return {
                    'error': f'Invalid status transition: {current_status.value} → {new_status}'
                }, 400
            
            # Atualizar status
            template.status = new_status
            db.session.commit()
            
            result = self._serialize_template(template)
            logger.info(f"Template {template_id} status updated to {new_status}")
            
            return result, 200
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating template status: {e}")
            return {'error': 'Internal server error'}, 500
    
    def _serialize_template(self, template: DocumentTemplate) -> Dict[str, Any]:
        """
        Serializar template para JSON com ENUMs.
        """
        # Obter placeholders/campos
        placeholders = TemplatePlaceholder.query.filter_by(
            template_id=template.id
        ).order_by(TemplatePlaceholder.field_order).all()
        
        fields = [
            {
                'id': p.id,
                'name': p.name,
                'label': p.label,
                'type': p.field_type,
                'required': p.required,
                'order': p.field_order
            }
            for p in placeholders
        ]
        
        return {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'status': template.status,
            'fields': fields,
            'created_at': template.created_at.isoformat() if template.created_at else None,
            'updated_at': template.updated_at.isoformat() if template.updated_at else None
        }

class EnumInfoController:
    """
    Controller para fornecer informações sobre ENUMs disponíveis.
    """
    
    def get_field_types(self) -> Dict[str, Any]:
        """
        Obter tipos de campo disponíveis.
        GET /api/field-types/
        """
        try:
            field_types = [
                {
                    'value': field_type.value,
                    'label': label
                }
                for field_type, label in zip(
                    FieldType,
                    ['Texto', 'E-mail', 'Número', 'Data', 'Seleção', 
                     'Seleção Múltipla', 'Área de Texto', 'Checkbox', 'Arquivo']
                )
            ]
            
            return field_types, 200
            
        except Exception as e:
            logger.error(f"Error getting field types: {e}")
            return {'error': 'Internal server error'}, 500
    
    def get_template_statuses(self) -> Dict[str, Any]:
        """
        Obter status de template disponíveis.
        GET /api/template-statuses/
        """
        try:
            statuses = [
                {
                    'value': status.value,
                    'label': label
                }
                for status, label in zip(
                    TemplateStatus,
                    ['Rascunho', 'Em Revisão', 'Publicado', 'Arquivado']
                )
            ]
            
            return statuses, 200
            
        except Exception as e:
            logger.error(f"Error getting template statuses: {e}")
            return {'error': 'Internal server error'}, 500 