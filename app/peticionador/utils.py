"""
Utilitários compartilhados para o módulo peticionador.
Funções auxiliares para normalização e validação de dados.
"""

from datetime import datetime
import re
import logging
import json
from typing import Any, Dict, Union


def normalize_placeholders_list(placeholders_data):
    """
    Normaliza uma lista de placeholders para garantir que seja uma lista de strings.
    
    Args:
        placeholders_data: Lista que pode conter strings ou dicionários com placeholders
    
    Returns:
        List[str]: Lista de strings com as chaves dos placeholders
    """
    if not placeholders_data:
        return []
    
    chaves_normalizadas = []
    
    for item in placeholders_data:
        if isinstance(item, dict):
            # Se for dicionário, extrair a chave
            if "key" in item:
                chaves_normalizadas.append(str(item["key"]))
            elif "chave" in item:
                chaves_normalizadas.append(str(item["chave"]))
            elif "placeholder" in item:
                chaves_normalizadas.append(str(item["placeholder"]))
            else:
                # Se é um dict mas não tem chaves conhecidas, usar o primeiro valor string encontrado
                for value in item.values():
                    if isinstance(value, str):
                        chaves_normalizadas.append(value)
                        break
        elif isinstance(item, str):
            chaves_normalizadas.append(item)
        else:
            # Converter para string como fallback
            chaves_normalizadas.append(str(item))
    
    # Remover duplicatas e strings vazias
    return list(filter(None, list(set(chaves_normalizadas))))


def safe_extract_placeholder_keys(placeholders_data):
    """
    Extrai com segurança as chaves de placeholders de dados que podem estar
    em formatos diferentes (lista de strings ou lista de dicionários).
    
    Args:
        placeholders_data: Dados de placeholders em formato variado
    
    Returns:
        List[str]: Lista de chaves de placeholders
    """
    try:
        if not placeholders_data:
            return []
        
        # Se já é uma lista de strings
        if isinstance(placeholders_data, list) and placeholders_data:
            if isinstance(placeholders_data[0], str):
                return placeholders_data
            elif isinstance(placeholders_data[0], dict):
                return normalize_placeholders_list(placeholders_data)
        
        # Se é um único item
        if isinstance(placeholders_data, (str, dict)):
            return normalize_placeholders_list([placeholders_data])
        
        # Fallback para outros tipos
        return normalize_placeholders_list(placeholders_data)
        
    except Exception as e:
        # Log do erro mas não falhar
        logging.error(f"Erro ao extrair chaves de placeholders: {e}")
        return []


def validate_placeholder_format(chave):
    """
    Valida se uma string é um formato válido para placeholder.
    
    Args:
        chave (str): String a ser validada
    
    Returns:
        bool: True se é válida, False caso contrário
    """
    if not isinstance(chave, str) or not chave.strip():
        return False
    
    # Verificar se contém apenas caracteres válidos
    return bool(re.match(r'^[a-zA-Z0-9_]+$', chave.strip()))


def clean_placeholder_key(chave):
    """
    Limpa uma chave de placeholder removendo caracteres inválidos.
    
    Args:
        chave (str): Chave a ser limpa
    
    Returns:
        str: Chave limpa
    """
    if not isinstance(chave, str):
        chave = str(chave)
    
    # Remover caracteres especiais, manter apenas letras, números e underscore
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', chave.strip())
    
    # Remover underscores múltiplos consecutivos
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remover underscore do início e fim
    cleaned = cleaned.strip('_')
    
    return cleaned if cleaned else 'placeholder'


