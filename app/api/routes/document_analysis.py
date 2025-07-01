"""
Rotas para análise de documentos Google Docs.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services.google_docs_analyzer import google_docs_analyzer
# Service account authentication - no OAuth required
from app.utils.exceptions import (
    DocumentNotFoundException,
    GoogleDriveException,
    AuthenticationException
)
from app.extensions import limiter

logger = logging.getLogger(__name__)

# Blueprint para análise de documentos
document_analysis_bp = Blueprint('document_analysis', __name__, url_prefix='/api/documents')


@document_analysis_bp.route('/analyze/<document_id>', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def analyze_document(document_id):
    """
    Analisa um documento Google Docs completo.
    
    Args:
        document_id: ID do documento no Google Drive
        
    Returns:
        JSON com análise completa do documento
    """
    try:
        user_id = str(current_user.id)
        
        logger.info(f"Iniciando análise do documento {document_id} para usuário {user_id}")
        
        # Analisa documento
        analysis = google_docs_analyzer.analyze_document(user_id, document_id)
        
        logger.info(f"Análise concluída: {analysis['placeholders']['total_count']} placeholders encontrados")
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'message': 'Documento analisado com sucesso'
        }), 200
        
    except DocumentNotFoundException as e:
        logger.warning(f"Documento não encontrado: {document_id}")
        return jsonify({
            'success': False,
            'error': 'document_not_found',
            'message': f'Documento {document_id} não foi encontrado'
        }), 404
        
    except AuthenticationException as e:
        logger.error(f"Erro de autenticação: {e}")
        return jsonify({
            'success': False,
            'error': 'authentication_error',
            'message': 'Erro na autenticação com Google Drive'
        }), 401
        
    except GoogleDriveException as e:
        logger.error(f"Erro do Google Drive: {e}")
        return jsonify({
            'success': False,
            'error': 'google_drive_error',
            'message': str(e)
        }), 503
        
    except Exception as e:
        logger.error(f"Erro inesperado na análise: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor'
        }), 500


@document_analysis_bp.route('/quick-scan/<document_id>', methods=['GET'])
@limiter.limit("30 per minute")
@login_required
def quick_scan_document(document_id):
    """
    Faz uma varredura rápida do documento para informações básicas.
    
    Args:
        document_id: ID do documento no Google Drive
        
    Returns:
        JSON com informações básicas do documento
    """
    try:
        user_id = str(current_user.id)
        
        # Varredura rápida
        scan_result = google_docs_analyzer.quick_scan(user_id, document_id)
        
        return jsonify({
            'success': True,
            'scan': scan_result,
            'message': 'Varredura concluída'
        }), 200
        
    except DocumentNotFoundException as e:
        logger.warning(f"Documento não encontrado: {document_id}")
        return jsonify({
            'success': False,
            'error': 'document_not_found',
            'message': f'Documento {document_id} não foi encontrado'
        }), 404
        
    except Exception as e:
        logger.error(f"Erro na varredura rápida: {e}")
        return jsonify({
            'success': False,
            'error': 'scan_error',
            'message': 'Erro na varredura do documento'
        }), 500


@document_analysis_bp.route('/batch-analyze', methods=['POST'])
@limiter.limit("5 per minute")
@login_required
def batch_analyze_documents():
    """
    Analisa múltiplos documentos em lote.
    
    Expects:
        JSON: {
            "document_ids": ["id1", "id2", "id3"],
            "quick_scan_only": false
        }
        
    Returns:
        JSON com resultados da análise em lote
    """
    try:
        data = request.get_json()
        
        if not data or 'document_ids' not in data:
            return jsonify({
                'success': False,
                'error': 'invalid_request',
                'message': 'Lista de document_ids é obrigatória'
            }), 400
        
        document_ids = data['document_ids']
        quick_scan_only = data.get('quick_scan_only', False)
        
        if not isinstance(document_ids, list) or len(document_ids) == 0:
            return jsonify({
                'success': False,
                'error': 'invalid_request',
                'message': 'document_ids deve ser uma lista não vazia'
            }), 400
        
        if len(document_ids) > 10:
            return jsonify({
                'success': False,
                'error': 'too_many_documents',
                'message': 'Máximo de 10 documentos por lote'
            }), 400
        
        user_id = str(current_user.id)
        results = []
        
        for doc_id in document_ids:
            try:
                if quick_scan_only:
                    result = google_docs_analyzer.quick_scan(user_id, doc_id)
                else:
                    result = google_docs_analyzer.analyze_document(user_id, doc_id)
                
                results.append({
                    'document_id': doc_id,
                    'success': True,
                    'result': result
                })
                
            except DocumentNotFoundException:
                results.append({
                    'document_id': doc_id,
                    'success': False,
                    'error': 'document_not_found'
                })
                
            except Exception as e:
                logger.error(f"Erro ao analisar documento {doc_id}: {e}")
                results.append({
                    'document_id': doc_id,
                    'success': False,
                    'error': 'analysis_error',
                    'message': str(e)
                })
        
        # Estatísticas do lote
        successful_analyses = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': True,
            'batch_results': results,
            'statistics': {
                'total_documents': len(document_ids),
                'successful_analyses': successful_analyses,
                'failed_analyses': len(document_ids) - successful_analyses,
                'quick_scan_only': quick_scan_only
            },
            'message': f'Análise em lote concluída: {successful_analyses}/{len(document_ids)} sucessos'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na análise em lote: {e}")
        return jsonify({
            'success': False,
            'error': 'batch_error',
            'message': 'Erro na análise em lote'
        }), 500


@document_analysis_bp.route('/placeholders/extract/<document_id>', methods=['POST'])
@limiter.limit("20 per minute")
@login_required
def extract_placeholders_only(document_id):
    """
    Extrai apenas os placeholders de um documento (análise focada).
    
    Args:
        document_id: ID do documento no Google Drive
        
    Returns:
        JSON com placeholders extraídos
    """
    try:
        user_id = str(current_user.id)
        
        # Análise completa primeiro
        analysis = google_docs_analyzer.analyze_document(user_id, document_id)
        
        # Retorna apenas informações de placeholders
        placeholders_info = {
            'document_id': document_id,
            'document_name': analysis['metadata']['name'],
            'placeholders': analysis['placeholders']['placeholders'],
            'summary': {
                'total_count': analysis['placeholders']['total_count'],
                'unique_count': analysis['placeholders']['unique_count'],
                'categories': analysis['placeholders']['categories'],
                'types': analysis['placeholders']['types']
            },
            'suitability': analysis['suitable_for_template'],
            'extraction_timestamp': analysis['analysis_timestamp']
        }
        
        return jsonify({
            'success': True,
            'placeholders': placeholders_info,
            'message': f'{placeholders_info["summary"]["total_count"]} placeholders extraídos'
        }), 200
        
    except DocumentNotFoundException as e:
        logger.warning(f"Documento não encontrado: {document_id}")
        return jsonify({
            'success': False,
            'error': 'document_not_found',
            'message': f'Documento {document_id} não foi encontrado'
        }), 404
        
    except Exception as e:
        logger.error(f"Erro na extração de placeholders: {e}")
        return jsonify({
            'success': False,
            'error': 'extraction_error',
            'message': 'Erro na extração de placeholders'
        }), 500


@document_analysis_bp.route('/suitability/<document_id>', methods=['GET'])
@limiter.limit("30 per minute")
@login_required
def assess_template_suitability(document_id):
    """
    Avalia se um documento é adequado como template.
    
    Args:
        document_id: ID do documento no Google Drive
        
    Returns:
        JSON com avaliação de adequação
    """
    try:
        user_id = str(current_user.id)
        
        # Análise completa
        analysis = google_docs_analyzer.analyze_document(user_id, document_id)
        
        # Retorna apenas avaliação de adequação
        suitability = {
            'document_id': document_id,
            'document_name': analysis['metadata']['name'],
            'suitability_assessment': analysis['suitable_for_template'],
            'key_metrics': {
                'placeholder_count': analysis['placeholders']['total_count'],
                'categories_count': len(analysis['placeholders']['categories']),
                'word_count': analysis['content']['word_count'],
                'placeholder_density': analysis['statistics']['placeholder_density']['placeholders_per_100_words']
            },
            'assessment_timestamp': analysis['analysis_timestamp']
        }
        
        return jsonify({
            'success': True,
            'suitability': suitability,
            'message': f'Adequação: {suitability["suitability_assessment"]["classification"]}'
        }), 200
        
    except DocumentNotFoundException as e:
        logger.warning(f"Documento não encontrado: {document_id}")
        return jsonify({
            'success': False,
            'error': 'document_not_found',
            'message': f'Documento {document_id} não foi encontrado'
        }), 404
        
    except Exception as e:
        logger.error(f"Erro na avaliação de adequação: {e}")
        return jsonify({
            'success': False,
            'error': 'assessment_error',
            'message': 'Erro na avaliação de adequação'
        }), 500


@document_analysis_bp.route('/statistics', methods=['GET'])
@limiter.limit("60 per minute")
@login_required
def get_analysis_statistics():
    """
    Obtém estatísticas gerais de análises realizadas pelo usuário.
    
    Returns:
        JSON com estatísticas de uso
    """
    try:
        # Por enquanto, retorna estatísticas mock
        # Em uma implementação completa, isso viria do banco de dados
        statistics = {
            'user_id': str(current_user.id),
            'total_analyses': 0,  # Seria contado do histórico
            'documents_analyzed_today': 0,
            'most_common_categories': [],
            'average_placeholders_per_document': 0,
            'templates_created': 0,
            'last_analysis': None
        }
        
        return jsonify({
            'success': True,
            'statistics': statistics,
            'message': 'Estatísticas obtidas com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        return jsonify({
            'success': False,
            'error': 'statistics_error',
            'message': 'Erro ao obter estatísticas'
        }), 500