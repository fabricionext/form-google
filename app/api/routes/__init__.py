"""
Registro de Rotas da Nova Arquitetura
=====================================

Este módulo centraliza o registro de todos os blueprints da nova arquitetura,
facilitando a migração gradual e o gerenciamento de rotas.
"""

from flask import Flask

from .auth import auth_bp
from .clients import clients_bp
from .google_auth import google_auth_bp
from .document_analysis import document_analysis_bp
from .template_conversion import template_conversion_bp
from .service_account_test import service_account_test_bp
from .cache_management import cache_management_bp
from .template_import import template_import_bp
from .preview_generation import preview_generation_bp

# Lista de blueprints disponíveis
AVAILABLE_BLUEPRINTS = [
    ('auth_bp', auth_bp, 'Autenticação'),
    ('clients_bp', clients_bp, 'Clientes'),
    ('google_auth_bp', google_auth_bp, 'Autenticação Google'),
    ('document_analysis_bp', document_analysis_bp, 'Análise de Documentos'),
    ('template_conversion_bp', template_conversion_bp, 'Conversão de Templates'),
    ('service_account_test_bp', service_account_test_bp, 'Teste Conta de Serviço'),
    ('cache_management_bp', cache_management_bp, 'Gerenciamento de Cache'),
    ('template_import_bp', template_import_bp, 'Importação de Templates'),
    ('preview_generation_bp', preview_generation_bp, 'Geração de Previews'),
    ('templates_bp', None, 'Templates'), # Carregado dinamicamente
    ('forms_bp', None, 'Formulários'),   # Carregado dinamicamente  
    ('documents_bp', None, 'Documentos'), # Carregado dinamicamente
]

# Feature flags para controlar quais blueprints registrar
FEATURE_FLAGS = {
    'NEW_AUTH_API': True,       # ✅ Nova API de autenticação - FASE 3 Completa
    'NEW_CLIENTS_API': True,    # ✅ Nova API de clientes - FASE 3 Completa
    'GOOGLE_AUTH_API': True,    # ✅ Autenticação Google OAuth 2.0 - FASE 4
    'DOCUMENT_ANALYSIS_API': True,  # ✅ Análise de documentos Google Docs - FASE 4
    'TEMPLATE_CONVERSION_API': True,  # ✅ Conversão automática de templates - FASE 4
    'SERVICE_ACCOUNT_TEST_API': True,  # ✅ Teste de conta de serviço - FASE 4
    'CACHE_MANAGEMENT_API': True,  # ✅ Gerenciamento de cache - FASE 4
    'TEMPLATE_IMPORT_API': True,  # ✅ Importação real de templates - FASE 4
    'PREVIEW_GENERATION_API': True,  # ✅ Geração de previews dinâmicos - FASE 4
    'NEW_TEMPLATES_API': True,  # ✅ Nova API de templates - FASE 4 Implementada
    'NEW_FORMS_API': True,      # ✅ Nova API de formulários - FASE 4 Implementada
    'NEW_DOCUMENTS_API': True,  # ✅ Nova API de documentos - FASE 4 Implementada
}


