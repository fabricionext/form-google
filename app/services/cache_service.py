"""
Serviço de cache adaptativo para análise de documentos.
Suporta Redis (preferido) ou cache em memória como fallback.
"""

import json
import logging
import hashlib
import time
import os
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CacheService:
    """
    Serviço de cache adaptativo que usa Redis quando disponível,
    com fallback para cache em memória.
    """
    
    def __init__(self):
        """Inicializa o serviço de cache."""
        self.redis_client = None
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'backend': None
        }
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Inicializa o backend de cache (Redis ou memória)."""
        try:
            import redis

            # Obtém a URL do Redis a partir da variável de ambiente
            redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')
            parsed_url = urlparse(redis_url)

            redis_host = parsed_url.hostname or 'redis'
            redis_port = parsed_url.port or 6379
            # O caminho após a barra é o número do DB (ex: /0)
            try:
                redis_db = int((parsed_url.path or '/0').lstrip('/'))
            except ValueError:
                redis_db = 0

            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Testa conexão
            self.redis_client.ping()
            self.cache_stats['backend'] = 'redis'
            logger.info(f"✅ Cache Redis inicializado com sucesso (host={redis_host}, port={redis_port}, db={redis_db})")
            
        except ImportError:
            logger.warning("⚠️  Redis não está instalado, usando cache em memória")
            self.cache_stats['backend'] = 'memory'
            
        except Exception as e:
            logger.warning(f"⚠️  Falha na conexão Redis ({e}), usando cache em memória")
            self.redis_client = None
            self.cache_stats['backend'] = 'memory'
    
    def _generate_key(self, prefix: str, identifier: str) -> str:
        """
        Gera chave de cache única.
        
        Args:
            prefix: Prefixo da chave (ex: 'doc_analysis', 'template_conv')
            identifier: Identificador único (ex: document_id)
            
        Returns:
            Chave formatada
        """
        # Cria hash para garantir tamanho consistente
        hash_obj = hashlib.md5(identifier.encode())
        return f"form_google:{prefix}:{hash_obj.hexdigest()}"
    
    def get(self, prefix: str, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Obtém item do cache.
        
        Args:
            prefix: Prefixo da chave
            identifier: Identificador único
            
        Returns:
            Dados cached ou None se não encontrado
        """
        key = self._generate_key(prefix, identifier)
        
        try:
            if self.redis_client:
                # Cache Redis
                cached_data = self.redis_client.get(key)
                if cached_data:
                    self.cache_stats['hits'] += 1
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return json.loads(cached_data)
                    
            else:
                # Cache em memória
                if key in self.memory_cache:
                    cache_entry = self.memory_cache[key]
                    
                    # Verifica expiração
                    if cache_entry['expires_at'] > time.time():
                        self.cache_stats['hits'] += 1
                        logger.debug(f"Cache HIT (Memory): {key}")
                        return cache_entry['data']
                    else:
                        # Remove entrada expirada
                        del self.memory_cache[key]
            
            self.cache_stats['misses'] += 1
            logger.debug(f"Cache MISS: {key}")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter cache {key}: {e}")
            self.cache_stats['misses'] += 1
            return None
    
    def set(
        self, 
        prefix: str, 
        identifier: str, 
        data: Dict[str, Any], 
        ttl_minutes: int = 60
    ) -> bool:
        """
        Armazena item no cache.
        
        Args:
            prefix: Prefixo da chave
            identifier: Identificador único
            data: Dados a serem cached
            ttl_minutes: Tempo de vida em minutos
            
        Returns:
            True se armazenado com sucesso
        """
        key = self._generate_key(prefix, identifier)
        
        try:
            # Adiciona metadados
            cache_data = {
                'data': data,
                'cached_at': datetime.now().isoformat(),
                'cache_key': key,
                'ttl_minutes': ttl_minutes
            }
            
            if self.redis_client:
                # Cache Redis
                serialized_data = json.dumps(cache_data, default=str)
                self.redis_client.setex(
                    key, 
                    timedelta(minutes=ttl_minutes), 
                    serialized_data
                )
                logger.debug(f"Cache SET (Redis): {key} (TTL: {ttl_minutes}min)")
                
            else:
                # Cache em memória
                expires_at = time.time() + (ttl_minutes * 60)
                self.memory_cache[key] = {
                    'data': cache_data,
                    'expires_at': expires_at
                }
                logger.debug(f"Cache SET (Memory): {key} (TTL: {ttl_minutes}min)")
            
            self.cache_stats['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erro ao armazenar cache {key}: {e}")
            return False
    
    def delete(self, prefix: str, identifier: str) -> bool:
        """
        Remove item do cache.
        
        Args:
            prefix: Prefixo da chave
            identifier: Identificador único
            
        Returns:
            True se removido com sucesso
        """
        key = self._generate_key(prefix, identifier)
        
        try:
            if self.redis_client:
                deleted = self.redis_client.delete(key)
                logger.debug(f"Cache DELETE (Redis): {key}")
                return deleted > 0
                
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    logger.debug(f"Cache DELETE (Memory): {key}")
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Erro ao deletar cache {key}: {e}")
            return False
    
    def clear_prefix(self, prefix: str) -> int:
        """
        Remove todas as entradas com determinado prefixo.
        
        Args:
            prefix: Prefixo a ser limpo
            
        Returns:
            Número de entradas removidas
        """
        try:
            pattern = f"form_google:{prefix}:*"
            removed_count = 0
            
            if self.redis_client:
                # Redis: busca por padrão
                keys = self.redis_client.keys(pattern)
                if keys:
                    removed_count = self.redis_client.delete(*keys)
                logger.info(f"Cache CLEAR (Redis): {removed_count} chaves removidas para {prefix}")
                
            else:
                # Memória: filtra chaves
                keys_to_remove = [
                    key for key in self.memory_cache.keys() 
                    if key.startswith(f"form_google:{prefix}:")
                ]
                for key in keys_to_remove:
                    del self.memory_cache[key]
                removed_count = len(keys_to_remove)
                logger.info(f"Cache CLEAR (Memory): {removed_count} chaves removidas para {prefix}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Erro ao limpar cache {prefix}: {e}")
            return 0
    
    def cleanup_expired(self) -> int:
        """
        Remove entradas expiradas do cache em memória.
        (Redis faz isso automaticamente)
        
        Returns:
            Número de entradas removidas
        """
        if self.redis_client:
            return 0  # Redis faz limpeza automática
        
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry['expires_at'] <= current_time
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        if expired_keys:
            logger.info(f"Cache CLEANUP: {len(expired_keys)} entradas expiradas removidas")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache.
        
        Returns:
            Estatísticas de uso
        """
        stats = self.cache_stats.copy()
        
        # Calcula hit rate
        total_requests = stats['hits'] + stats['misses']
        stats['hit_rate'] = (stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # Informações específicas do backend
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_info'] = {
                    'used_memory': info.get('used_memory_human'),
                    'connected_clients': info.get('connected_clients'),
                    'total_commands_processed': info.get('total_commands_processed')
                }
            except:
                stats['redis_info'] = {'error': 'Não foi possível obter informações do Redis'}
        else:
            stats['memory_cache_size'] = len(self.memory_cache)
            stats['memory_cache_keys'] = list(self.memory_cache.keys())[:10]  # Primeiras 10
        
        return stats
    
    def is_redis_available(self) -> bool:
        """Verifica se Redis está disponível."""
        return self.redis_client is not None


# Cache específico para documentos
class DocumentCache:
    """Cache especializado para análises de documentos."""
    
    def __init__(self, cache_service: CacheService):
        self.cache = cache_service
    
    def get_analysis(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Obtém análise cached de documento."""
        return self.cache.get('doc_analysis', document_id)
    
    def set_analysis(self, document_id: str, analysis: Dict[str, Any], ttl_minutes: int = 120) -> bool:
        """Cache análise de documento (TTL padrão: 2 horas)."""
        return self.cache.set('doc_analysis', document_id, analysis, ttl_minutes)
    
    def get_template(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Obtém template convertido cached."""
        return self.cache.get('template_conv', document_id)
    
    def set_template(self, document_id: str, template: Dict[str, Any], ttl_minutes: int = 240) -> bool:
        """Cache template convertido (TTL padrão: 4 horas)."""
        return self.cache.set('template_conv', document_id, template, ttl_minutes)
    
    def get_quick_scan(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Obtém quick scan cached."""
        return self.cache.get('quick_scan', document_id)
    
    def set_quick_scan(self, document_id: str, scan: Dict[str, Any], ttl_minutes: int = 30) -> bool:
        """Cache quick scan (TTL padrão: 30 minutos)."""
        return self.cache.set('quick_scan', document_id, scan, ttl_minutes)
    
    def invalidate_document(self, document_id: str) -> bool:
        """Invalida todos os caches relacionados a um documento."""
        results = []
        results.append(self.cache.delete('doc_analysis', document_id))
        results.append(self.cache.delete('template_conv', document_id))
        results.append(self.cache.delete('quick_scan', document_id))
        return any(results)


# Instâncias globais
cache_service = CacheService()
document_cache = DocumentCache(cache_service)