def log_placeholder_operation(operation, modelo_id, details=None):
    """
    Log seguro de operações com placeholders.
    
    Args:
        operation (str): Tipo de operação (sync, create, update, etc.)
        modelo_id (int): ID do modelo
        details (dict, optional): Detalhes adicionais
    """
    logger = logging.getLogger(__name__)
    
    log_data = {
        "operation": operation,
        "modelo_id": modelo_id,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        log_data.update(details)
    
    # Sanitizar dados sensíveis antes do log
    sanitized_data = {k: v for k, v in log_data.items() 
                     if not any(sensitive in str(k).lower() 
                               for sensitive in ['password', 'token', 'secret'])}
    
    logger.info(f"Placeholder operation: {sanitized_data}")


def handle_placeholder_extraction_error(error, modelo_id, document_id=None):
    """
    Manipula erros de extração de placeholders de forma consistente.
    
    Args:
        error: Exceção capturada
        modelo_id (int): ID do modelo
        document_id (str, optional): ID do documento Google
    
    Returns:
        tuple: (success: bool, message: str, data: list)
    """
    logger = logging.getLogger(__name__)
    
    error_msg = str(error)
    
    # Log do erro com contexto
    log_placeholder_operation(
        "extraction_error",
        modelo_id,
        {
            "error": error_msg,
            "document_id": document_id,
            "error_type": type(error).__name__
        }
    )
    
    # Determinar mensagem amigável baseada no tipo de erro
    if "unhashable type" in error_msg:
        user_message = "Erro interno na estrutura de dados. Problema foi registrado e será corrigido."
    elif "permission" in error_msg.lower() or "unauthorized" in error_msg.lower():
        user_message = "Sem permissão para acessar o documento Google. Verifique as credenciais."
    elif "not found" in error_msg.lower():
        user_message = "Documento Google não encontrado. Verifique o ID do documento."
    elif "timeout" in error_msg.lower():
        user_message = "Timeout ao acessar o documento. Tente novamente em alguns minutos."
    else:
        user_message = f"Erro ao extrair placeholders: {error_msg}"
    
    return False, user_message, []


def safe_serialize_model(obj, fallback_value=None) -> Union[Dict, Any]:
    """
    Serializa de forma segura um objeto SQLAlchemy para JSON.
    
    Args:
        obj: Objeto a ser serializado
        fallback_value: Valor de retorno em caso de erro
        
    Returns:
        Dict ou fallback_value: Dicionário serializável ou valor padrão
    """
    if obj is None:
        return fallback_value
    
    # Se tem método to_json_safe, usar ele
    if hasattr(obj, 'to_json_safe'):
        try:
            return obj.to_json_safe()
        except Exception as e:
            logging.warning(f"Erro em to_json_safe: {e}")
    
    # Se tem método to_dict, usar ele
    if hasattr(obj, 'to_dict'):
        try:
            return obj.to_dict()
        except Exception as e:
            logging.warning(f"Erro em to_dict: {e}")
    
    # Se tem método __json__, usar ele
    if hasattr(obj, '__json__'):
        try:
            return obj.__json__()
        except Exception as e:
            logging.warning(f"Erro em __json__: {e}")
    
    # Última tentativa: extrair atributos manualmente
    try:
        if hasattr(obj, '_sa_instance_state'):
            # É um objeto SQLAlchemy
            data = {}
            for column in obj.__table__.columns:
                value = getattr(obj, column.name, None)
                if isinstance(value, datetime):
                    data[column.name] = value.isoformat() if value else None
                else:
                    data[column.name] = value
            return data
    except Exception as e:
        logging.error(f"Erro na serialização manual: {e}")
    
    # Se nada funcionar, retornar o fallback
    return fallback_value or {"error": "Não foi possível serializar o objeto"}


def safe_json_dumps(obj, default=None):
    """
    json.dumps seguro que tenta serializar objetos SQLAlchemy.
    
    Args:
        obj: Objeto para serializar
        default: Função de fallback
        
    Returns:
        str: JSON string
    """
    def json_serializer(o):
        # Tentar serializar objetos SQLAlchemy
        if hasattr(o, 'to_json_safe'):
            return o.to_json_safe()
        if hasattr(o, 'to_dict'):
            return o.to_dict()
        if hasattr(o, '__json__'):
            return o.__json__()
        if isinstance(o, datetime):
            return o.isoformat()
        if default:
            return default(o)
        raise TypeError(f"Object of type {type(o)} is not JSON serializable")
    
    return json.dumps(obj, default=json_serializer, ensure_ascii=False)


def get_enum_display_name(enum_value):
    """
    Retorna o nome de exibição de um valor de enum.
    
    Args:
        enum_value: Valor do enum
    
    Returns:
        str: Nome de exibição ou string vazia
    """
    if enum_value is None:
        return ""
    
    if hasattr(enum_value, 'value'):
        return str(enum_value.value)
    
    return str(enum_value)