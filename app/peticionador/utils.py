# app/peticionador/utils.py


def get_enum_display_name(enum_member):
    """Retorna string amigável para um membro Enum (prefere .value)."""
    if enum_member:
        try:
            return str(enum_member.value)
        except AttributeError:
            return str(enum_member.name).replace("_", " ").title()
    return ""


import re

# ---------------------------------------------------------------------------
# Funções reutilizáveis de normalização de chaves e busca flexível em payloads
# ---------------------------------------------------------------------------
import unicodedata


def normalizar_para_camel_case(chave: str) -> str:
    """Remove acentos/espacos e converte para camelCase."""
    chave = (
        unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("ASCII")
    )
    palavras = re.split(r"[ _-]", chave)
    if not palavras:
        return ""
    return palavras[0].lower() + "".join(p.title() for p in palavras[1:] if p)


def buscar_valor_flexivel(payload: dict, *variantes):
    """Retorna o primeiro valor correspondente entre variantes (exata ou camelCase)."""
    if not isinstance(payload, dict):
        return None
    for k in variantes:
        if k in payload:
            return payload[k]
    variantes_norm = {normalizar_para_camel_case(v) for v in variantes}
    for k, v in payload.items():
        if normalizar_para_camel_case(k) in variantes_norm:
            return v
    return None
