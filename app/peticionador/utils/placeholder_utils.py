"""
Placeholder Utilities
====================

Funções utilitárias para manipulação de placeholders.
Migradas do routes.py para melhor organização.
"""

import re
from typing import Dict, List, Any
from flask import current_app


def categorize_placeholder_key(chave: str) -> str:
    """
    Categoriza automaticamente o placeholder baseado na chave, 
    com priorização para evitar duplicações.
    
    Migrado do routes.py para utils organizados.
    """
    chave_lower = chave.lower()

    # 1. AUTORIDADES DE TRÂNSITO (primeira prioridade para evitar duplicações)
    if chave_lower.startswith("orgao_transito") or "autoridade" in chave_lower:
        return "autoridades"

    # 2. AUTORES NUMERADOS (segunda prioridade) - melhorada para detectar todos os números
    if chave_lower.startswith("autor_"):
        # Melhor regex para detectar autores numerados (autor_1_, autor_2_, autor_10_, etc.)
        match = re.match(r"autor_(\d+)_(.+)", chave_lower)
        if match:
            campo_resto = match.group(2)
            if any(termo in campo_resto for termo in ["endereco", "endereço"]):
                return "autor_endereco"
            else:
                return "autor_dados"
        else:
            # Autor sem numeração - fallback para compatibilidade
            if any(termo in chave_lower for termo in ["endereco", "endereço"]):
                return "autor_endereco"
            else:
                return "autor_dados"

    # 3. PARTES PROCESSUAIS - POLO ATIVO
    polo_ativo_keywords = [
        "requerente",
        "requerentes",
        "impetrante",
        "impetrantes",
        "exequente",
        "exequentes",
        "embargante",
        "embargantes",
        "recorrente",
        "recorrentes",
        "agravante",
        "agravantes",
        "apelante",
        "apelantes",
        "substituido",
        "substituidos",
    ]
    if any(keyword in chave_lower for keyword in polo_ativo_keywords):
        return "polo_ativo"

    # 4. PARTES PROCESSUAIS - POLO PASSIVO
    polo_passivo_keywords = [
        "reu",
        "reus",
        "requerido",
        "requeridos",
        "impetrado",
        "impetrados",
        "executado",
        "executados",
        "embargado",
        "embargados",
        "recorrido",
        "recorridos",
        "agravado",
        "agravados",
        "apelado",
        "apelados",
        "substituidor",
        "substituidores",
    ]
    if any(keyword in chave_lower for keyword in polo_passivo_keywords):
        return "polo_passivo"

    # 5. PARTES PROCESSUAIS - TERCEIROS
    terceiros_keywords = [
        "assistente",
        "assistentes",
        "opoente",
        "opoentes",
        "curador",
        "curadores",
        "tutor",
        "tutores",
        "inventariante",
        "inventariantes",
    ]
    if any(keyword in chave_lower for keyword in terceiros_keywords):
        return "terceiros"

    # 6. DADOS PESSOAIS DO CLIENTE (menor prioridade para evitar conflitos)
    dados_pessoais = [
        "nome",
        "cpf",
        "rg",
        "cnh",
        "email",
        "telefone",
        "data_nascimento",
        "nacionalidade",
        "estado_civil",
        "profissao",
    ]
    if any(termo in chave_lower for termo in dados_pessoais):
        return "cliente"

    # 7. ENDEREÇO (separado de dados pessoais para melhor organização)
    endereco_keywords = [
        "endereco",
        "endereço",
        "logradouro",
        "numero",
        "complemento",
        "bairro",
        "cidade",
        "estado",
        "uf",
        "cep",
    ]
    if any(termo in chave_lower for termo in endereco_keywords):
        return "endereco"

    # 8. DADOS PROCESSUAIS
    processo_keywords = [
        "processo",
        "numero_processo",
        "autos",
        "comarca",
        "vara",
        "juiz",
        "data_fato",
        "data_infracao",
        "local_infracao",
        "artigo",
        "lei",
        "codigo",
    ]
    if any(termo in chave_lower for termo in processo_keywords):
        return "processo"

    # 9. ÓRGÃOS E AUTORIDADES (última verificação mais ampla)
    autoridade_keywords = [
        "detran",
        "denatran",
        "jari",
        "cetran",
        "policia",
        "pm",
        "prf",
        "ciretran",
    ]
    if any(termo in chave_lower for termo in autoridade_keywords):
        return "autoridades"

    # Padrão para campos não categorizados
    return "outros"


