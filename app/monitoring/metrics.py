"""
Sistema de Métricas Prometheus
==============================

Instrumentação completa de métricas para todos os serviços da aplicação.
Configuração centralizada de métricas Prometheus seguindo best practices.
"""

from prometheus_client import (
    Histogram, Counter, Gauge, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from flask import Response, request, g
import time
import logging
import psutil
import os
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

# Registry personalizado para métricas da aplicação
app_registry = CollectorRegistry()

# =============================================================================
# MÉTRICAS DE APLICAÇÃO
# =============================================================================

# Métricas HTTP
HTTP_REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'Duração das requisições HTTP',
    ['method', 'endpoint', 'status_code'],
    registry=app_registry,
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf'))
)

HTTP_REQUEST_TOTAL = Counter(
    'http_requests_total',
    'Total de requisições HTTP',
    ['method', 'endpoint', 'status_code'],
    registry=app_registry
)

HTTP_REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'Tamanho das requisições HTTP em bytes',
    ['method', 'endpoint'],
    registry=app_registry
)

HTTP_RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'Tamanho das respostas HTTP em bytes',
    ['method', 'endpoint'],
    registry=app_registry
)

# Métricas de Business Logic
DOCUMENT_GENERATION_DURATION = Histogram(
    'document_generation_duration_seconds',
    'Tempo de geração de documento',
    ['template_type', 'status'],
    registry=app_registry
)

DOCUMENT_GENERATION_TOTAL = Counter(
    'document_generation_total',
    'Total de gerações de documento',
    ['template_type', 'status'],
    registry=app_registry
)

TEMPLATE_SYNC_DURATION = Histogram(
    'template_sync_duration_seconds',
    'Tempo de sincronização de templates',
    ['template_id', 'status'],
    registry=app_registry
)

PLACEHOLDER_PROCESSING_DURATION = Histogram(
    'placeholder_processing_duration_seconds',
    'Tempo de processamento de placeholders',
    ['operation_type'],
    registry=app_registry
)

# Métricas de Integração Externa
GOOGLE_API_CALLS_TOTAL = Counter(
    'google_api_calls_total',
    'Total de chamadas à API do Google',
    ['method', 'status', 'api_type'],
    registry=app_registry
)

GOOGLE_API_DURATION = Histogram(
    'google_api_duration_seconds',
    'Duração das chamadas à API do Google',
    ['method', 'api_type'],
    registry=app_registry,
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, float('inf'))
)

# Métricas de Sistema
ACTIVE_CELERY_TASKS = Gauge(
    'active_celery_tasks',
    'Número de tarefas Celery ativas',
    ['queue', 'task_type'],
    registry=app_registry
)

REDIS_CONNECTION_POOL = Gauge(
    'redis_connection_pool_size',
    'Tamanho do pool de conexões Redis',
    ['pool_type'],
    registry=app_registry
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Conexões ativas com o banco de dados',
    registry=app_registry
)

# Métricas de Cache
CACHE_OPERATIONS_TOTAL = Counter(
    'cache_operations_total',
    'Total de operações de cache',
    ['operation', 'status'],
    registry=app_registry
)

CACHE_HIT_RATIO = Gauge(
    'cache_hit_ratio',
    'Taxa de acertos do cache',
    ['cache_type'],
    registry=app_registry
)

# Métricas de Segurança
AUTHENTICATION_ATTEMPTS = Counter(
    'authentication_attempts_total',
    'Total de tentativas de autenticação',
    ['status', 'method'],
    registry=app_registry
)

RATE_LIMIT_EXCEEDED = Counter(
    'rate_limit_exceeded_total',
    'Total de violações de rate limit',
    ['endpoint', 'user_id'],
    registry=app_registry
)

# Informações da Aplicação
APP_INFO = Info(
    'application_info',
    'Informações da aplicação',
    registry=app_registry
)

# =============================================================================
# DECORADORES PARA INSTRUMENTAÇÃO
# =============================================================================

def measure_time(metric_histogram, labels=None):
    """
    Decorator para medir tempo de execução de funções.
    
    Args:
        metric_histogram: Métrica Histogram do Prometheus
        labels: Labels adicionais para a métrica
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = 'success'
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                final_labels = (labels or []) + [status]
                metric_histogram.labels(*final_labels).observe(duration)
        return wrapper
    return decorator


def count_calls(metric_counter, labels=None):
    """
    Decorator para contar chamadas de funções.
    
    Args:
        metric_counter: Métrica Counter do Prometheus
        labels: Labels adicionais para a métrica
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                status = 'success'
                return result
            except Exception as e:
                status = 'error'
                raise
            finally:
                final_labels = (labels or []) + [status]
                metric_counter.labels(*final_labels).inc()
        return wrapper
    return decorator


