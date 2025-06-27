"""
Exceções customizadas do sistema peticionador.
"""

from typing import Optional, Dict, Any


class PeticionadorException(Exception):
    """Exceção base do sistema peticionador."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte exceção para dicionário para serialização."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'details': self.details
        }


class ValidationException(PeticionadorException):
    """Exceção para erros de validação."""
    
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.value = value
        details = {'field': field, 'value': str(value) if value is not None else None}
        super().__init__(message, details)


class TemplateValidationException(ValidationException):
    """Exceção para erros de validação de template."""
    pass


class DocumentValidationException(ValidationException):
    """Exceção para erros de validação de documento."""
    pass


class PlaceholderValidationException(ValidationException):
    """Exceção para erros de validação de placeholder."""
    pass


class IntegrationException(PeticionadorException):
    """Exceção para erros de integração com serviços externos."""
    
    def __init__(self, service: str, message: str, error_code: Optional[str] = None):
        self.service = service
        self.error_code = error_code
        details = {'service': service, 'error_code': error_code}
        super().__init__(message, details)


class GoogleDriveException(IntegrationException):
    """Exceção para erros do Google Drive."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, quota_exceeded: bool = False):
        self.quota_exceeded = quota_exceeded
        super().__init__('google_drive', message, error_code)
        self.details['quota_exceeded'] = quota_exceeded


class AuthenticationException(IntegrationException):
    """Exceção para erros de autenticação."""
    
    def __init__(self, message: str, provider: str = 'google'):
        super().__init__(provider, message)


class BusinessException(PeticionadorException):
    """Exceção para erros de regra de negócio."""
    pass


class TemplateNotFoundException(BusinessException):
    """Exceção quando template não é encontrado."""
    
    def __init__(self, template_id: int):
        self.template_id = template_id
        message = f"Template com ID {template_id} não encontrado"
        super().__init__(message, {'template_id': template_id})


class DocumentNotFoundException(BusinessException):
    """Exceção quando documento não é encontrado."""
    
    def __init__(self, document_id: int):
        self.document_id = document_id
        message = f"Documento com ID {document_id} não encontrado"
        super().__init__(message, {'document_id': document_id})


class PlaceholderMismatchException(BusinessException):
    """Exceção quando placeholders não coincidem."""
    
    def __init__(self, missing_placeholders: list, extra_data: list):
        self.missing_placeholders = missing_placeholders
        self.extra_data = extra_data
        message = "Placeholders não coincidem com dados fornecidos"
        details = {
            'missing_placeholders': missing_placeholders,
            'extra_data': extra_data
        }
        super().__init__(message, details)


class PermissionDeniedException(BusinessException):
    """Exceção para acesso negado."""
    
    def __init__(self, resource: str, action: str, user_id: Optional[int] = None):
        self.resource = resource
        self.action = action
        self.user_id = user_id
        message = f"Acesso negado para {action} em {resource}"
        details = {
            'resource': resource,
            'action': action,
            'user_id': user_id
        }
        super().__init__(message, details)


class ProcessingException(PeticionadorException):
    """Exceção para erros durante processamento."""
    
    def __init__(self, stage: str, message: str, recoverable: bool = False):
        self.stage = stage
        self.recoverable = recoverable
        details = {'stage': stage, 'recoverable': recoverable}
        super().__init__(message, details)


class DocumentGenerationException(ProcessingException):
    """Exceção para erros na geração de documento."""
    
    def __init__(self, template_id: int, message: str, error_details: Optional[Dict] = None):
        self.template_id = template_id
        self.error_details = error_details or {}
        details = {
            'template_id': template_id,
            'error_details': self.error_details
        }
        super().__init__('document_generation', message)
        self.details.update(details)


class CacheException(PeticionadorException):
    """Exceção para erros de cache."""
    
    def __init__(self, key: str, operation: str, message: str):
        self.key = key
        self.operation = operation
        details = {'key': key, 'operation': operation}
        super().__init__(message, details)


class ConfigurationException(PeticionadorException):
    """Exceção para erros de configuração."""
    
    def __init__(self, config_key: str, message: str):
        self.config_key = config_key
        details = {'config_key': config_key}
        super().__init__(message, details)


class RateLimitException(PeticionadorException):
    """Exceção para rate limiting."""
    
    def __init__(self, limit: str, retry_after: Optional[int] = None):
        self.limit = limit
        self.retry_after = retry_after
        message = f"Rate limit excedido: {limit}"
        details = {'limit': limit, 'retry_after': retry_after}
        super().__init__(message, details)


# Helper functions para criar exceções comuns
def template_not_found(template_id: int) -> TemplateNotFoundException:
    """Helper para criar exceção de template não encontrado."""
    return TemplateNotFoundException(template_id)


def document_not_found(document_id: int) -> DocumentNotFoundException:
    """Helper para criar exceção de documento não encontrado."""
    return DocumentNotFoundException(document_id)