def detect_persona_patterns(chaves: List[str]) -> Dict[str, Any]:
    """
    Detecta padrões de personas em placeholders de forma robusta.
    
    Migrado do routes.py com melhorias na validação de tipos.
    """
    # Validação robusta de entrada
    if not chaves:
        return {"patterns": {}, "counts": {}, "total_personas": 0}
    
    # Garantir que temos apenas strings válidas
    chaves_validadas = []
    for item in chaves:
        if isinstance(item, dict):
            # Se for dicionário, extrair a chave
            if "key" in item:
                chaves_validadas.append(str(item["key"]))
            elif "chave" in item:
                chaves_validadas.append(str(item["chave"]))
        elif isinstance(item, str):
            chaves_validadas.append(item)
        else:
            # Converter para string como fallback
            chaves_validadas.append(str(item))
    
    persona_patterns = {}
    persona_counts = {}

    for chave in chaves_validadas:
        # Buscar padrões como: autor_1_nome, reu_2_cpf, autoridade_3_endereco
        match = re.match(r"([a-zA-Z_]+?)_(\d+)_([a-zA-Z_]+)", chave)

        if match:
            persona_tipo = match.group(1)  # ex: autor, reu, autoridade
            persona_numero = int(match.group(2))  # ex: 1, 2, 3
            campo_tipo = match.group(3)  # ex: nome, cpf, endereco

            if persona_tipo not in persona_patterns:
                persona_patterns[persona_tipo] = {}
                persona_counts[persona_tipo] = 0

            if persona_numero not in persona_patterns[persona_tipo]:
                persona_patterns[persona_tipo][persona_numero] = []

            persona_patterns[persona_tipo][persona_numero].append(
                {"campo": campo_tipo, "chave_completa": chave}
            )

            persona_counts[persona_tipo] = max(
                persona_counts[persona_tipo], persona_numero
            )

        # Também detectar padrões simples como: autor_nome, reu_cpf (implica persona única)
        else:
            for persona_keyword in [
                "autor",
                "reu",
                "requerente",
                "requerido",
                "impetrante",
                "impetrado",
                "exequente",
                "executado",
                "recorrente",
                "recorrido",
                "autoridade",
                "orgao",
            ]:
                if chave.lower().startswith(persona_keyword + "_"):
                    if persona_keyword not in persona_counts:
                        persona_counts[persona_keyword] = 1
                    break

    return {
        "patterns": persona_patterns,
        "counts": persona_counts,
        "total_personas": sum(persona_counts.values()),
    }


def determine_field_type_from_key(chave: str) -> str:
    """
    Determina o tipo de campo WTForm baseado na chave do placeholder.
    
    Migrado do routes.py.
    """
    chave_lower = chave.lower()
    
    # Mapeamento de tipos de campo
    if any(keyword in chave_lower for keyword in ['email']):
        return 'email'
    elif any(keyword in chave_lower for keyword in ['telefone', 'celular', 'fone']):
        return 'tel'
    elif any(keyword in chave_lower for keyword in ['data', 'nascimento']):
        return 'date'
    elif any(keyword in chave_lower for keyword in ['observacao', 'descricao', 'motivo']):
        return 'textarea'
    elif any(keyword in chave_lower for keyword in ['estado_civil', 'tipo_pessoa', 'sexo']):
        return 'select'
    else:
        return 'string'


def format_label_from_key(chave: str) -> str:
    """
    Formata uma label legível a partir da chave do placeholder.
    
    Migrado do routes.py.
    """
    # Substituições específicas para melhor legibilidade
    replacements = {
        'cpf': 'CPF',
        'rg': 'RG',
        'cnh': 'CNH',
        'cep': 'CEP',
        'uf': 'UF',
        'endereco': 'Endereço',
        'numero': 'Número',
        'email': 'E-mail',
        'telefone': 'Telefone',
        'data_nascimento': 'Data de Nascimento',
        'estado_civil': 'Estado Civil',
        'orgao_transito': 'Órgão de Trânsito'
    }
    
    # Remover underscores e capitalizar
    label = chave.replace('_', ' ')
    
    # Aplicar substituições específicas
    for old, new in replacements.items():
        if old in label.lower():
            label = label.replace(old, new)
    
    # Capitalizar cada palavra
    return label.title()


