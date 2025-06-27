"""
Tasks Celery - Geração de Documentos
====================================

Tasks assíncronas para geração de documentos com Google Drive API.
Implementa circuit breakers, retry logic e instrumentação de métricas.
"""

from celery import current_task
from celery.exceptions import Retry
from app.celery_config import make_celery
from app.models.document import Document
from app.models.template import Template
from app.adapters.enhanced_google_drive import EnhancedGoogleDriveAdapter
from app.services.document_service import DocumentService
from app.services.advanced_placeholder_service import AdvancedPlaceholderService
from app.utils.exceptions import (
    DocumentGenerationException, 
    GoogleDriveException,
    PlaceholderException
)
import logging
import time
from datetime import datetime
import json

# Instrumentação Prometheus
try:
    from prometheus_client import Histogram, Counter, Gauge
    
    # Métricas de geração de documentos
    DOCUMENT_GENERATION_DURATION = Histogram(
        'document_generation_duration_seconds',
        'Tempo de geração de documento',
        ['template_type', 'status']
    )
    
    DOCUMENT_GENERATION_TOTAL = Counter(
        'document_generation_total',
        'Total de gerações de documento',
        ['template_type', 'status']
    )
    
    GOOGLE_API_CALLS_TOTAL = Counter(
        'google_api_calls_total',
        'Total de chamadas à API do Google',
        ['method', 'status']
    )
    
    ACTIVE_DOCUMENT_TASKS = Gauge(
        'active_document_generation_tasks',
        'Número de tarefas de geração ativas'
    )
    
    PROMETHEUS_AVAILABLE = True
    
except ImportError:
    # Fallback se Prometheus não estiver disponível
    PROMETHEUS_AVAILABLE = False
    logging.warning("⚠️  Prometheus client não disponível - métricas desabilitadas")


# Circuit Breaker
try:
    from pybreaker import CircuitBreaker
    
    # Circuit breaker para Google Drive API
    google_drive_breaker = CircuitBreaker(
        fail_max=5,  # Falha após 5 erros consecutivos
        reset_timeout=60,  # Reset após 1 minuto
        exclude=[
            # Não quebrar para estes tipos de erro
            ValueError,
            KeyError
        ]
    )
    
    CIRCUIT_BREAKER_AVAILABLE = True
    
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    google_drive_breaker = None
    logging.warning("⚠️  pybreaker não disponível - circuit breaker desabilitado")


# Logger específico para tasks
logger = logging.getLogger(__name__)

# Configurar retry com Tenacity
try:
    from tenacity import (
        retry, 
        stop_after_attempt, 
        wait_exponential,
        retry_if_exception_type
    )
    
    TENACITY_AVAILABLE = True
    
    # Configuração de retry para operações do Google Drive
    google_drive_retry = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((
            GoogleDriveException,
            ConnectionError,
            TimeoutError
        ))
    )
    
except ImportError:
    TENACITY_AVAILABLE = False
    google_drive_retry = lambda x: x  # No-op decorator
    logging.warning("⚠️  Tenacity não disponível - retry automático desabilitado")


# Função para criar task com contexto
def create_celery_task():
    """Factory para criar tarefas Celery com contexto."""
    from flask import current_app
    return make_celery(current_app)


@google_drive_retry
def _safe_google_operation(operation, *args, **kwargs):
    """
    Executa operação do Google Drive com circuit breaker e instrumentação.
    
    Args:
        operation: Função a ser executada
        *args, **kwargs: Argumentos para a função
        
    Returns:
        Resultado da operação
    """
    start_time = time.time()
    operation_name = operation.__name__
    
    try:
        if CIRCUIT_BREAKER_AVAILABLE and google_drive_breaker:
            result = google_drive_breaker(operation)(*args, **kwargs)
        else:
            result = operation(*args, **kwargs)
        
        # Instrumentar sucesso
        if PROMETHEUS_AVAILABLE:
            GOOGLE_API_CALLS_TOTAL.labels(
                method=operation_name, 
                status='success'
            ).inc()
        
        duration = time.time() - start_time
        logger.info(f"✅ {operation_name} executada com sucesso em {duration:.2f}s")
        
        return result
        
    except Exception as e:
        # Instrumentar erro
        if PROMETHEUS_AVAILABLE:
            GOOGLE_API_CALLS_TOTAL.labels(
                method=operation_name, 
                status='error'
            ).inc()
        
        duration = time.time() - start_time
        logger.error(f"❌ {operation_name} falhou após {duration:.2f}s: {str(e)}")
        
        raise GoogleDriveException(f"Erro em {operation_name}: {str(e)}")


