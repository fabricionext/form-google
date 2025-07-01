"""
Configurações centralizadas do sistema peticionador.
"""

import os
from typing import Optional

def _get_database_uri():
    """Constrói a URI do banco de dados a partir das variáveis de ambiente."""
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Use a DATABASE_URL diretamente se fornecida
        return database_url

    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASS')
    db_host = os.environ.get('DB_HOST')
    db_port = os.environ.get('DB_PORT', '5432')  # Default para 5432
    db_name = os.environ.get('DB_NAME')

    if all([db_user, db_pass, db_host, db_port, db_name]):
        return f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    return 'sqlite:///peticionador.db'


class BaseConfig:
    """Configuração base."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hora
    
    # Database
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'echo': False
    }
    
    # Google Drive API
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')
    GOOGLE_SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents'
    ]
    
    # Cache (Redis)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutos
    
    # Celery (async tasks)
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/peticionador.log')
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/2')
    RATELIMIT_HEADERS_ENABLED = True
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'doc', 'docx', 'pdf'}
    
    # Application specific
    APP_NAME = "Sistema Peticionador"
    APP_VERSION = "2.0.0"
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
    
    # Monitoring
    ENABLE_METRICS = os.environ.get('ENABLE_METRICS', 'False').lower() == 'true'
    METRICS_PORT = int(os.environ.get('METRICS_PORT', 9090))


class DevelopmentConfig(BaseConfig):
    """Configuração para desenvolvimento."""
    
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_ENGINE_OPTIONS = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': True  # Log SQL queries
    }
    
    # Security (relaxed for dev)
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Disable CSRF for easier testing
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    # Google (use test credentials)
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID_DEV', 'dev-client-id')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET_DEV', 'dev-client-secret')


class TestingConfig(BaseConfig):
    """Configuração para testes."""
    
    TESTING = True
    DEBUG = False
    
    # Database (in-memory)
    DATABASE_URL = 'sqlite:///:memory:'
    
    # Security
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    
    # Cache
    CACHE_TYPE = 'null'  # Disable cache during tests
    
    # Logging
    LOG_LEVEL = 'WARNING'  # Reduce noise during tests


class ProductionConfig(BaseConfig):
    """Configuração para produção."""
    
    DEBUG = False
    TESTING = False
    
    # Database - A URI já é pega pela BaseConfig, mas podemos garantir aqui.
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Google credentials
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    
    # Logging
    LOG_LEVEL = 'INFO'
    
    # Enable all security features
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
    
    @classmethod
    def validate(cls):
        """Valida configurações obrigatórias para produção."""
        if not cls.SQLALCHEMY_DATABASE_URI or 'sqlite' in cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL ou variáveis DB_* são obrigatórias para produção e não pode ser SQLite.")
        
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY environment variable is required for production")
        
        if not cls.GOOGLE_CLIENT_ID or not cls.GOOGLE_CLIENT_SECRET:
            raise ValueError("Google credentials are required for production")


# Configuration mapping
CONFIG_MAP = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: Optional[str] = None) -> BaseConfig:
    """
    Retorna a configuração baseada no ambiente.
    
    Args:
        config_name: Nome da configuração ou None para usar FLASK_ENV
        
    Returns:
        Classe de configuração apropriada
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    return CONFIG_MAP.get(config_name, DevelopmentConfig)


def validate_config(config: BaseConfig) -> bool:
    """
    Valida configurações obrigatórias.
    
    Args:
        config: Instância de configuração
        
    Returns:
        True se válida, raises ValueError se inválida
    """
    required_google = ['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']
    
    for attr in required_google:
        if not getattr(config, attr, None):
            raise ValueError(f"Configuration {attr} is required")
    
    return True