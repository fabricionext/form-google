"""
Constantes centralizadas do sistema peticionador.
Versão refatorada com melhor organização e eliminação de duplicações.
"""

from enum import Enum

# =============================================================================
# ENUMS PRINCIPAIS - FONTE ÚNICA DA VERDADE
# =============================================================================

class DocumentStatus(Enum):
    """Status values for document generation process."""
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentTypes(Enum):
    """Types of documents that can be generated."""
    FICHA_CADASTRAL_PF = "ficha_cadastral_pf"
    FICHA_CADASTRAL_PJ = "ficha_cadastral_pj"
    DEFESA_PREVIA = "defesa_previa"
    RECURSO_JARI = "recurso_jari"
    TERMO_ACORDO = "termo_acordo"
    ACAO_ANULATORIA = "acao_anulatoria"


class PlaceholderType(Enum):
    """Types of data for placeholders."""
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    EMAIL = "email"
    CPF = "cpf"
    PHONE = "phone"
    CURRENCY = "currency"
    SELECT = "select"
    TEXTAREA = "textarea"
    CNPJ = "cnpj"


class PlaceholderCategory(Enum):
    """Categories for organizing placeholders."""
    CLIENTE = "cliente"
    VEICULO = "veiculo"
    DOCUMENTO = "documento"
    AUTORIDADE = "autoridade"
    OUTROS = "outros"


# =============================================================================
# CONFIGURAÇÕES POR CONTEXTO - ESTRUTURA HIERÁRQUICA
# =============================================================================

# Google Drive Configuration
GOOGLE_DRIVE_CONFIG = {
    'TEMPLATES_FOLDER_ID': '1LvPsvml7bkN2TQjyAqnNAYAy7qRebrDf',
    'CLIENT_FOLDERS_ROOT': 'Clientes',
    'FOLDER_NAMES': {
        'TEMPLATES': 'templates',
        'GENERATED': 'generated_documents', 
        'TEMP': 'temp'
    },
    'DOCUMENT_TYPES_SUBFOLDERS': {
        DocumentTypes.FICHA_CADASTRAL_PF.value: 'Fichas Cadastrais',
        DocumentTypes.FICHA_CADASTRAL_PJ.value: 'Fichas Cadastrais',
        DocumentTypes.DEFESA_PREVIA.value: 'Defesas e Recursos',
        DocumentTypes.RECURSO_JARI.value: 'Defesas e Recursos',
        DocumentTypes.TERMO_ACORDO.value: 'Termos de Acordo',
        DocumentTypes.ACAO_ANULATORIA.value: 'Ações Anulatórias'
    },
    'RETRY_ATTEMPTS': 3,
    'RETRY_DELAY': 2,
    'CIRCUIT_BREAKER_THRESHOLD': 5,
    'CIRCUIT_BREAKER_TIMEOUT': 300,
    'MAX_FILE_SIZE_MB_TEMPLATE': 10,
    'MAX_FILE_SIZE_MB_GENERATED': 50
}

# Cache Configuration
CACHE_CONFIG = {
    "clients": {
        "ttl": 3600,  # 1 hour
        "key_pattern": "client:cpf:{cpf}"
    },
    "authorities": {
        "ttl": 86400,  # 24 hours
        "key_pattern": "authority:name:{name}"
    },
    "templates": {
        "ttl": 300,  # 5 minutes
        "key_pattern": "template:id:{id}"
    },
    "placeholders": {
        "ttl": 1800,  # 30 minutes
        "key_pattern": "placeholders:template:{template_id}"
    },
    "google_token": {
        "ttl": 3000,  # 50 minutes
        "key_pattern": "google:access_token"
    },
    "form_structure": {
        "ttl": 900,  # 15 minutes
        "key_pattern": "form:template:{template_id}"
    }
}

