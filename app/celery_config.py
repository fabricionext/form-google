"""
Configuração do Celery - Processamento Assíncrono
================================================

Configuração do Celery com Redis como broker e backend para tarefas assíncronas.
"""

from celery import Celery
from flask import current_app
import os

# Configuração do Redis
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

def make_celery(app=None):
    """
    Factory function para criar instância do Celery integrada com Flask.
    
    Args:
        app: Instância da aplicação Flask
        
    Returns:
        celery: Instância configurada do Celery
    """
    celery = Celery(
        app.import_name if app else __name__,
        backend=CELERY_RESULT_BACKEND,
        broker=CELERY_BROKER_URL,
        include=[
            'app.tasks.document_generation',
            'app.tasks.template_sync',
            'app.tasks.cleanup'
        ]
    )
    
    # Configurações do Celery
    celery.conf.update({
        # Task routing
        'task_routes': {
            'app.tasks.document_generation.*': {'queue': 'documents'},
            'app.tasks.template_sync.*': {'queue': 'templates'},
            'app.tasks.cleanup.*': {'queue': 'maintenance'}
        },
        
        # Retry configuration
        'task_acks_late': True,
        'worker_prefetch_multiplier': 1,
        'task_reject_on_worker_lost': True,
        
        # Time limits
        'task_time_limit': 300,  # 5 minutos hard limit
        'task_soft_time_limit': 240,  # 4 minutos soft limit
        
        # Serialization
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'timezone': 'America/Sao_Paulo',
        'enable_utc': True,
        
        # Results
        'result_expires': 3600,  # 1 hora
        'result_compression': 'gzip',
        
        # Monitoring
        'worker_send_task_events': True,
        'task_send_sent_event': True,
        
        # Error handling
        'task_reject_on_worker_lost': True,
        'task_ignore_result': False,
        
        # Batching (para otimização)
        'worker_pool_restarts': True,
        
        # Priority queues
        'task_default_priority': 5,
        'worker_disable_rate_limits': False
    })
    
    if app:
        # Integração com Flask app context
        class ContextTask(celery.Task):
            """Task personalizada que executa dentro do contexto da aplicação Flask."""
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
        
        # Inicializar Redis connections
        init_redis_connections(app)
    
    return celery


def init_redis_connections(app):
    """
    Inicializa conexões Redis para cache e outras operações.
    
    Args:
        app: Instância da aplicação Flask
    """
    try:
        import redis
        
        # Redis para cache
        app.redis_cache = redis.Redis.from_url(
            REDIS_URL + '/1',  # Database 1 para cache
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Redis para sessões (se necessário)
        app.redis_sessions = redis.Redis.from_url(
            REDIS_URL + '/2',  # Database 2 para sessões
            decode_responses=True
        )
        
        # Testar conexões
        app.redis_cache.ping()
        app.redis_sessions.ping()
        
        app.logger.info("✅ Conexões Redis inicializadas com sucesso")
        
    except Exception as e:
        app.logger.error(f"❌ Erro ao inicializar Redis: {str(e)}")
        # Fallback para cache em memória se Redis não estiver disponível
        app.redis_cache = None
        app.redis_sessions = None


# Configurações específicas por ambiente
CELERY_CONFIG_BY_ENV = {
    'development': {
        'task_always_eager': False,  # False para testar workers reais
        'task_eager_propagates': True,
        'worker_log_level': 'DEBUG',
        'worker_concurrency': 2
    },
    'testing': {
        'task_always_eager': True,  # True para testes síncronos
        'task_eager_propagates': True,
        'task_store_eager_result': True
    },
    'production': {
        'task_always_eager': False,
        'worker_log_level': 'INFO',
        'worker_concurrency': 4,
        'worker_max_tasks_per_child': 1000,
        'worker_max_memory_per_child': 200000  # 200MB
    }
}


def get_celery_config(env='development'):
    """
    Retorna configuração específica do ambiente.
    
    Args:
        env: Ambiente ('development', 'testing', 'production')
        
    Returns:
        dict: Configurações do Celery para o ambiente
    """
    return CELERY_CONFIG_BY_ENV.get(env, CELERY_CONFIG_BY_ENV['development']) 