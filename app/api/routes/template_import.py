"""
Rotas para importação real de templates do Google Drive.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services.google_service_account import google_service_account
from app.services.google_docs_analyzer import google_docs_analyzer
from app.services.template_converter import template_converter
from app.services.cache_service import document_cache
from app.utils.exceptions import (
    DocumentNotFoundException,
    GoogleDriveException,
    ValidationException,
    TemplateServiceException
)
from app.extensions import limiter

logger = logging.getLogger(__name__)

# Blueprint para importação de templates
template_import_bp = Blueprint('template_import', __name__, url_prefix='/api/import')


@template_import_bp.route('/search-documents', methods=['GET'])
@limiter.limit("10 per minute")
@login_required
def search_google_documents():
    """
    Busca documentos Google Docs disponíveis para importação.
    
    Query Parameters:
        q: Termo de busca (opcional)
        max_results: Máximo de resultados (padrão: 20, máximo: 50)
        
    Returns:
        JSON com documentos encontrados
    """
    try:
        query = request.args.get('q', '')
        max_results = min(int(request.args.get('max_results', 20)), 50)
        
        logger.info(f"Buscando documentos Google Docs para usuário {current_user.id}")
        
        if query:
            # Busca com termo específico
            search_result = google_service_account.search_documents(query, max_results)
        else:
            # Lista documentos recentes (usando busca vazia)
            search_result = google_service_account.search_documents('', max_results)
        
        if not search_result['success']:
            return jsonify({
                'success': False,
                'error': 'search_failed',
                'message': search_result.get('error', 'Falha na busca')
            }), 503
        
        documents = search_result['documents']
        
        # Enriquece com informações de cache se disponível
        enriched_documents = []
        for doc in documents:
            doc_info = {
                'id': doc['id'],
                'name': doc['name'],
                'modified_time': doc.get('modifiedTime'),
                'created_time': doc.get('createdTime'),
                'size': doc.get('size'),
                'owners': doc.get('owners', []),
                'mime_type': doc.get('mimeType')
            }
            
            # Verifica se já tem análise em cache
            cached_analysis = document_cache.get_analysis(doc['id'])
            if cached_analysis:
                doc_info['cached_analysis'] = {
                    'available': True,
                    'placeholder_count': cached_analysis.get('placeholders', {}).get('total_count', 0),
                    'suitability_score': cached_analysis.get('suitable_for_template', {}).get('percentage', 0)
                }
            else:
                doc_info['cached_analysis'] = {'available': False}
            
            # Verifica se já tem template em cache
            cached_template = document_cache.get_template(doc['id'])
            if cached_template:
                doc_info['cached_template'] = {
                    'available': True,
                    'field_count': len(cached_template.get('fields', [])),
                    'category': cached_template.get('category', 'Desconhecida')
                }
            else:
                doc_info['cached_template'] = {'available': False}
            
            enriched_documents.append(doc_info)
        
        return jsonify({
            'success': True,
            'search_query': query,
            'documents': enriched_documents,
            'total_found': len(enriched_documents),
            'max_results': max_results,
            'message': f'{len(enriched_documents)} documentos encontrados'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na busca de documentos: {e}")
        return jsonify({
            'success': False,
            'error': 'search_error',
            'message': 'Erro interno na busca'
        }), 500


@template_import_bp.route('/preview/<document_id>', methods=['POST'])
@limiter.limit("5 per minute")
@login_required
def preview_document_import(document_id):
    """
    Faz preview de importação de um documento específico.
    
    Args:
        document_id: ID do documento no Google Drive
        
    Request Body:
        {
            "template_name": "Nome personalizado (opcional)",
            "template_category": "Categoria personalizada (opcional)"
        }
        
    Returns:
        JSON com preview da importação
    """
    try:
        user_id = str(current_user.id)
        data = request.get_json() or {}
        
        template_name = data.get('template_name')
        template_category = data.get('template_category')
        
        logger.info(f"Preview de importação do documento {document_id} para usuário {user_id}")
        
        # Primeiro faz análise completa
        analysis = google_docs_analyzer.analyze_document(user_id, document_id)
        
        # Depois faz conversão para template
        converted_template = template_converter.convert_document_to_template(
            user_id=user_id,
            document_id=document_id,
            template_name=template_name,
            template_category=template_category
        )
        
        # Gera preview detalhado
        preview_data = {
            'document_info': {
                'id': document_id,
                'name': analysis['metadata']['name'],
                'word_count': analysis['content']['word_count'],
                'character_count': analysis['content']['character_count'],
                'paragraph_count': analysis['content']['paragraph_count']
            },
            'template_preview': {
                'name': converted_template.name,
                'description': converted_template.description,
                'category': converted_template.category,
                'field_count': len(converted_template.fields),
                'suitability_score': converted_template.suitability_score,
                'suitability_classification': analysis['suitable_for_template']['classification']
            },
            'fields_preview': [
                {
                    'name': field.name,
                    'label': field.label,
                    'type': field.type,
                    'category': field.category,
                    'required': field.required,
                    'description': field.description,
                    'has_options': field.options is not None,
                    'has_validation': field.validation_rules is not None
                }
                for field in converted_template.fields[:10]  # Primeiros 10 campos
            ],
            'import_recommendations': analysis['suitable_for_template']['recommendations'],
            'form_complexity': self._assess_form_complexity(converted_template),
            'estimated_completion_time': self._estimate_completion_time(converted_template)
        }
        
        return jsonify({
            'success': True,
            'preview': preview_data,
            'can_import': analysis['suitable_for_template']['suitable'],
            'message': f'Preview gerado: {len(converted_template.fields)} campos detectados'
        }), 200
        
    except DocumentNotFoundException:
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
            'can_import': False
        }), 400
        
    except Exception as e:
        logger.error(f"Erro no preview de importação: {e}")
        return jsonify({
            'success': False,
            'error': 'preview_error',
            'message': 'Erro interno no preview'
        }), 500


@template_import_bp.route('/import/<document_id>', methods=['POST'])
@limiter.limit("3 per minute")
@login_required
def import_document_as_template(document_id):
    """
    Importa um documento como template utilizável.
    
    Args:
        document_id: ID do documento no Google Drive
        
    Request Body:
        {
            "template_name": "Nome do template",
            "template_category": "Categoria",
            "save_to_database": true,
            "generate_form_preview": true
        }
        
    Returns:
        JSON com template importado
    """
    try:
        user_id = str(current_user.id)
        data = request.get_json() or {}
        
        template_name = data.get('template_name')
        template_category = data.get('template_category')
        save_to_database = data.get('save_to_database', False)
        generate_form_preview = data.get('generate_form_preview', True)
        
        if not template_name:
            return jsonify({
                'success': False,
                'error': 'missing_template_name',
                'message': 'Nome do template é obrigatório'
            }), 400
        
        logger.info(f"Importando documento {document_id} como template '{template_name}' para usuário {user_id}")
        
        # Converte documento em template
        converted_template = template_converter.convert_document_to_template(
            user_id=user_id,
            document_id=document_id,
            template_name=template_name,
            template_category=template_category
        )
        
        # Prepara resposta
        import_result = {
            'template': {
                'id': converted_template.template_id,
                'name': converted_template.name,
                'description': converted_template.description,
                'category': converted_template.category,
                'field_count': len(converted_template.fields),
                'suitability_score': converted_template.suitability_score,
                'created_at': converted_template.created_at,
                'metadata': converted_template.metadata
            },
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
            'import_summary': {
                'source_document': document_id,
                'total_fields': len(converted_template.fields),
                'required_fields': len([f for f in converted_template.fields if f.required]),
                'field_categories': list(converted_template.form_schema['field_groups'].keys()),
                'form_complexity': self._assess_form_complexity(converted_template)
            }
        }
        
        # Gera preview do formulário se solicitado
        if generate_form_preview:
            import_result['form_preview'] = {
                'schema': converted_template.form_schema,
                'field_groups': converted_template.form_schema['field_groups'],
                'required_fields': converted_template.form_schema['required']
            }
        
        # TODO: Implementar salvamento no banco de dados
        if save_to_database:
            import_result['database_save'] = {
                'requested': True,
                'saved': False,
                'message': 'Funcionalidade de salvamento no banco será implementada'
            }
        
        logger.info(f"Template '{template_name}' importado com sucesso: {len(converted_template.fields)} campos")
        
        return jsonify({
            'success': True,
            'import_result': import_result,
            'message': f'Template importado com sucesso: {len(converted_template.fields)} campos criados'
        }), 200
        
    except DocumentNotFoundException:
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
            'message': str(e)
        }), 400
        
    except TemplateServiceException as e:
        logger.error(f"Erro no serviço de template: {e}")
        return jsonify({
            'success': False,
            'error': 'template_service_error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Erro inesperado na importação: {e}")
        return jsonify({
            'success': False,
            'error': 'import_error',
            'message': 'Erro interno na importação'
        }), 500


@template_import_bp.route('/batch-import', methods=['POST'])
@limiter.limit("2 per minute")
@login_required
def batch_import_documents():
    """
    Importa múltiplos documentos como templates em lote.
    
    Request Body:
        {
            "imports": [
                {
                    "document_id": "ID1",
                    "template_name": "Nome1",
                    "template_category": "Categoria1"
                },
                {
                    "document_id": "ID2", 
                    "template_name": "Nome2",
                    "template_category": "Categoria2"
                }
            ],
            "save_to_database": false
        }
        
    Returns:
        JSON com resultados da importação em lote
    """
    try:
        data = request.get_json() or {}
        imports = data.get('imports', [])
        save_to_database = data.get('save_to_database', False)
        
        if not imports or not isinstance(imports, list):
            return jsonify({
                'success': False,
                'error': 'missing_imports',
                'message': 'Lista de imports é obrigatória'
            }), 400
        
        if len(imports) > 5:
            return jsonify({
                'success': False,
                'error': 'too_many_imports',
                'message': 'Máximo de 5 documentos por lote'
            }), 400
        
        user_id = str(current_user.id)
        results = []
        
        logger.info(f"Importação em lote de {len(imports)} documentos para usuário {user_id}")
        
        for import_item in imports:
            document_id = import_item.get('document_id')
            template_name = import_item.get('template_name')
            template_category = import_item.get('template_category')
            
            if not document_id or not template_name:
                results.append({
                    'document_id': document_id,
                    'success': False,
                    'error': 'missing_required_fields',
                    'message': 'document_id e template_name são obrigatórios'
                })
                continue
            
            try:
                converted_template = template_converter.convert_document_to_template(
                    user_id=user_id,
                    document_id=document_id,
                    template_name=template_name,
                    template_category=template_category
                )
                
                results.append({
                    'document_id': document_id,
                    'success': True,
                    'template': {
                        'id': converted_template.template_id,
                        'name': converted_template.name,
                        'category': converted_template.category,
                        'field_count': len(converted_template.fields),
                        'suitability_score': converted_template.suitability_score
                    }
                })
                
            except (DocumentNotFoundException, ValidationException, TemplateServiceException) as e:
                results.append({
                    'document_id': document_id,
                    'success': False,
                    'error': type(e).__name__,
                    'message': str(e)
                })
            
            except Exception as e:
                logger.error(f"Erro ao importar documento {document_id}: {e}")
                results.append({
                    'document_id': document_id,
                    'success': False,
                    'error': 'unexpected_error',
                    'message': 'Erro interno na importação'
                })
        
        # Estatísticas do lote
        successful_imports = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'batch_results': results,
            'statistics': {
                'total_requested': len(imports),
                'successful_imports': successful_imports,
                'failed_imports': len(imports) - successful_imports,
                'save_to_database': save_to_database
            },
            'message': f'Importação em lote concluída: {successful_imports}/{len(imports)} sucessos'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na importação em lote: {e}")
        return jsonify({
            'success': False,
            'error': 'batch_import_error',
            'message': 'Erro na importação em lote'
        }), 500


def _assess_form_complexity(template) -> str:
    """Avalia complexidade do formulário."""
    field_count = len(template.fields)
    categories = len(template.form_schema['field_groups'])
    
    if field_count <= 5 and categories <= 2:
        return 'Simples'
    elif field_count <= 15 and categories <= 4:
        return 'Moderado'
    elif field_count <= 30 and categories <= 6:
        return 'Complexo'
    else:
        return 'Muito Complexo'


def _estimate_completion_time(template) -> str:
    """Estima tempo de preenchimento do formulário."""
    field_count = len(template.fields)
    
    if field_count <= 5:
        return '2-3 minutos'
    elif field_count <= 10:
        return '5-7 minutos'
    elif field_count <= 20:
        return '10-15 minutos'
    else:
        return '20+ minutos'