def validation_error(field: str, message: str, value: Any = None) -> ValidationException:
    """Helper para criar erro de validação."""
    return ValidationException(field, message, value)


def google_drive_error(message: str, error_code: Optional[str] = None) -> GoogleDriveException:
    """Helper para criar erro do Google Drive."""
    return GoogleDriveException(message, error_code)


def permission_denied(resource: str, action: str, user_id: Optional[int] = None) -> PermissionDeniedException:
    """Helper para criar erro de permissão."""
    return PermissionDeniedException(resource, action, user_id)


# Exceções adicionais para compatibilidade com a nova arquitetura
class NotFoundException(BusinessException):
    """Exceção genérica para recursos não encontrados."""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: Any = None):
        self.resource_type = resource_type
        self.resource_id = resource_id
        details = {
            'resource_type': resource_type,
            'resource_id': resource_id
        }
        super().__init__(message, details)


class UnauthorizedException(BusinessException):
    """Exceção para usuário não autenticado."""
    
    def __init__(self, message: str = "Acesso não autorizado"):
        super().__init__(message)


class ClientNotFoundException(NotFoundException):
    """Exceção quando cliente não é encontrado."""
    
    def __init__(self, client_id: Any = None, cpf: str = None):
        identifier = f"ID {client_id}" if client_id else f"CPF {cpf}" if cpf else "critério fornecido"
        message = f"Cliente com {identifier} não encontrado"
        details = {'client_id': client_id, 'cpf': cpf}
        super().__init__(message, 'client', client_id or cpf)
        self.details.update(details)


class FormProcessingException(ProcessingException):
    """Exceção para erros no processamento de formulários."""
    
    def __init__(self, message: str, form_errors: Optional[Dict] = None, template_id: Optional[int] = None):
        self.form_errors = form_errors or {}
        self.template_id = template_id
        details = {
            'form_errors': self.form_errors,
            'template_id': template_id
        }
        super().__init__('form_processing', message)
        self.details.update(details)


class FormValidationException(ValidationException):
    """Exceção para erros de validação de formulário."""
    
    def __init__(self, field: str, message: str, value: Any = None, rule: str = None):
        self.rule = rule
        super().__init__(field, message, value)
        self.details['rule'] = rule


class SchemaException(PeticionadorException):
    """Exceção para erros de schema de formulário."""
    
    def __init__(self, message: str, schema_errors: Optional[Dict] = None):
        self.schema_errors = schema_errors or {}
        details = {'schema_errors': self.schema_errors}
        super().__init__(message, details)


class FieldNotFoundException(BusinessException):
    """Exceção quando campo não é encontrado no template."""
    
    def __init__(self, field_name: str, template_id: Optional[int] = None):
        self.field_name = field_name
        self.template_id = template_id
        message = f"Campo '{field_name}' não encontrado"
        if template_id:
            message += f" no template {template_id}"
        details = {'field_name': field_name, 'template_id': template_id}
        super().__init__(message, details)


class ServiceException(PeticionadorException):
    """Exceção base para erros de service."""
    
    def __init__(self, service_name: str, message: str, method: Optional[str] = None):
        self.service_name = service_name
        self.method = method
        details = {'service': service_name, 'method': method}
        super().__init__(message, details)


class TemplateServiceException(ServiceException):
    """Exceção para erros do TemplateService."""
    
    def __init__(self, message: str, method: Optional[str] = None):
        super().__init__('TemplateService', message, method)


class DocumentServiceException(ServiceException):
    """Exceção para erros do DocumentService."""
    
    def __init__(self, message: str, method: Optional[str] = None):
        super().__init__('DocumentService', message, method)


class FormServiceException(ServiceException):
    """Exceção para erros do FormService."""
    
    def __init__(self, message: str, method: Optional[str] = None):
        super().__init__('FormService', message, method)


# Alias para compatibilidade com importações existentes
DocumentGenerationError = DocumentGenerationException
TemplateNotFound = TemplateNotFoundException
DocumentNotFound = DocumentNotFoundException


# Helpers adicionais para as novas exceções
def form_processing_error(message: str, form_errors: Optional[Dict] = None, template_id: Optional[int] = None) -> FormProcessingException:
    """Helper para criar erro de processamento de formulário."""
    return FormProcessingException(message, form_errors, template_id)


def field_not_found(field_name: str, template_id: Optional[int] = None) -> FieldNotFoundException:
    """Helper para criar erro de campo não encontrado."""
    return FieldNotFoundException(field_name, template_id)


def schema_error(message: str, schema_errors: Optional[Dict] = None) -> SchemaException:
    """Helper para criar erro de schema."""
    return SchemaException(message, schema_errors)


def service_error(service_name: str, message: str, method: Optional[str] = None) -> ServiceException:
    """Helper para criar erro de service."""
    return ServiceException(service_name, message, method)