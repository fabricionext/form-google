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

# =============================================================================
# DECORADORES PARA INSTRUMENTAÇÃO
# =============================================================================

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
        
        return response
    
    # Endpoint para métricas
    @app.route('/metrics')
    def metrics():
        """Endpoint para coleta de métricas pelo Prometheus."""
        try:
            # Gerar métricas em formato Prometheus
            data = generate_latest(app_registry)
            return Response(data, mimetype=CONTENT_TYPE_LATEST)
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar métricas: {str(e)}")
            return Response("Error generating metrics", status=500)


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


def init_metrics(app):
    """
    Inicializa sistema de métricas.
    
    Args:
        app: Instância da aplicação Flask
    """
    try:
        # Configurar middleware
        setup_metrics_middleware(app)
        
        logger.info("✅ Sistema de métricas Prometheus inicializado")
        
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar métricas: {str(e)}")
        raise 