"""
Peticionador Utils Package
=========================

Módulo organizado de utilitários para o sistema peticionador.
Dividido em categorias específicas para melhor organização.
"""


# Importar funções legacy reais
from .document_utils import extract_placeholders_keys_only

from .placeholder_utils import *
from .document_utils import *
from .form_utils import *

__all__ = [
    # Funções legacy mantidas para compatibilidade
    'safe_extract_placeholder_keys',
    'validate_placeholder_format', 
    'clean_placeholder_key',
    'get_enum_display_name',
    'normalize_placeholders_list',
    'handle_placeholder_extraction_error',
    'log_placeholder_operation',
    
    # Novas funções organizadas
    'categorize_placeholder_key',
    'detect_persona_patterns',
    'determine_field_type_from_key',
    'format_label_from_key',
    'is_required_field_key',
    'generate_placeholder_text_from_key',
    'build_dynamic_form',
    'determine_client_map_key',
    'get_choices_for_field_key',
    'extract_placeholders_from_document',
    'extract_placeholders_keys_only',
    'generate_preview_html',
    'analyze_document_personas'
]