def register_new_api_routes(app: Flask):
    """
    Registra todas as rotas da nova arquitetura na aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    try:
        registered_count = 0
        
        # Registrar blueprints baseado em feature flags
        if FEATURE_FLAGS.get('NEW_AUTH_API', False):
            app.register_blueprint(auth_bp)
            app.logger.info("✅ Blueprint de autenticação registrado: /api/auth")
            registered_count += 1
        
        if FEATURE_FLAGS.get('NEW_CLIENTS_API', False):
            app.register_blueprint(clients_bp)
            app.logger.info("✅ Blueprint de clientes registrado: /api/clients")
            registered_count += 1
        
        if FEATURE_FLAGS.get('GOOGLE_AUTH_API', False):
            app.register_blueprint(google_auth_bp)
            app.logger.info("✅ Blueprint de autenticação Google registrado: /api/google")
            registered_count += 1
        
        if FEATURE_FLAGS.get('DOCUMENT_ANALYSIS_API', False):
            app.register_blueprint(document_analysis_bp)
            app.logger.info("✅ Blueprint de análise de documentos registrado: /api/documents")
            registered_count += 1
        
        if FEATURE_FLAGS.get('TEMPLATE_CONVERSION_API', False):
            app.register_blueprint(template_conversion_bp)
            app.logger.info("✅ Blueprint de conversão de templates registrado: /api/template-conversion")
            registered_count += 1
        
        if FEATURE_FLAGS.get('SERVICE_ACCOUNT_TEST_API', False):
            app.register_blueprint(service_account_test_bp)
            app.logger.info("✅ Blueprint de teste da conta de serviço registrado: /api/service-account")
            registered_count += 1
        
        if FEATURE_FLAGS.get('CACHE_MANAGEMENT_API', False):
            app.register_blueprint(cache_management_bp)
            app.logger.info("✅ Blueprint de gerenciamento de cache registrado: /api/cache")
            registered_count += 1
        
        if FEATURE_FLAGS.get('TEMPLATE_IMPORT_API', False):
            app.register_blueprint(template_import_bp)
            app.logger.info("✅ Blueprint de importação de templates registrado: /api/import")
            registered_count += 1
        
        if FEATURE_FLAGS.get('PREVIEW_GENERATION_API', False):
            app.register_blueprint(preview_generation_bp)
            app.logger.info("✅ Blueprint de geração de previews registrado: /api/preview")
            registered_count += 1
        
        # FASE 4 - APIs expandidas
        if FEATURE_FLAGS.get('NEW_TEMPLATES_API', False):
            try:
                from .templates import templates_bp
                app.register_blueprint(templates_bp)
                app.logger.info("✅ Blueprint de templates registrado: /api/templates")
                registered_count += 1
            except ImportError as e:
                app.logger.warning(f"⚠️  Blueprint de templates não pode ser carregado: {e}")
        
        if FEATURE_FLAGS.get('NEW_FORMS_API', False):
            try:
                from .forms import forms_bp
                app.register_blueprint(forms_bp)
                app.logger.info("✅ Blueprint de formulários registrado: /api/forms")
                registered_count += 1
            except ImportError as e:
                app.logger.warning(f"⚠️  Blueprint de formulários não pode ser carregado: {e}")
        
        if FEATURE_FLAGS.get('NEW_DOCUMENTS_API', False):
            try:
                from .documents import documents_bp
                app.register_blueprint(documents_bp)
                app.logger.info("✅ Blueprint de documentos registrado: /api/documents")
                registered_count += 1
            except ImportError as e:
                app.logger.warning(f"⚠️  Blueprint de documentos não pode ser carregado: {e}")
        
        app.logger.info(f"🎯 Nova arquitetura: {registered_count} blueprints registrados com sucesso")
        
        # Log de feature flags ativas
        active_flags = [k for k, v in FEATURE_FLAGS.items() if v]
        app.logger.info(f"🚀 Feature flags ativas: {', '.join(active_flags)}")
        
        return registered_count
        
    except Exception as e:
        app.logger.error(f"❌ Erro ao registrar blueprints da nova arquitetura: {str(e)}")
        raise


def get_api_status():
    """
    Retorna status das APIs da nova arquitetura.
    
    Returns:
        dict: Status de cada API
    """
    return {
        'new_architecture_enabled': True,
        'feature_flags': FEATURE_FLAGS,
        'available_blueprints': [
            {
                'name': name,
                'description': desc,
                'enabled': FEATURE_FLAGS.get(name.upper().replace('_BP', '_API'), False),
                'url_prefix': bp.url_prefix if bp and hasattr(bp, 'url_prefix') else f'/api/{name.replace("_bp", "")}'
            }
            for name, bp, desc in AVAILABLE_BLUEPRINTS
        ]
    }


def toggle_feature_flag(flag_name: str, enabled: bool = None):
    """
    Ativa/desativa feature flag dinamicamente.
    
    Args:
        flag_name: Nome da feature flag
        enabled: Novo estado (None para toggle)
    
    Returns:
        dict: Resultado da operação
    """
    if flag_name not in FEATURE_FLAGS:
        return {
            'success': False,
            'message': f"Feature flag '{flag_name}' não encontrada",
            'available_flags': list(FEATURE_FLAGS.keys())
        }
    
    old_value = FEATURE_FLAGS[flag_name]
    
    if enabled is None:
        FEATURE_FLAGS[flag_name] = not old_value
    else:
        FEATURE_FLAGS[flag_name] = enabled
    
    new_value = FEATURE_FLAGS[flag_name]
    
    return {
        'success': True,
        'flag_name': flag_name,
        'old_value': old_value,
        'new_value': new_value,
        'message': f"Feature flag '{flag_name}': {old_value} → {new_value}"
    }


# Função de conveniência para importação
__all__ = [
    'register_new_api_routes',
    'get_api_status',
    'toggle_feature_flag',
    'FEATURE_FLAGS'
] 