# Validation Configuration
VALIDATION_CONFIG = {
    'PATTERNS': {
        'CPF': r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
        'CNPJ': r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
        'PHONE': r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
        'EMAIL': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'CEP': r'^\d{5}-\d{3}$',
        'PROCESS_CNJ': r'^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$'
    },
    'LIMITS': {
        'MAX_PLACEHOLDER_NAME_LENGTH': 100,
        'MAX_TEMPLATE_NAME_LENGTH': 200,
        'MAX_DOCUMENT_TITLE_LENGTH': 300,
        'MAX_CLIENT_NAME_LENGTH': 100
    },
    'RULES': {
        'cpf': {
            'required': True,
            'pattern': 'CPF',  # Reference to PATTERNS
            'message': 'CPF deve estar no formato 000.000.000-00'
        },
        'email': {
            'required': False,
            'pattern': 'EMAIL',
            'message': 'Email deve ter formato válido'
        },
        'phone': {
            'required': False,
            'pattern': 'PHONE',
            'message': 'Telefone deve estar no formato (00) 0000-0000'
        },
        'name': {
            'required': True,
            'min_length': 2,
            'max_length': 100,
            'message': 'Nome deve ter entre 2 e 100 caracteres'
        }
    }
}

# API Rate Limiting
API_RATE_LIMITS = {
    # Legacy Rate Limits
    'DOCUMENT_GENERATION_PER_MINUTE': 5,
    'GLOBAL_API_CALLS_PER_HOUR': 100,
    'LOGIN_ATTEMPTS_PER_MINUTE': 5,
    'GOOGLE_DRIVE_REQUESTS_PER_MINUTE': 100,
    'GOOGLE_DOCS_REQUESTS_PER_MINUTE': 60,
    'CLIENT_SEARCH_REQUESTS_PER_MINUTE': 300,
    'AUTHORITY_SEARCH_REQUESTS_PER_MINUTE': 200,
    
    # Nova API - FASE 4 (Rate limits em formato string para Flask-Limiter)
    # Autenticação
    'auth_login': "5/minute",
    'auth_logout': "10/minute", 
    'auth_validate': "30/minute",
    
    # Clientes
    'clients_list': "60/minute",
    'clients_get': "120/minute",
    'clients_create': "10/minute",
    'clients_update': "20/minute",
    'clients_delete': "5/minute",
    'clients_search': "100/minute",
    'clients_validate': "200/minute",
    
    # Templates - FASE 4
    'templates_list': "60/minute",
    'templates_get': "120/minute",
    'templates_create': "10/minute",
    'templates_update': "20/minute",
    'templates_delete': "5/minute",
    'templates_sync': "5/minute",
    'templates_preview': "30/minute",
    'templates_stats': "20/minute",
    
    # Forms - FASE 4
    'forms_schema': "60/minute",
    'forms_validate': "120/minute",
    'forms_validate_field': "200/minute",
    'forms_suggestions': "120/minute",
    'forms_conditional': "60/minute",
    'forms_submit': "20/minute",
    'forms_templates': "60/minute",
    'forms_metadata': "60/minute",
    'forms_config': "10/minute",
    'forms_export': "10/minute",
    'forms_analytics': "20/minute",
    
    # Documents - FASE 4
    'documents_generate': "10/minute",
    'documents_status': "120/minute", 
    'documents_list': "60/minute",
    'documents_get': "120/minute",
    'documents_download': "30/minute",
    'documents_regenerate': "5/minute",
    'documents_delete': "10/minute",
    'documents_history': "30/minute",
    'documents_stats': "20/minute"
}

# Legal Deadlines (in days)
LEGAL_DEADLINES = {
    DocumentTypes.DEFESA_PREVIA.value: 15,
    DocumentTypes.RECURSO_JARI.value: 30,
    DocumentTypes.ACAO_ANULATORIA.value: 120,
    DocumentTypes.TERMO_ACORDO.value: 30
}

# Document Complexity Levels
DOCUMENT_COMPLEXITY = {
    DocumentTypes.FICHA_CADASTRAL_PF.value: 'simple',
    DocumentTypes.FICHA_CADASTRAL_PJ.value: 'simple',
    DocumentTypes.DEFESA_PREVIA.value: 'medium',
    DocumentTypes.RECURSO_JARI.value: 'medium',
    DocumentTypes.TERMO_ACORDO.value: 'medium',
    DocumentTypes.ACAO_ANULATORIA.value: 'complex'
}