def is_required_field_key(chave: str) -> bool:
    """
    Determina se um campo é obrigatório baseado na chave.
    
    Migrado do routes.py.
    """
    chave_lower = chave.lower()
    
    # Campos essenciais sempre obrigatórios
    required_keywords = [
        'nome', 'cpf', 'email', 'processo_numero',
        'autor_1_nome', 'autor_1_cpf'
    ]
    
    return any(keyword in chave_lower for keyword in required_keywords)


def safe_extract_placeholder_keys(text: str) -> List[str]:
    """
    Extrai placeholders de forma segura de um texto.
    """
    if not text:
        return []
    
    try:
        # Busca por padrões {{chave}}
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, text)
        return [match.strip() for match in matches if match.strip()]
    except Exception as e:
        current_app.logger.error(f"Erro ao extrair placeholders: {e}")
        return []


def validate_placeholder_format(key: str) -> bool:
    """
    Valida se um placeholder está em formato válido.
    """
    if not key or not isinstance(key, str):
        return False
    
    # Não deve conter caracteres especiais problemáticos
    if re.search(r'[<>"\'\\\n\r\t]', key):
        return False
    
    # Deve ter pelo menos 1 caractere não-espaço
    if not key.strip():
        return False
    
    return True


def clean_placeholder_key(key: str) -> str:
    """
    Limpa e normaliza uma chave de placeholder.
    """
    if not key:
        return ""
    
    # Remove espaços extras
    cleaned = key.strip()
    
    # Remove caracteres problemáticos
    cleaned = re.sub(r'[<>"\'\\\n\r\t]', '', cleaned)
    
    return cleaned


def get_enum_display_name(enum_value) -> str:
    """
    Obtém o nome de exibição de um valor enum.
    """
    if hasattr(enum_value, 'value'):
        return str(enum_value.value)
    return str(enum_value)


def normalize_placeholders_list(placeholders) -> List[str]:
    """
    Normaliza uma lista de placeholders.
    """
    if not placeholders:
        return []
    
    normalized = []
    for placeholder in placeholders:
        if isinstance(placeholder, str):
            cleaned = clean_placeholder_key(placeholder)
            if cleaned and validate_placeholder_format(cleaned):
                normalized.append(cleaned)
        elif hasattr(placeholder, 'key'):
            cleaned = clean_placeholder_key(placeholder.key)
            if cleaned and validate_placeholder_format(cleaned):
                normalized.append(cleaned)
    
    return list(set(normalized))  # Remove duplicatas


def handle_placeholder_extraction_error(error: Exception, context: str = "") -> None:
    """
    Trata erros de extração de placeholders.
    """
    error_msg = f"Erro na extração de placeholders"
    if context:
        error_msg += f" ({context})"
    error_msg += f": {str(error)}"
    
    current_app.logger.error(error_msg)


def log_placeholder_operation(operation: str, modelo_id: int, data: Dict[str, Any] = None) -> None:
    """
    Registra operações de placeholder para auditoria.
    """
    log_data = {
        'operation': operation,
        'modelo_id': modelo_id,
        'timestamp': str(current_app.time.time() if hasattr(current_app, 'time') else 'unknown')
    }
    
    if data:
        log_data.update(data)
    
    current_app.logger.info(f"Placeholder operation: {log_data}")


def generate_placeholder_text_from_key(chave: str) -> str:
    """
    Gera texto de placeholder baseado na chave.
    
    Migrado do routes.py.
    """
    # Mapeamento específico de textos de placeholder
    placeholder_map = {
        'cpf': 'Ex: 123.456.789-00',
        'rg': 'Ex: 12.345.678-9',
        'cnh': 'Ex: 12345678901',
        'cep': 'Ex: 01234-567',
        'email': 'Ex: exemplo@email.com',
        'telefone': 'Ex: (11) 99999-9999',
        'data_nascimento': 'DD/MM/AAAA',
        'endereco_numero': 'Ex: 123',
        'processo_numero': 'Ex: 1234567-89.2023.8.26.0001'
    }
    
    chave_lower = chave.lower()
    
    # Verificar mapeamentos específicos
    for key, placeholder in placeholder_map.items():
        if key in chave_lower:
            return placeholder
    
    # Placeholder genérico baseado no tipo
    if 'nome' in chave_lower:
        return 'Digite o nome completo'
    elif 'endereco' in chave_lower:
        return 'Digite o endereço'
    elif 'cidade' in chave_lower:
        return 'Digite a cidade'
    elif 'estado' in chave_lower:
        return 'Ex: SP'
    else:
        # Gerar placeholder genérico
        label = format_label_from_key(chave)
        return f'Digite {label.lower()}'