# Task Principal de Geração de Documentos
def generate_document_task(template_id, form_data, options=None, user_id=None):
    """
    Task Celery para geração assíncrona de documentos.
    
    Args:
        template_id (int): ID do template
        form_data (dict): Dados do formulário
        options (dict): Opções de geração
        user_id (int): ID do usuário solicitante
        
    Returns:
        dict: Resultado da geração com metadata
    """
    task_id = current_task.request.id
    start_time = time.time()
    
    # Incrementar métrica de tarefas ativas
    if PROMETHEUS_AVAILABLE:
        ACTIVE_DOCUMENT_TASKS.inc()
    
    try:
        # Log início da tarefa
        logger.info(f"🚀 Iniciando geração de documento - Task: {task_id}, Template: {template_id}")
        
        # Atualizar status da tarefa
        current_task.update_state(
            state='PROCESSING',
            meta={
                'status': 'Iniciando geração...',
                'progress': 10,
                'started_at': datetime.now().isoformat()
            }
        )
        
        # 1. Carregar template
        template_service = DocumentService()
        template = template_service.get_template(template_id)
        
        if not template:
            raise DocumentGenerationException(f"Template {template_id} não encontrado")
        
        current_task.update_state(
            state='PROCESSING',
            meta={
                'status': 'Template carregado',
                'progress': 20,
                'template_name': template.name
            }
        )
        
        # 2. Validar dados do formulário
        placeholder_service = AdvancedPlaceholderService()
        validation_result = placeholder_service.validate_form_data(template_id, form_data)
        
        if not validation_result['valid']:
            raise PlaceholderException(f"Dados inválidos: {validation_result['errors']}")
        
        current_task.update_state(
            state='PROCESSING',
            meta={
                'status': 'Dados validados',
                'progress': 30
            }
        )
        
        # 3. Processar placeholders
        processed_data = placeholder_service.process_complex_placeholders(
            template_id, 
            form_data
        )
        
        current_task.update_state(
            state='PROCESSING',
            meta={
                'status': 'Placeholders processados',
                'progress': 50
            }
        )
        
        # 4. Gerar documento no Google Drive
        drive_adapter = EnhancedGoogleDriveAdapter()
        
        # Operações com circuit breaker
        document_copy = _safe_google_operation(
            drive_adapter.copy_document,
            template.google_doc_id,
            f"Documento - {template.name} - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        current_task.update_state(
            state='PROCESSING',
            meta={
                'status': 'Documento criado no Google Drive',
                'progress': 70,
                'google_doc_id': document_copy['id']
            }
        )
        
        # 5. Preencher placeholders no documento
        _safe_google_operation(
            drive_adapter.update_document_content,
            document_copy['id'],
            processed_data
        )
        
        current_task.update_state(
            state='PROCESSING',
            meta={
                'status': 'Conteúdo preenchido',
                'progress': 85
            }
        )
        
        # 6. Salvar metadados no banco
        document_record = template_service.create_document_record({
            'template_id': template_id,
            'google_doc_id': document_copy['id'],
            'name': document_copy['name'],
            'form_data': form_data,
            'processed_data': processed_data,
            'status': 'completed',
            'user_id': user_id,
            'generation_options': options or {},
            'task_id': task_id
        })
        
        # Calcular métricas finais
        total_duration = time.time() - start_time
        
        # Instrumentar sucesso
        if PROMETHEUS_AVAILABLE:
            DOCUMENT_GENERATION_DURATION.labels(
                template_type=template.category or 'unknown',
                status='success'
            ).observe(total_duration)
            
            DOCUMENT_GENERATION_TOTAL.labels(
                template_type=template.category or 'unknown',
                status='success'
            ).inc()
        
        # Resultado final
        result = {
            'status': 'SUCCESS',
            'document_id': document_record.id,
            'google_doc_id': document_copy['id'],
            'document_url': document_copy.get('webViewLink'),
            'name': document_copy['name'],
            'duration': total_duration,
            'completed_at': datetime.now().isoformat(),
            'metadata': {
                'template_name': template.name,
                'placeholders_count': len(processed_data),
                'task_id': task_id
            }
        }
        
        current_task.update_state(
            state='SUCCESS',
            meta=result
        )
        
        logger.info(f"✅ Documento gerado com sucesso - ID: {document_record.id}, Duração: {total_duration:.2f}s")
        
        return result
        
    except Exception as e:
        # Calcular duração mesmo em caso de erro
        total_duration = time.time() - start_time
        
        # Instrumentar erro
        if PROMETHEUS_AVAILABLE:
            template_type = 'unknown'
            try:
                template = Template.query.get(template_id)
                if template:
                    template_type = template.category or 'unknown'
            except:
                pass
            
            DOCUMENT_GENERATION_DURATION.labels(
                template_type=template_type,
                status='error'
            ).observe(total_duration)
            
            DOCUMENT_GENERATION_TOTAL.labels(
                template_type=template_type,
                status='error'
            ).inc()
        
        error_details = {
            'status': 'FAILURE',
            'error': str(e),
            'error_type': type(e).__name__,
            'duration': total_duration,
            'failed_at': datetime.now().isoformat(),
            'task_id': task_id
        }
        
        current_task.update_state(
            state='FAILURE',
            meta=error_details
        )
        
        logger.error(f"❌ Falha na geração de documento - Task: {task_id}, Erro: {str(e)}")
        
        # Relançar exceção para que o Celery registre como falha
        raise DocumentGenerationException(f"Falha na geração: {str(e)}")
        
    finally:
        # Decrementar métrica de tarefas ativas
        if PROMETHEUS_AVAILABLE:
            ACTIVE_DOCUMENT_TASKS.dec()


# Task de Cleanup
def cleanup_failed_documents_task():
    """
    Task de limpeza de documentos com falha há mais de 24h.
    """
    try:
        from datetime import timedelta
        from app.models.document import Document
        from app import db
        
        cutoff_date = datetime.now() - timedelta(hours=24)
        
        failed_documents = Document.query.filter(
            Document.status == 'failed',
            Document.created_at < cutoff_date
        ).all()
        
        cleaned_count = 0
        for doc in failed_documents:
            try:
                # Tentar remover do Google Drive
                if doc.google_doc_id:
                    drive_adapter = EnhancedGoogleDriveAdapter()
                    _safe_google_operation(
                        drive_adapter.delete_document,
                        doc.google_doc_id
                    )
                
                # Marcar como removido
                doc.status = 'deleted'
                db.session.commit()
                cleaned_count += 1
                
            except Exception as e:
                logger.warning(f"⚠️  Erro ao limpar documento {doc.id}: {str(e)}")
                continue
        
        logger.info(f"🧹 Limpeza concluída - {cleaned_count} documentos removidos")
        
        return {
            'status': 'SUCCESS',
            'cleaned_documents': cleaned_count,
            'completed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Erro na limpeza: {str(e)}")
        raise