# File Naming Configuration
FILE_NAMING_CONFIG = {
    'MAX_LENGTH': 150,
    'DATE_FORMAT': '%d-%m-%Y',
    'TIMESTAMP_FORMAT': '%H%M%S',
    'INVALID_CHARS': r'[<>:"/\\|?*]',
    'TYPE_MAPPINGS': {
        DocumentTypes.FICHA_CADASTRAL_PF.value: "Ficha_Cadastral_PF",
        DocumentTypes.FICHA_CADASTRAL_PJ.value: "Ficha_Cadastral_PJ",
        DocumentTypes.DEFESA_PREVIA.value: "Defesa_Previa",
        DocumentTypes.RECURSO_JARI.value: "Recurso_JARI",
        DocumentTypes.TERMO_ACORDO.value: "Termo_Acordo",
        DocumentTypes.ACAO_ANULATORIA.value: "Acao_Anulatoria"
    }
}

# Form Generation Configuration
FORM_CONFIG = {
    'MAX_AUTHORS': 3,
    'MAX_AUTHORITIES': 3,
    'REQUIRED_FIELDS_HIGHLIGHT': True,
    'ENABLE_AUTOCOMPLETE': True,
    'ENABLE_VALIDATION': True,
    'ENABLE_CONDITIONAL_LOGIC': True,
    'FIELD_MASKS': {
        'cpf': '###.###.###-##',
        'cnpj': '##.###.###/####-##',
        'phone': '(##) #####-####',
        'cep': '#####-###'
    },
    'FIELD_TYPES_MAPPING': {
        PlaceholderType.TEXT.value: 'Text Input',
        PlaceholderType.EMAIL.value: 'Email Input',
        PlaceholderType.DATE.value: 'Date Picker',
        PlaceholderType.NUMBER.value: 'Number Input',
        PlaceholderType.CURRENCY.value: 'Currency Input',
        PlaceholderType.PHONE.value: 'Phone Input',
        PlaceholderType.CPF.value: 'CPF Input',
        PlaceholderType.CNPJ.value: 'CNPJ Input',
        PlaceholderType.TEXTAREA.value: 'Text Area',
        PlaceholderType.SELECT.value: 'Select Dropdown'
    },
    'VALIDATION_RULES': {
        'required': 'Campo obrigatório',
        'min_length': 'Mínimo de {min} caracteres',
        'max_length': 'Máximo de {max} caracteres',
        'email_format': 'Email inválido',
        'cpf_format': 'CPF inválido',
        'cnpj_format': 'CNPJ inválido',
        'phone_format': 'Telefone inválido',
        'date_format': 'Data inválida',
        'number_range': 'Número deve estar entre {min} e {max}',
        'currency_format': 'Valor monetário inválido'
    }
}

# Monitoring and Metrics Configuration
METRICS_CONFIG = {
    'DOCUMENT_GENERATION_TIME_BUCKETS': [0.5, 1, 2, 5, 10, 30, 60],
    'ERROR_RATE_THRESHOLD': 0.05,  # 5%
    'RESPONSE_TIME_THRESHOLD_SECONDS': 30,
    'CACHE_HIT_RATE_THRESHOLD': 0.8,  # 80%
    'PERFORMANCE_MONITORING_ENABLED': True,
    'METRICS_RETENTION_DAYS': 90
}

# Security Configuration
SECURITY_CONFIG = {
    'MAX_FILE_UPLOAD_SIZE_MB': 50,
    'ALLOWED_UPLOAD_FILE_TYPES': ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png'],
    'SESSION_TIMEOUT_MINUTES': 120,
    'MAX_LOGIN_ATTEMPTS': 5,
    'PASSWORD_MIN_LENGTH': 8,
    'ENABLE_2FA': False,
    'REQUIRE_HTTPS': True,
    'CSRF_PROTECTION': True
}

# Backup and Recovery Configuration
BACKUP_CONFIG = {
    'AUTO_BACKUP_ENABLED': True,
    'BACKUP_FREQUENCY_HOURS': 24,
    'RETENTION_DAYS': 30,
    'BACKUP_DESTINATIONS': ['google_drive', 'local_storage'],
    'BACKUP_ENCRYPTION': True,
    'INCREMENTAL_BACKUP': True
}

