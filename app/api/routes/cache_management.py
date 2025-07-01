"""
Rotas para gerenciamento de cache do sistema.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from app.services.cache_service import cache_service, document_cache
from app.extensions import limiter

logger = logging.getLogger(__name__)

# Blueprint para gerenciamento de cache
cache_management_bp = Blueprint('cache_management', __name__, url_prefix='/api/cache')


@cache_management_bp.route('/stats', methods=['GET'])
@limiter.limit("10 per minute")
@login_required
def get_cache_stats():
    """
    Obtém estatísticas do cache.
    
    Returns:
        JSON com estatísticas de uso do cache
    """
    try:
        stats = cache_service.get_stats()
        
        return jsonify({
            'success': True,
            'cache_stats': stats,
            'message': f'Cache usando backend: {stats["backend"]}'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do cache: {e}")
        return jsonify({
            'success': False,
            'error': 'stats_error',
            'message': 'Erro ao obter estatísticas do cache'
        }), 500


@cache_management_bp.route('/clear', methods=['POST'])
@limiter.limit("3 per minute")
@login_required
def clear_cache():
    """
    Limpa cache por prefixo ou invalidação específica.
    
    Request Body:
        {
            "action": "clear_prefix|clear_document|cleanup_expired",
            "prefix": "doc_analysis|template_conv|quick_scan", 
            "document_id": "ID_do_documento" (para clear_document)
        }
        
    Returns:
        JSON com resultado da operação
    """
    try:
        data = request.get_json() or {}
        action = data.get('action')
        
        if not action:
            return jsonify({
                'success': False,
                'error': 'missing_action',
                'message': 'action é obrigatório (clear_prefix, clear_document, cleanup_expired)'
            }), 400
        
        result = {}
        
        if action == 'clear_prefix':
            prefix = data.get('prefix')
            if not prefix:
                return jsonify({
                    'success': False,
                    'error': 'missing_prefix',
                    'message': 'prefix é obrigatório para clear_prefix'
                }), 400
            
            removed_count = cache_service.clear_prefix(prefix)
            result = {
                'action': 'clear_prefix',
                'prefix': prefix,
                'removed_entries': removed_count
            }
            
        elif action == 'clear_document':
            document_id = data.get('document_id')
            if not document_id:
                return jsonify({
                    'success': False,
                    'error': 'missing_document_id',
                    'message': 'document_id é obrigatório para clear_document'
                }), 400
            
            invalidated = document_cache.invalidate_document(document_id)
            result = {
                'action': 'clear_document',
                'document_id': document_id,
                'invalidated': invalidated
            }
            
        elif action == 'cleanup_expired':
            removed_count = cache_service.cleanup_expired()
            result = {
                'action': 'cleanup_expired',
                'removed_entries': removed_count
            }
            
        else:
            return jsonify({
                'success': False,
                'error': 'invalid_action',
                'message': 'action deve ser: clear_prefix, clear_document ou cleanup_expired'
            }), 400
        
        logger.info(f"Cache {action} executado por usuário {current_user.id}: {result}")
        
        return jsonify({
            'success': True,
            'cache_operation': result,
            'message': f'Operação {action} executada com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na operação de cache: {e}")
        return jsonify({
            'success': False,
            'error': 'cache_operation_error',
            'message': 'Erro na operação de cache'
        }), 500


@cache_management_bp.route('/status', methods=['GET'])
@limiter.limit("30 per minute")
@login_required
def get_cache_status():
    """
    Obtém status do sistema de cache.
    
    Returns:
        JSON com status do cache
    """
    try:
        is_redis = cache_service.is_redis_available()
        stats = cache_service.get_stats()
        
        status = {
            'cache_backend': stats['backend'],
            'redis_available': is_redis,
            'cache_enabled': True,
            'performance': {
                'hit_rate': stats['hit_rate'],
                'total_hits': stats['hits'],
                'total_misses': stats['misses'],
                'total_sets': stats['sets']
            }
        }
        
        if is_redis:
            status['redis_info'] = stats.get('redis_info', {})
        else:
            status['memory_cache'] = {
                'current_size': stats.get('memory_cache_size', 0),
                'sample_keys': stats.get('memory_cache_keys', [])
            }
        
        return jsonify({
            'success': True,
            'cache_status': status,
            'message': 'Status do cache obtido com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter status do cache: {e}")
        return jsonify({
            'success': False,
            'error': 'status_error',
            'message': 'Erro ao obter status do cache'
        }), 500


@cache_management_bp.route('/test', methods=['POST'])
@limiter.limit("5 per minute")
@login_required
def test_cache():
    """
    Testa funcionalidade do cache com dados de exemplo.
    
    Returns:
        JSON com resultado do teste
    """
    try:
        test_key = f"test_user_{current_user.id}"
        test_data = {
            'test': True,
            'timestamp': str(cache_service.cache_stats),
            'user_id': str(current_user.id)
        }
        
        # Teste de escrita
        set_result = cache_service.set('test', test_key, test_data, ttl_minutes=5)
        
        # Teste de leitura
        retrieved_data = cache_service.get('test', test_key)
        
        # Teste de remoção
        delete_result = cache_service.delete('test', test_key)
        
        test_results = {
            'set_operation': set_result,
            'get_operation': retrieved_data is not None,
            'data_integrity': retrieved_data == test_data if retrieved_data else False,
            'delete_operation': delete_result,
            'cache_backend': cache_service.cache_stats['backend']
        }
        
        success = all([
            test_results['set_operation'],
            test_results['get_operation'], 
            test_results['data_integrity']
        ])
        
        return jsonify({
            'success': success,
            'cache_test': test_results,
            'message': 'Teste de cache concluído' if success else 'Falha no teste de cache'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Erro no teste de cache: {e}")
        return jsonify({
            'success': False,
            'error': 'test_error',
            'message': 'Erro no teste de cache'
        }), 500


@cache_management_bp.route('/health', methods=['GET'])
@limiter.limit("60 per minute")
def cache_health_check():
    """
    Health check do sistema de cache (não requer autenticação).
    
    Returns:
        JSON com status de saúde do cache
    """
    try:
        backend = cache_service.cache_stats['backend']
        is_healthy = True
        
        if backend == 'redis':
            try:
                cache_service.redis_client.ping()
                health_status = 'healthy'
            except:
                health_status = 'redis_connection_failed'
                is_healthy = False
        else:
            health_status = 'memory_cache_active'
        
        return jsonify({
            'cache_healthy': is_healthy,
            'backend': backend,
            'status': health_status,
            'timestamp': str(cache_service.cache_stats)
        }), 200 if is_healthy else 503
        
    except Exception as e:
        logger.error(f"Erro no health check do cache: {e}")
        return jsonify({
            'cache_healthy': False,
            'error': str(e)
        }), 503