def track_google_api_call(api_type, method):
    """
    Decorator específico para rastreamento de chamadas Google API.
    
    Args:
        api_type: Tipo de API (drive, docs, etc.)
        method: Método chamado
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                status = 'success'
                return result
            except Exception as e:
                status = 'error'
                logger.error(f"❌ Google API call failed: {api_type}.{method} - {str(e)}")
                raise
            finally:
                duration = time.time() - start_time
                
                # Instrumentar duração
                GOOGLE_API_DURATION.labels(
                    method=method,
                    api_type=api_type
                ).observe(duration)
                
                # Instrumentar contador
                GOOGLE_API_CALLS_TOTAL.labels(
                    method=method,
                    status=status,
                    api_type=api_type
                ).inc()
                
                logger.info(f"📊 Google API: {api_type}.{method} - {status} ({duration:.2f}s)")
        return wrapper
    return decorator


# =============================================================================
# MIDDLEWARE FLASK PARA INSTRUMENTAÇÃO AUTOMÁTICA
# =============================================================================

def setup_metrics_middleware(app):
    """
    Configura middleware para instrumentação automática de métricas HTTP.
    
    Args:
        app: Instância da aplicação Flask
    """
    
    @app.before_request
    def before_request():
        """Registra início da requisição."""
        g.start_time = time.time()
        g.request_size = len(request.get_data())
    
    @app.after_request
    def after_request(response):
        """Registra métricas da requisição."""
        if hasattr(g, 'start_time'):
            # Calcular duração
            duration = time.time() - g.start_time
            
            # Extrair informações da requisição
            method = request.method
            endpoint = request.endpoint or 'unknown'
            status_code = str(response.status_code)
            
            # Instrumentar duração
            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(duration)
            
            # Instrumentar contador
            HTTP_REQUEST_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            # Instrumentar tamanho da requisição
            if hasattr(g, 'request_size'):
                HTTP_REQUEST_SIZE.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(g.request_size)
            
            # Instrumentar tamanho da resposta
            if response.content_length:
                HTTP_RESPONSE_SIZE.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(response.content_length)
        
        return response
    
    # Endpoint para métricas
    @app.route('/metrics')
    def metrics():
        """Endpoint para coleta de métricas pelo Prometheus."""
        try:
            # Atualizar métricas de sistema antes de expor
            update_system_metrics()
            
            # Gerar métricas em formato Prometheus
            data = generate_latest(app_registry)
            return Response(data, mimetype=CONTENT_TYPE_LATEST)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar métricas: {str(e)}")
            return Response("Error generating metrics", status=500)


# =============================================================================
# MÉTRICAS DE SISTEMA
# =============================================================================

def update_system_metrics():
    """
    Atualiza métricas de sistema (CPU, memória, etc.).
    """
    try:
        # Métricas de processo
        process = psutil.Process(os.getpid())
        
        # CPU e Memória (se disponível)
        try:
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            
            # Criar gauges dinâmicos se não existirem
            if not hasattr(update_system_metrics, 'cpu_gauge'):
                update_system_metrics.cpu_gauge = Gauge(
                    'process_cpu_percent',
                    'Uso de CPU do processo',
                    registry=app_registry
                )
                
                update_system_metrics.memory_gauge = Gauge(
                    'process_memory_bytes',
                    'Uso de memória do processo',
                    ['type'],
                    registry=app_registry
                )
            
            update_system_metrics.cpu_gauge.set(cpu_percent)
            update_system_metrics.memory_gauge.labels(type='rss').set(memory_info.rss)
            update_system_metrics.memory_gauge.labels(type='vms').set(memory_info.vms)
            
        except Exception as e:
            logger.debug(f"Métricas de sistema não disponíveis: {str(e)}")
    
    except Exception as e:
        logger.warning(f"⚠️  Erro ao atualizar métricas de sistema: {str(e)}")


def update_app_info(app):
    """
    Atualiza informações da aplicação.
    
    Args:
        app: Instância da aplicação Flask
    """
    try:
        from app.config.constants import APP_VERSION
        
        APP_INFO.info({
            'version': getattr(app.config, 'VERSION', APP_VERSION),
            'environment': app.config.get('FLASK_ENV', 'unknown'),
            'debug': str(app.debug),
            'started_at': datetime.now().isoformat(),
            'python_version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
        })
        
    except Exception as e:
        logger.warning(f"⚠️  Erro ao atualizar informações da aplicação: {str(e)}")


# =============================================================================
# FUNÇÕES DE CONVENIÊNCIA
# =============================================================================

def increment_document_generation(template_type, status='success'):
    """Incrementa contador de geração de documentos."""
    DOCUMENT_GENERATION_TOTAL.labels(
        template_type=template_type,
        status=status
    ).inc()


def record_document_duration(template_type, duration, status='success'):
    """Registra duração de geração de documento."""
    DOCUMENT_GENERATION_DURATION.labels(
        template_type=template_type,
        status=status
    ).observe(duration)


def increment_cache_operation(operation, status='hit'):
    """Incrementa operação de cache."""
    CACHE_OPERATIONS_TOTAL.labels(
        operation=operation,
        status=status
    ).inc()


def record_authentication_attempt(status, method='form'):
    """Registra tentativa de autenticação."""
    AUTHENTICATION_ATTEMPTS.labels(
        status=status,
        method=method
    ).inc()


# =============================================================================
# INICIALIZAÇÃO
# =============================================================================

def init_metrics(app):
    """
    Inicializa sistema de métricas.
    
    Args:
        app: Instância da aplicação Flask
    """
    try:
        # Configurar middleware
        setup_metrics_middleware(app)
        
        # Atualizar informações da aplicação
        update_app_info(app)
        
        logger.info("✅ Sistema de métricas Prometheus inicializado")
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar métricas: {str(e)}")
        raise 