# Feature Flags
FEATURE_FLAGS = {
    'NEW_AUTH_API': True,
    'NEW_CLIENTS_API': True,
    'NEW_TEMPLATES_API': True,
    'NEW_FORMS_API': True,
    'NEW_DOCUMENTS_API': True,
    'ENABLE_BATCH_OPERATIONS': True,
    'ENABLE_ADVANCED_SEARCH': True,
    'ENABLE_DOCUMENT_PREVIEW': True,
    'ENABLE_COLLABORATIVE_EDITING': False,
    'ENABLE_AI_SUGGESTIONS': False,
    'ENABLE_AUDIT_LOGGING': True,
    'ENABLE_SCHEMA_VALIDATION': True,
    'ENABLE_ASYNC_PROCESSING': True,
    'ENABLE_CIRCUIT_BREAKERS': True
}

# =============================================================================
# CONFIGURAÇÕES ESPECIAIS E MAPEAMENTOS
# =============================================================================

# Special Placeholders for conditional processing
SPECIAL_PLACEHOLDERS = {
    "[BLOCO_IMAGEM_NOTIFICACAO]": "image_notification",
    "{{valor_extenso}}": "calculate_extensive_value",
    "{{saldo_pontos}}": "calculate_points_balance",
    "{{data_atual}}": "current_date_formatted",
    "[BLOCO_MULTIPLOS_AUTORES]": "multiple_authors_block",
    "[BLOCO_DADOS_VEICULO]": "vehicle_data_block",
    "[BLOCO_AUTORIDADES]": "authorities_block"
}

# =============================================================================
# CONSTANTES BÁSICAS - FORMATOS E MENSAGENS
# =============================================================================

# Date Formats
DATE_FORMAT_ISO = "%Y-%m-%d"
DATE_FORMAT_BR = "%d/%m/%Y"
DATETIME_FORMAT_ISO = "%Y-%m-%dT%H:%M:%S"
DATETIME_FORMAT_BR = "%d/%m/%Y %H:%M:%S"

# Service Log Levels
SERVICE_LOG_LEVELS = {
    "template_service": "INFO",
    "document_service": "INFO", 
    "placeholder_service": "DEBUG",
    "google_drive_adapter": "WARNING",
    "cache_adapter": "INFO",
    "validation_service": "INFO"
}

# Error Messages
ERROR_MESSAGES = {
    "template_not_found": "Template não encontrado",
    "document_generation_failed": "Falha na geração do documento",
    "invalid_placeholder_data": "Dados de placeholder inválidos",
    "google_auth_failed": "Falha na autenticação com Google",
    "insufficient_permissions": "Permissões insuficientes",
    "validation_failed": "Validação dos dados falhou",
    "cache_error": "Erro no sistema de cache",
    "database_error": "Erro no banco de dados",
    "client_not_found": "Cliente não encontrado",
    "unauthorized_access": "Acesso não autorizado",
    "rate_limit_exceeded": "Limite de requisições excedido"
}

# Audit Events
AUDIT_EVENTS = {
    'TEMPLATE_CREATE': "template_create",
    'TEMPLATE_UPDATE': "template_update",
    'TEMPLATE_DELETE': "template_delete",
    'DOCUMENT_GENERATE': "document_generate",
    'USER_LOGIN': "user_login",
    'USER_LOGOUT': "user_logout",
    'PERMISSION_DENIED': "permission_denied",
    'CLIENT_CREATE': "client_create",
    'CLIENT_UPDATE': "client_update",
    'CLIENT_DELETE': "client_delete"
}

# =============================================================================
# FUNÇÕES AUXILIARES PARA ACESSO DINÂMICO AOS ENUMS
# =============================================================================

def get_document_statuses():
    """Retorna lista de todos os status de documento."""
    return [status.value for status in DocumentStatus]

def get_document_types():
    """Retorna lista de todos os tipos de documento."""
    return [doc_type.value for doc_type in DocumentTypes]

