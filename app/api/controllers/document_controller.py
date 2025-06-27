"""
Document Controller - Gerenciamento completo de documentos
=========================================================

Controller para geração, monitoramento e gestão de documentos gerados.
"""

from typing import Dict, Any, List, Optional
from flask import request, current_app, send_file
from marshmallow import ValidationError
import uuid

from .base import BaseController
from app.services.document_service import DocumentService
from app.services.template_service import TemplateService
from app.services.validation_service import ValidationService
from app.utils.exceptions import (
    NotFoundException, 
    ValidationException, 
    DocumentNotFoundException,
    TemplateNotFoundException,
    IntegrationException
)


class DocumentController(BaseController):
    """Controller para operações com documentos."""
    
    def __init__(self):
        super().__init__()
        self.document_service = DocumentService()
        self.template_service = TemplateService()
        self.validation_service = ValidationService()
    
    def generate_document(self, template_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Inicia geração de documento (processamento assíncrono)."""
        try:
            # Verificar se template existe
            template = self.template_service.get_template_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(template_id)
            
            # Validar dados de entrada
            validation_result = self.validation_service.validate_document_data(
                template_id, data
            )
            if not validation_result['is_valid']:
                return self.error_response(
                    f"Dados inválidos: {', '.join(validation_result['errors'])}",
                    400
                )
            
            # Gerar ID único para a tarefa
            task_id = str(uuid.uuid4())
            
            # Enfileirar geração via service (Celery task)
            generation_result = self.document_service.generate_document_async(
                template_id=template_id,
                data=data,
                task_id=task_id,
                user_id=getattr(request, 'user_id', None)
            )
            
            return self.success_response(
                data={
                    'task_id': task_id,
                    'template_id': template_id,
                    'status': 'queued',
                    'estimated_time': generation_result.get('estimated_time', 30)
                },
                message="Geração de documento iniciada",
                status_code=202
            )
            
        except TemplateNotFoundException as e:
            return self.error_response(str(e), 404)
        except ValidationException as e:
            return self.error_response(str(e), 400)
        except Exception as e:
            current_app.logger.error(f"Erro ao iniciar geração documento: {str(e)}")
            return self.error_response("Erro ao iniciar geração de documento")
    
    def get_document_status(self, task_id: str) -> Dict[str, Any]:
        """Consulta status da geração de documento."""
        try:
            status_info = self.document_service.get_generation_status(task_id)
            
            if not status_info:
                return self.error_response("Tarefa não encontrada", 404)
            
            return self.success_response(
                data=status_info,
                message="Status obtido com sucesso"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao obter status {task_id}: {str(e)}")
            return self.error_response("Erro ao obter status")
    
    def list_documents(self, filters: Dict[str, Any] = None, 
                      pagination: Dict[str, int] = None) -> Dict[str, Any]:
        """Lista documentos gerados com filtros."""
        try:
            # Parâmetros de paginação
            page = pagination.get('page', 1) if pagination else 1
            per_page = min(pagination.get('per_page', 20) if pagination else 20, 100)
            
            # Filtros
            filters = filters or {}
            
            # Adicionar filtro por usuário se não for admin
            user_id = getattr(request, 'user_id', None)
            if user_id and not getattr(request, 'is_admin', False):
                filters['user_id'] = user_id
            
            # Buscar documentos via service
            documents_data = self.document_service.list_documents(
                filters=filters,
                page=page,
                per_page=per_page
            )
            
            return self.paginated_response(
                items=documents_data['items'],
                total=documents_data['total'],
                pagination_params={
                    'page': page,
                    'per_page': per_page,
                    'pages': documents_data.get('pages', 1)
                },
                message=f"Encontrados {documents_data['total']} documentos"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao listar documentos: {str(e)}")
            return self.error_response("Erro ao listar documentos")
    
    def get_document(self, document_id: int) -> Dict[str, Any]:
        """Busca documento por ID."""
        try:
            document_data = self.document_service.get_document_by_id(document_id)
            
            if not document_data:
                raise DocumentNotFoundException(document_id)
            
            # Verificar permissões (usuário só vê seus próprios documentos)
            user_id = getattr(request, 'user_id', None)
            is_admin = getattr(request, 'is_admin', False)
            
            if not is_admin and document_data.get('user_id') != user_id:
                return self.error_response("Acesso não autorizado", 403)
            
            return self.success_response(
                data={'document': document_data},
                message="Documento encontrado com sucesso"
            )
            
        except DocumentNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao buscar documento {document_id}: {str(e)}")
            return self.error_response("Erro ao buscar documento")
    
    def download_document(self, document_id: int) -> Any:
        """Download do documento gerado."""
        try:
            document_data = self.document_service.get_document_by_id(document_id)
            
            if not document_data:
                raise DocumentNotFoundException(document_id)
            
            # Verificar permissões
            user_id = getattr(request, 'user_id', None)
            is_admin = getattr(request, 'is_admin', False)
            
            if not is_admin and document_data.get('user_id') != user_id:
                return self.error_response("Acesso não autorizado", 403)
            
            # Verificar se documento está pronto
            if document_data['status'] != 'completed':
                return self.error_response(
                    f"Documento não está pronto. Status: {document_data['status']}",
                    400
                )
            
            # Obter link ou arquivo para download
            download_info = self.document_service.get_download_info(document_id)
            
            if download_info['type'] == 'redirect':
                # Redirect para Google Drive
                return {
                    'redirect_url': download_info['url'],
                    'file_name': download_info['file_name']
                }
            elif download_info['type'] == 'file':
                # Download direto
                return send_file(
                    download_info['file_path'],
                    as_attachment=True,
                    download_name=download_info['file_name']
                )
            
        except DocumentNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao fazer download {document_id}: {str(e)}")
            return self.error_response("Erro ao fazer download")
    
    def regenerate_document(self, document_id: int, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Regenera documento com dados atualizados."""
        try:
            # Buscar documento original
            original_doc = self.document_service.get_document_by_id(document_id)
            if not original_doc:
                raise DocumentNotFoundException(document_id)
            
            # Verificar permissões
            user_id = getattr(request, 'user_id', None)
            is_admin = getattr(request, 'is_admin', False)
            
            if not is_admin and original_doc.get('user_id') != user_id:
                return self.error_response("Acesso não autorizado", 403)
            
            # Usar dados fornecidos ou dados originais
            generation_data = data or original_doc.get('generation_data', {})
            
            # Gerar novo documento
            task_id = str(uuid.uuid4())
            
            generation_result = self.document_service.generate_document_async(
                template_id=original_doc['template_id'],
                data=generation_data,
                task_id=task_id,
                user_id=user_id,
                parent_document_id=document_id
            )
            
            return self.success_response(
                data={
                    'task_id': task_id,
                    'parent_document_id': document_id,
                    'status': 'queued'
                },
                message="Regeneração iniciada",
                status_code=202
            )
            
        except DocumentNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao regenerar documento {document_id}: {str(e)}")
            return self.error_response("Erro ao regenerar documento")
    
    def delete_document(self, document_id: int) -> Dict[str, Any]:
        """Remove documento (soft delete)."""
        try:
            document_data = self.document_service.get_document_by_id(document_id)
            if not document_data:
                raise DocumentNotFoundException(document_id)
            
            # Verificar permissões
            user_id = getattr(request, 'user_id', None)
            is_admin = getattr(request, 'is_admin', False)
            
            if not is_admin and document_data.get('user_id') != user_id:
                return self.error_response("Acesso não autorizado", 403)
            
            # Soft delete via service
            self.document_service.delete_document(document_id)
            
            return self.success_response(
                message="Documento removido com sucesso"
            )
            
        except DocumentNotFoundException as e:
            return self.error_response(str(e), 404)
        except Exception as e:
            current_app.logger.error(f"Erro ao remover documento {document_id}: {str(e)}")
            return self.error_response("Erro ao remover documento")
    
    def get_generation_history(self, template_id: int = None, 
                             user_id: int = None) -> Dict[str, Any]:
        """Retorna histórico de gerações."""
        try:
            # Filtros baseados em permissões
            current_user_id = getattr(request, 'user_id', None)
            is_admin = getattr(request, 'is_admin', False)
            
            if not is_admin:
                user_id = current_user_id  # Forçar filtro por usuário atual
            
            history = self.document_service.get_generation_history(
                template_id=template_id,
                user_id=user_id
            )
            
            return self.success_response(
                data={'history': history},
                message="Histórico obtido com sucesso"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao obter histórico: {str(e)}")
            return self.error_response("Erro ao obter histórico")
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais de documentos."""
        try:
            # Verificar se usuário tem permissão (apenas admins)
            is_admin = getattr(request, 'is_admin', False)
            if not is_admin:
                return self.error_response("Acesso não autorizado", 403)
            
            stats = self.document_service.get_document_statistics()
            
            return self.success_response(
                data={'statistics': stats},
                message="Estatísticas obtidas com sucesso"
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao obter estatísticas: {str(e)}")
            return self.error_response("Erro ao obter estatísticas") 