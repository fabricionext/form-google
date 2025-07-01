"""
Rotas para conversão de documentos em templates utilizáveis.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services.template_converter import template_converter
# Service account authentication - no OAuth required
from app.utils.exceptions import (
    DocumentNotFoundException,
    ValidationException,
    TemplateServiceException
)
from app.extensions import limiter

logger = logging.getLogger(__name__)

# Blueprint para conversão de templates
template_conversion_bp = Blueprint('template_conversion', __name__, url_prefix='/api/template-conversion')


@template_conversion_bp.route('/convert/<document_id>', methods=['POST'])
@limiter.limit("5 per minute")
@login_required
def convert_document_to_template(document_id):
    """
    Converte um documento Google Docs em template utilizável.
    
    Args:
        document_id: ID do documento no Google Drive
        
    Request Body:
        {
            "template_name": "Nome do Template (opcional)",
            "template_category": "Categoria (opcional)",
            "auto_save": true
        }
        
    Returns:
        JSON com template convertido
    """
    try:
        user_id = str(current_user.id)
        data = request.get_json() or {}
        
        template_name = data.get('template_name')
        template_category = data.get('template_category')
        auto_save = data.get('auto_save', False)
        
        logger.info(f"Convertendo documento {document_id} em template para usuário {user_id}")
        
        # Converte documento
        converted_template = template_converter.convert_document_to_template(
            user_id=user_id,
            document_id=document_id,
            template_name=template_name,
            template_category=template_category
        )
        
        response_data = {
            'success': True,
            'template': {
                'id': converted_template.template_id,
                'name': converted_template.name,
                'description': converted_template.description,
                'category': converted_template.category,
                'fields': [
                    {
                        'name': field.name,
                        'label': field.label,
                        'type': field.type,
                        'category': field.category,
                        'required': field.required,
                        'description': field.description,
                        'options': field.options,
                        'placeholder': field.placeholder,
                        'validation_rules': field.validation_rules,
                        'default_value': field.default_value
                    }
                    for field in converted_template.fields
                ],
                'metadata': converted_template.metadata,
                'form_schema': converted_template.form_schema,
                'suitability_score': converted_template.suitability_score,
                'created_at': converted_template.created_at
            },
            'conversion_summary': {
                'total_fields': len(converted_template.fields),
                'field_categories': list(converted_template.form_schema['field_groups'].keys()),
                'required_fields': len([f for f in converted_template.fields if f.required]),
                'suitability_percentage': converted_template.suitability_score
            },
            'message': f'Template convertido com sucesso: {len(converted_template.fields)} campos criados'
        }
        
        # TODO: Implementar auto_save quando necessário
        if auto_save:
            logger.info(f"Auto-save solicitado para template {converted_template.template_id}")
            response_data['auto_saved'] = False
            response_data['auto_save_message'] = 'Funcionalidade de auto-save será implementada'
        
        logger.info(f"Conversão concluída: {len(converted_template.fields)} campos, score {converted_template.suitability_score:.1f}%")
        
        return jsonify(response_data), 200
        
    except DocumentNotFoundException as e:
        logger.warning(f"Documento não encontrado: {document_id}")
        return jsonify({
            'success': False,
            'error': 'document_not_found',
            'message': f'Documento {document_id} não foi encontrado'
        }), 404
        
    except ValidationException as e:
        logger.warning(f"Documento inadequado para template: {e}")
        return jsonify({
            'success': False,
            'error': 'document_unsuitable',
            'message': str(e),
            'field': e.field if hasattr(e, 'field') else None
        }), 400
        
    except TemplateServiceException as e:
        logger.error(f"Erro no serviço de template: {e}")
        return jsonify({
            'success': False,
            'error': 'template_service_error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Erro inesperado na conversão: {e}")
        return jsonify({
            'success': False,
            'error': 'conversion_error',
            'message': 'Erro interno na conversão'
        }), 500


@template_conversion_bp.route('/generate-instance', methods=['POST'])
@limiter.limit("20 per minute")
@login_required
def generate_document_instance():
    """
    Gera instância de documento a partir de template e dados do formulário.
    
    Request Body:
        {
            "document_id": "ID do documento original",
            "template_name": "Nome do template",
            "template_category": "Categoria",
            "form_data": {
                "campo1": "valor1",
                "campo2": "valor2"
            }
        }
        
    Returns:
        JSON com dados processados para geração
    """
    try:
        user_id = str(current_user.id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'invalid_request',
                'message': 'Dados JSON são obrigatórios'
            }), 400
        
        document_id = data.get('document_id')
        form_data = data.get('form_data', {})
        template_name = data.get('template_name')
        template_category = data.get('template_category')
        
        if not document_id:
            return jsonify({
                'success': False,
                'error': 'missing_document_id',
                'message': 'document_id é obrigatório'
            }), 400
        
        if not form_data:
            return jsonify({
                'success': False,
                'error': 'missing_form_data',
                'message': 'form_data é obrigatório'
            }), 400
        
        logger.info(f"Gerando instância de documento para template {document_id}")
        
        # Primeiro converte documento em template
        converted_template = template_converter.convert_document_to_template(
            user_id=user_id,
            document_id=document_id,
            template_name=template_name,
            template_category=template_category
        )
        
        # Depois cria instância com dados do formulário
        instance_data = template_converter.create_instance_from_template(
            converted_template=converted_template,
            form_data=form_data
        )
        
        return jsonify({
            'success': True,
            'instance': instance_data,
            'template_info': {
                'name': converted_template.name,
                'category': converted_template.category,
                'field_count': len(converted_template.fields)
            },
            'message': 'Instância de documento gerada com sucesso'
        }), 200
        
    except ValidationException as e:
        logger.warning(f"Dados de formulário inválidos: {e}")
        return jsonify({
            'success': False,
            'error': 'form_validation_error',
            'message': str(e),
            'field': e.field if hasattr(e, 'field') else None,
            'details': e.details if hasattr(e, 'details') else None
        }), 400
        
    except DocumentNotFoundException as e:
        logger.warning(f"Documento não encontrado: {e}")
        return jsonify({
            'success': False,
            'error': 'document_not_found',
            'message': str(e)
        }), 404
        
    except TemplateServiceException as e:
        logger.error(f"Erro no serviço de template: {e}")
        return jsonify({
            'success': False,
            'error': 'template_service_error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Erro inesperado na geração de instância: {e}")
        return jsonify({
            'success': False,
            'error': 'instance_generation_error',
            'message': 'Erro interno na geração de instância'
        }), 500


@template_conversion_bp.route('/preview-conversion/<document_id>', methods=['GET'])
@limiter.limit("10 per minute")
@login_required
def preview_template_conversion(document_id):
    """
    Faz preview da conversão sem executar totalmente.
    
    Args:
        document_id: ID do documento no Google Drive
        
    Returns:
        JSON com preview da conversão
    """
    try:
        user_id = str(current_user.id)
        
        logger.info(f"Fazendo preview de conversão para documento {document_id}")
        
        # Usa análise rápida primeiro
        from app.services.google_docs_analyzer import google_docs_analyzer
        analysis = google_docs_analyzer.analyze_document(user_id, document_id)
        
        # Cria preview baseado na análise
        preview_data = {
            'document_info': {
                'id': document_id,
                'name': analysis['metadata']['name'],
                'word_count': analysis['content']['word_count'],
                'character_count': analysis['content']['character_count']
            },
            'conversion_feasibility': {
                'suitable': analysis['suitable_for_template']['suitable'],
                'score': analysis['suitable_for_template']['score'],
                'percentage': analysis['suitable_for_template']['percentage'],
                'classification': analysis['suitable_for_template']['classification'],
                'reasons': analysis['suitable_for_template']['reasons'],
                'recommendations': analysis['suitable_for_template']['recommendations']
            },
            'expected_fields': {
                'total_placeholders': analysis['placeholders']['total_count'],
                'unique_placeholders': analysis['placeholders']['unique_count'],
                'categories': analysis['placeholders']['categories'],
                'field_types': analysis['placeholders']['types']
            },
            'preview_fields': [
                {
                    'name': placeholder['name'],
                    'category': placeholder['category'],
                    'type': placeholder['type'],
                    'required': placeholder['required'],
                    'description': placeholder['description']
                }
                for placeholder in analysis['placeholders']['placeholders'][:10]  # Primeiros 10
            ],
            'estimated_form_complexity': _estimate_form_complexity(analysis),
            'preview_generated_at': analysis['analysis_timestamp']
        }
        
        return jsonify({
            'success': True,
            'preview': preview_data,
            'message': f'Preview gerado: {preview_data["expected_fields"]["total_placeholders"]} campos detectados'
        }), 200
        
    except DocumentNotFoundException as e:
        logger.warning(f"Documento não encontrado: {document_id}")
        return jsonify({
            'success': False,
            'error': 'document_not_found',
            'message': f'Documento {document_id} não foi encontrado'
        }), 404
        
    except Exception as e:
        logger.error(f"Erro no preview de conversão: {e}")
        return jsonify({
            'success': False,
            'error': 'preview_error',
            'message': 'Erro ao gerar preview'
        }), 500


@template_conversion_bp.route('/validate-form-data', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def validate_template_form_data():
    """
    Valida dados de formulário contra schema de template.
    
    Request Body:
        {
            "form_schema": {...},
            "form_data": {...}
        }
        
    Returns:
        JSON com resultado da validação
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'invalid_request',
                'message': 'Dados JSON são obrigatórios'
            }), 400
        
        form_schema = data.get('form_schema')
        form_data = data.get('form_data')
        
        if not form_schema or not form_data:
            return jsonify({
                'success': False,
                'error': 'missing_data',
                'message': 'form_schema e form_data são obrigatórios'
            }), 400
        
        # Valida usando método do conversor
        validation_errors = template_converter._validate_form_data(form_schema, form_data)
        
        is_valid = len(validation_errors) == 0
        
        validation_result = {
            'valid': is_valid,
            'errors': validation_errors,
            'validated_fields': len(form_data),
            'required_fields_count': len(form_schema.get('required', [])),
            'validation_timestamp': logging.time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'success': True,
            'validation': validation_result,
            'message': 'Validação concluída' if is_valid else f'{len(validation_errors)} erros encontrados'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na validação de formulário: {e}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': 'Erro na validação'
        }), 500


def _estimate_form_complexity(analysis: dict) -> str:
    """
    Estima complexidade do formulário baseado na análise.
    
    Args:
        analysis: Análise do documento
        
    Returns:
        Classificação de complexidade
    """
    field_count = analysis['placeholders']['unique_count']
    category_count = len(analysis['placeholders']['categories'])
    
    if field_count <= 5 and category_count <= 2:
        return 'Simples'
    elif field_count <= 15 and category_count <= 4:
        return 'Moderado'
    elif field_count <= 30 and category_count <= 6:
        return 'Complexo'
    else:
        return 'Muito Complexo'