def get_placeholder_types():
    """Retorna lista de todos os tipos de placeholder."""
    return [ph_type.value for ph_type in PlaceholderType]

def get_placeholder_categories():
    """Retorna lista de todas as categorias de placeholder."""
    return [category.value for category in PlaceholderCategory]

# =============================================================================
# ALIASES PARA COMPATIBILIDADE (DEPRECIADOS - USAR ENUMS DIRETAMENTE)
# =============================================================================

# Mantidos temporariamente para não quebrar código existente
# TODO: Remover após migração completa para Enums
CACHE_TTL_CLIENTES = CACHE_CONFIG["clients"]["ttl"]
FIELD_TYPES = FORM_CONFIG['FIELD_TYPES_MAPPING']
VALIDATION_RULES = VALIDATION_CONFIG['RULES']

# Aliases para limites de validação
MAX_TEMPLATE_NAME_LENGTH = VALIDATION_CONFIG['LIMITS']['MAX_TEMPLATE_NAME_LENGTH']
MAX_PLACEHOLDER_NAME_LENGTH = VALIDATION_CONFIG['LIMITS']['MAX_PLACEHOLDER_NAME_LENGTH']
MAX_DOCUMENT_TITLE_LENGTH = VALIDATION_CONFIG['LIMITS']['MAX_DOCUMENT_TITLE_LENGTH']
MAX_CLIENT_NAME_LENGTH = VALIDATION_CONFIG['LIMITS']['MAX_CLIENT_NAME_LENGTH']

# Aliases para listas (geradas dinamicamente dos Enums)
DOCUMENT_STATUSES = get_document_statuses()
PLACEHOLDER_TYPES = get_placeholder_types()
PLACEHOLDER_CATEGORIES = get_placeholder_categories()

# Aliases para padrões regex
REGEX_CPF = VALIDATION_CONFIG['PATTERNS']['CPF']
REGEX_CNPJ = VALIDATION_CONFIG['PATTERNS']['CNPJ'] 
REGEX_PHONE = VALIDATION_CONFIG['PATTERNS']['PHONE']
REGEX_EMAIL = VALIDATION_CONFIG['PATTERNS']['EMAIL']

# Aliases para status de documento individuais
DOCUMENT_STATUS_DRAFT = DocumentStatus.DRAFT.value
DOCUMENT_STATUS_PROCESSING = DocumentStatus.PROCESSING.value
DOCUMENT_STATUS_COMPLETED = DocumentStatus.COMPLETED.value
DOCUMENT_STATUS_FAILED = DocumentStatus.FAILED.value
DOCUMENT_STATUS_CANCELLED = DocumentStatus.CANCELLED.value

# Aliases para tipos de placeholder individuais
PLACEHOLDER_TYPE_TEXT = PlaceholderType.TEXT.value
PLACEHOLDER_TYPE_NUMBER = PlaceholderType.NUMBER.value
PLACEHOLDER_TYPE_DATE = PlaceholderType.DATE.value
PLACEHOLDER_TYPE_EMAIL = PlaceholderType.EMAIL.value
PLACEHOLDER_TYPE_CPF = PlaceholderType.CPF.value
PLACEHOLDER_TYPE_PHONE = PlaceholderType.PHONE.value
PLACEHOLDER_TYPE_CURRENCY = PlaceholderType.CURRENCY.value
PLACEHOLDER_TYPE_SELECT = PlaceholderType.SELECT.value
PLACEHOLDER_TYPE_TEXTAREA = PlaceholderType.TEXTAREA.value

# Aliases para categorias de placeholder individuais
PLACEHOLDER_CATEGORY_CLIENTE = PlaceholderCategory.CLIENTE.value
PLACEHOLDER_CATEGORY_VEICULO = PlaceholderCategory.VEICULO.value
PLACEHOLDER_CATEGORY_DOCUMENTO = PlaceholderCategory.DOCUMENTO.value
PLACEHOLDER_CATEGORY_AUTORIDADE = PlaceholderCategory.AUTORIDADE.value
PLACEHOLDER_CATEGORY_OUTROS = PlaceholderCategory.OUTROS.value