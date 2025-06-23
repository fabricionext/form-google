import csv
import logging
import re
from typing import Any, Dict, List, Optional

import click

# Configure basic logging to output to console
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

import os
from datetime import datetime

from flask.cli import with_appcontext
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.peticionador.models import Cliente, TipoPessoaEnum
from extensions import db

# Mapeamento de nomes de estado para siglas
ESTADOS_SIGLAS = {
    "ACRE": "AC",
    "ALAGOAS": "AL",
    "AMAPA": "AP",
    "AMAZONAS": "AM",
    "BAHIA": "BA",
    "CEARA": "CE",
    "DISTRITO FEDERAL": "DF",
    "ESPIRITO SANTO": "ES",
    "GOIAS": "GO",
    "MARANHAO": "MA",
    "MATO GROSSO": "MT",
    "MATO GROSSO DO SUL": "MS",
    "MINAS GERAIS": "MG",
    "PARA": "PA",
    "PARAIBA": "PB",
    "PARANA": "PR",
    "PERNAMBUCO": "PE",
    "PIAUI": "PI",
    "RIO DE JANEIRO": "RJ",
    "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS",
    "RONDONIA": "RO",
    "RORAIMA": "RR",
    "SANTA CATARINA": "SC",
    "SAO PAULO": "SP",
    "SERGIPE": "SE",
    "TOCANTINS": "TO",
}

# --- INÍCIO DAS NOVAS DEFINIÇÕES DE MAPEAMENTO ---

# Chaves padronizadas que o script de importação usará internamente
# O sufixo '_raw' indica que o valor pode precisar de parsing/transformação posterior
STANDARDIZED_KEYS = {
    "timestamp_raw": "timestamp_raw",
    "primeiro_nome": "primeiro_nome",
    "sobrenome": "sobrenome",
    "nacionalidade_raw": "nacionalidade_raw",
    "estado_civil_raw": "estado_civil_raw",
    "profissao_raw": "profissao_raw",
    "endereco_completo_raw": "endereco_completo_raw",  # Usado pela aba "Antigos"
    "endereco_logradouro_raw": "endereco_logradouro_raw",  # Usado pela aba "Respostas" (se tiver separado)
    "endereco_numero_raw": "endereco_numero_raw",
    "endereco_complemento_raw": "endereco_complemento_raw",
    "endereco_bairro_raw": "endereco_bairro_raw",
    "endereco_cidade_raw": "endereco_cidade_raw",
    "endereco_estado_raw": "endereco_estado_raw",
    "endereco_cep_raw": "endereco_cep_raw",
    "telefone_celular_raw": "telefone_celular_raw",
    "telefone_outro_raw": "telefone_outro_raw",
    "email_raw": "email_raw",
    "data_nascimento_raw": "data_nascimento_raw",
    "rg_numero_raw": "rg_numero_raw",
    "rg_estado_emissor_raw": "rg_estado_emissor_raw",
    "rg_completo_raw": "rg_completo_raw",  # Usado pela aba "Antigos" para parsing de RG completo
    "cpf_raw": "cpf_raw",
    "cnh_numero_raw": "cnh_numero_raw",
    # Adicione outras chaves padronizadas conforme necessário
}

MAP_RESPOSTAS = {
    # Coluna Planilha "Respostas" : Chave Padronizada Interna
    "Carimbo de data/hora": STANDARDIZED_KEYS["timestamp_raw"],
    "Primeiro Nome": STANDARDIZED_KEYS["primeiro_nome"],
    "Sobrenome": STANDARDIZED_KEYS["sobrenome"],
    "Nacionalidade": STANDARDIZED_KEYS["nacionalidade_raw"],
    "Estado Civil": STANDARDIZED_KEYS["estado_civil_raw"],
    "Profissão": STANDARDIZED_KEYS["profissao_raw"],
    "Endereço": STANDARDIZED_KEYS[
        "endereco_logradouro_raw"
    ],  # Assumindo que "Endereço" aqui é só o logradouro
    "Cidade": STANDARDIZED_KEYS["endereco_cidade_raw"],
    "Estado": STANDARDIZED_KEYS["endereco_estado_raw"],
    "CEP": STANDARDIZED_KEYS["endereco_cep_raw"],
    "Telefone celular": STANDARDIZED_KEYS["telefone_celular_raw"],
    "Outro telefone": STANDARDIZED_KEYS["telefone_outro_raw"],
    "E-mail": STANDARDIZED_KEYS["email_raw"],
    "Data de nascimento": STANDARDIZED_KEYS["data_nascimento_raw"],
    "RG": STANDARDIZED_KEYS["rg_numero_raw"],
    "Estado emissor do RG": STANDARDIZED_KEYS["rg_estado_emissor_raw"],
    "CPF": STANDARDIZED_KEYS["cpf_raw"],
    "Digite sua CNH (opcional):": STANDARDIZED_KEYS["cnh_numero_raw"],
    # 'Foto da CNH ou RG': '', # Ignorado por enquanto
    # 'Pontuação': '', # Ignorado por enquanto
    # 'Nome completo': '', # Ignorado, já temos Primeiro Nome e Sobrenome
}

MAP_ANTIGOS = {
    # Coluna Planilha "Antigos" : Chave Padronizada Interna
    "CPF": STANDARDIZED_KEYS["cpf_raw"],
    "Carimbo de data/hora": STANDARDIZED_KEYS["timestamp_raw"],
    "Primeiro Nome": "nome_completo_antigos_raw",  # Chave temporária para divisão
    # 'Sobrenome': '', # Na aba "Antigos", sobrenome está junto com Primeiro Nome ou ausente
    "Nacionalidade": STANDARDIZED_KEYS["nacionalidade_raw"],
    "Estado Civil": STANDARDIZED_KEYS["estado_civil_raw"],
    "Profissão": STANDARDIZED_KEYS["profissao_raw"],
    "Endereço": STANDARDIZED_KEYS[
        "endereco_completo_raw"
    ],  # Endereço completo vai para logradouro
    "Cidade": STANDARDIZED_KEYS["endereco_cidade_raw"],
    "Estado:": STANDARDIZED_KEYS["endereco_estado_raw"],  # Note o ":"
    "CEP": STANDARDIZED_KEYS["endereco_cep_raw"],
    "Telefone Celular:": STANDARDIZED_KEYS["telefone_celular_raw"],  # Note o ":"
    "Outro Telefone:": STANDARDIZED_KEYS["telefone_outro_raw"],  # Note o ":"
    "Email": STANDARDIZED_KEYS["email_raw"],  # Sem acento
    "Data de nascimento": STANDARDIZED_KEYS["data_nascimento_raw"],
    "RG": STANDARDIZED_KEYS["rg_completo_raw"],  # Mapeado para parsing de RG completo
    "Estado emissor do RG": STANDARDIZED_KEYS["rg_estado_emissor_raw"],
    "CNH": STANDARDIZED_KEYS["cnh_numero_raw"],
    # 'Foto da CNH ou RG': '', # Ignorado
}


def apply_mapper_and_specific_logic(
    row_dict_from_sheet: Dict[str, str], mapper: Dict[str, str], sheet_name: str
) -> Dict[str, Any]:
    standardized_data = {}
    for sheet_col_name, standardized_key in mapper.items():
        standardized_data[standardized_key] = row_dict_from_sheet.get(
            sheet_col_name, ""
        ).strip()

    # Lógica específica para a aba "Antigos" (dividir nome completo)
    if sheet_name == "Antigos" and "nome_completo_antigos_raw" in standardized_data:
        nome_completo = standardized_data.pop("nome_completo_antigos_raw", "")
        partes_nome = nome_completo.split(" ", 1)
        standardized_data[STANDARDIZED_KEYS["primeiro_nome"]] = partes_nome[0].strip()
        standardized_data[STANDARDIZED_KEYS["sobrenome"]] = (
            partes_nome[1].strip() if len(partes_nome) > 1 else ""
        )

    # Garantir que as chaves de nome sempre existam, mesmo que vazias, se não vieram do mapper
    standardized_data.setdefault(STANDARDIZED_KEYS["primeiro_nome"], "")
    standardized_data.setdefault(STANDARDIZED_KEYS["sobrenome"], "")

    return standardized_data


# --- FIM DAS NOVAS DEFINIÇÕES DE MAPEAMENTO ---


def obter_sigla_estado(nome_estado_str):
    if not nome_estado_str or not isinstance(nome_estado_str, str):
        return None

    nome_estado_limpo = nome_estado_str.strip().upper()

    # ESTADOS_SIGLAS é definido como {'NOME COMPLETO': 'SIGLA'}, e.g., {'PARANÁ': 'PR'}

    # Prioridade 1: Input é uma sigla de 2 letras já conhecida (e.g., "PR")
    # Verifica se nome_estado_limpo (e.g. "PR") existe nos VALORES de ESTADOS_SIGLAS (e.g. ['AC', 'AL', ..., 'PR', ...])
    if len(nome_estado_limpo) == 2 and nome_estado_limpo in ESTADOS_SIGLAS.values():
        return nome_estado_limpo

    # Prioridade 2: Input é um nome de estado completo conhecido (e.g., "PARANÁ")
    # Verifica se nome_estado_limpo (e.g. "PARANÁ") existe nas CHAVES de ESTADOS_SIGLAS
    if nome_estado_limpo in ESTADOS_SIGLAS:
        return ESTADOS_SIGLAS[
            nome_estado_limpo
        ]  # Retorna o VALOR associado (a sigla, e.g. "PR")

    # Prioridade 3: Input no formato "UF - Nome Estado" ou "UF – Nome Estado"
    sigla_extraida = None
    if " – " in nome_estado_str:  # M-dash, como em "PR – Paraná"
        partes = nome_estado_str.split(" – ", 1)
        sigla_extraida = partes[0].strip().upper()
    elif " - " in nome_estado_str:  # Hífen normal
        partes = nome_estado_str.split(" - ", 1)
        sigla_extraida = partes[0].strip().upper()

    # Se uma sigla foi extraída, verifica se ela é válida (tem 2 caracteres e existe nos valores de ESTADOS_SIGLAS)
    if (
        sigla_extraida
        and len(sigla_extraida) == 2
        and sigla_extraida in ESTADOS_SIGLAS.values()
    ):
        return sigla_extraida

    logger.warning(
        f"Não foi possível mapear o estado: '{nome_estado_str}' para uma sigla conhecida."
    )
    return None


def parse_rg_completo(rg_str):
    if not rg_str or not isinstance(rg_str, str):
        return {"numero": None, "orgao": None, "uf": None}

    original_rg_str = str(
        rg_str
    )  # Para logging, caso rg_str não seja string inicialmente
    rg_str_upper = str(rg_str).upper()

    # Normalizar: remover pontos e hífens do número, substituir barras por espaços
    # Remove . e - que estão entre dígitos ou entre dígito e X
    rg_str_upper = re.sub(r"(?<=[\dX])[.-](?=[\dX])", "", rg_str_upper)
    rg_str_upper = rg_str_upper.replace("/", " ")
    rg_str_upper = re.sub(r"\s+", " ", rg_str_upper).strip()  # Normaliza espaços

    numero = None
    orgao = None
    uf = None

    # Padrões (do mais específico para o mais geral)
    # Formato: NUMERO ORGAO UF (e.g., "12345678X SSP SP")
    # ORGAO pode ter de 2 a 5 letras, NUMERO pode ter X no final
    match = re.fullmatch(
        r"([\d]+[X]?|[\dX]+)\s+([A-Z]{2,5})\s+([A-Z]{2})", rg_str_upper
    )
    if match:
        num_cand, orgao_cand, uf_cand = match.groups()
        if uf_cand in ESTADOS_SIGLAS.values():  # ESTADOS_SIGLAS é o dict global
            return {"numero": num_cand, "orgao": orgao_cand, "uf": uf_cand}

    # Formato: NUMERO ORGAO (UF pode estar faltando ou ser o próprio órgão se tiver 2 letras e for UF válida)
    # e.g., "12345678X SSP", "12345678X SP"
    match = re.fullmatch(r"([\d]+[X]?|[\dX]+)\s+([A-Z]{2,})", rg_str_upper)
    if match:
        num_cand, orgao_cand = match.groups()
        if len(orgao_cand) == 2 and orgao_cand in ESTADOS_SIGLAS.values():
            return {"numero": num_cand, "orgao": orgao_cand, "uf": orgao_cand}
        else:
            return {"numero": num_cand, "orgao": orgao_cand, "uf": None}

    # Formato: NUMERO (sem órgão ou UF explícitos)
    # e.g., "12345678X"
    match = re.fullmatch(r"([\d]+[X]?|[\dX]+)", rg_str_upper)
    if match:
        return {"numero": match.group(1), "orgao": None, "uf": None}

    # Tentativa de extração mais liberal se os fullmatch falharem
    parts = rg_str_upper.split()
    if not parts:
        logger.warning(
            f"RG string '{original_rg_str}' resultou em partes vazias após normalização."
        )
        return {"numero": None, "orgao": None, "uf": None}

    num_cand_match = re.match(r"([\d]+[X]?|[\dX]+)", parts[0])
    if num_cand_match:
        numero = num_cand_match.group(1)
        remaining_parts = parts[1:]

        if not remaining_parts and numero:
            return {"numero": numero, "orgao": None, "uf": None}

        if remaining_parts:
            if (
                len(remaining_parts[-1]) == 2
                and remaining_parts[-1] in ESTADOS_SIGLAS.values()
            ):
                uf = remaining_parts[-1]
                orgao_parts = remaining_parts[:-1]
                if orgao_parts:
                    orgao = " ".join(orgao_parts)
                elif uf:
                    orgao = uf  # Caso como "12345 SP", órgão e UF são SP
            else:
                orgao = " ".join(remaining_parts)

            return {"numero": numero, "orgao": orgao, "uf": uf}

    logger.warning(
        f"Não foi possível parsear RG: '{original_rg_str}'. String normalizada: '{rg_str_upper}'."
    )
    return {"numero": None, "orgao": None, "uf": None}


def parse_endereco_completo_antigos(endereco_str):
    if not endereco_str or not isinstance(endereco_str, str):
        return {"logradouro": None, "numero": None, "complemento": None, "bairro": None}

    endereco_limpo = endereco_str.strip()
    original_endereco_str = endereco_str  # Para logging

    logradouro, numero, complemento, bairro = None, None, None, None

    # Tentativa de encontrar número (pode ter letras como S/N, KM)
    # Prioriza número no final ou seguido de vírgula/hífen e espaço
    match_numero = re.search(
        r"(?i)(?:,\s*|\s+N[°º]?[.:]?\s*|\s+N(?:Ú|U)MERO|\s+NR\s+|\s+)\b([A-Z]*\d+[A-Z]*\b|S/N\b|SEM\s+N(?:Ú|U)MERO\b|KM\s*\d+)\b(?:\s*,|\s+-|\s+LOTE|\s+QUADRA|\s+APTO|\s+CASA|\s+BLOCO|$)",
        endereco_limpo,
        re.IGNORECASE,
    )

    parte_logradouro = endereco_limpo
    parte_restante = ""

    if match_numero:
        numero = match_numero.group(1).upper()
        # O que vem antes do número (ou do seu delimitador) é o logradouro
        parte_logradouro = endereco_limpo[: match_numero.start()].strip()
        # O que vem depois do número é o restante (complemento, bairro)
        parte_restante = (
            endereco_limpo[match_numero.end() :].strip().lstrip(",- ").strip()
        )
    else:
        # Se não achar número explícito, pode ser que o logradouro seja tudo e não tenha número (lote, quadra etc.)
        # ou o número está no começo (menos comum para o formato que esperamos)
        # Vamos tentar pegar o logradouro como a parte antes da primeira vírgula ou hífen, se houver.
        primeira_virgula = parte_logradouro.find(",")
        if primeira_virgula != -1:
            # Verifica se o que vem depois da vírgula parece ser um número
            teste_num_virgula = (
                parte_logradouro[primeira_virgula + 1 :]
                .lstrip()
                .split(",")[0]
                .split("-")[0]
                .strip()
            )
            if re.match(
                r"^([A-Z]*\d+[A-Z]*|S/N|SEM NÚMERO)$", teste_num_virgula, re.IGNORECASE
            ):
                numero = teste_num_virgula.upper()
                parte_restante = (
                    parte_logradouro[parte_logradouro.find(numero) + len(numero) :]
                    .lstrip(",- ")
                    .strip()
                )
                parte_logradouro = parte_logradouro[:primeira_virgula].strip()
            # else: logradouro continua sendo tudo até aqui, e parte_restante é o que vem depois da vírgula
            #    parte_restante = parte_logradouro[primeira_virgula+1:].lstrip()
            #    parte_logradouro = parte_logradouro[:primeira_virgula].strip()
        # Se não tem número claro, o logradouro pode ser a string inteira, e o resto fica vazio.
        # Ou, se não achou número, mas tem vírgula, o que vem antes da primeira vírgula é o logradouro.
        # Esta parte é complexa e pode precisar de mais heurísticas.

    # Limpeza do logradouro: remover vírgulas no final se parte_restante ou numero foram encontrados
    if (numero or parte_restante) and parte_logradouro.endswith(","):
        parte_logradouro = parte_logradouro[:-1].strip()

    logradouro = parte_logradouro if parte_logradouro else None

    # Tentar extrair bairro e complemento do restante
    if parte_restante:
        # Palavras-chave comuns para bairro (tentar remover se estiver no final)
        # Formato: COMPLEMENTO - BAIRRO ou COMPLEMENTO, BAIRRO
        # Ou apenas BAIRRO se o complemento for sutil
        match_bairro = re.search(
            r"(?i)(?:-\s+|\s*Bairro\s+|\s*Br\s+|\s*Vila\s+|\s*Vl\s+|\s*Jardim\s+|\s*Jd\s+|\s*Setor\s+|\s*St\s+)(.+)$",
            parte_restante,
        )
        if match_bairro:
            bairro = match_bairro.group(1).strip().rstrip(",").strip()
            # O que sobra antes do bairro é o complemento
            complemento = (
                parte_restante[: match_bairro.start()].strip().rstrip(",-").strip()
            )
        else:
            # Se não achou marcador de bairro, o restante pode ser só complemento ou só bairro
            # Heurística: se tiver vírgula, o que vem depois da última vírgula pode ser o bairro
            partes_restantes = [
                p.strip() for p in parte_restante.split(",") if p.strip()
            ]
            if len(partes_restantes) > 1:
                # Se o último segmento não parecer um complemento típico (ex: não começa com Apto, Bloco, etc.)
                # e tiver mais de uma palavra ou for uma palavra comum para bairro, assume como bairro.
                # Esta é uma heurística frágil.
                # Por simplicidade, se houver mais de um segmento após vírgula, o último é bairro, o resto é complemento.
                bairro = partes_restantes[-1]
                complemento = ", ".join(partes_restantes[:-1])
            else:
                # Se não tem vírgula ou só um segmento, pode ser complemento ou bairro.
                # Se tiver palavras como APTO, BLOCO, SALA, etc., é provavelmente complemento.
                if re.search(
                    r"(?i)\b(APTO|APARTAMENTO|BLOCO|BL|CASA|CS|SALA|SL|FUNDOS|FDS|TERREO|LOJA|LJ|CONJUNTO|CJ|EDIFICIO|ED)\b",
                    parte_restante,
                ):
                    complemento = parte_restante
                else:
                    # Caso contrário, pode ser bairro (ou um complemento não reconhecido)
                    # Se for uma string mais longa, mais chance de ser bairro.
                    if (
                        len(parte_restante.split()) > 1 or len(parte_restante) > 15
                    ):  # Heurística de tamanho
                        bairro = parte_restante
                    else:
                        complemento = parte_restante  # Assume complemento se for curto e não parecer bairro

    # Garantir que campos vazios sejam None
    logradouro = logradouro if logradouro else None
    numero = numero if numero else None
    complemento = complemento if complemento else None
    bairro = bairro if bairro else None

    logger.debug(
        f"Parse Endereço: '{original_endereco_str}' -> L: '{logradouro}', N: '{numero}', C: '{complemento}', B: '{bairro}'"
    )
    return {
        "logradouro": logradouro,
        "numero": numero,
        "complemento": complemento,
        "bairro": bairro,
    }


def parse_data(date_string, default_format="%d/%m/%Y"):
    if not date_string:
        return None
    date_str_cleaned = date_string.strip()
    if not date_str_cleaned:
        return None

    try:
        return datetime.strptime(date_str_cleaned, default_format).date()
    except ValueError:
        cleaned_further = re.sub(r"[^0-9/]", "", date_str_cleaned)
        try:
            return datetime.strptime(cleaned_further, "%d/%m/%Y").date()
        except ValueError:
            try:
                if (
                    len(cleaned_further.split("/")[-1]) < 4
                ):  # Tentar com ano de dois dígitos
                    return datetime.strptime(cleaned_further, "%d/%m/%y").date()
            except ValueError:
                # logger.warning(f"Formato de data inválido '{date_string}'.") # Log mais detalhado abaixo
                return None
        # logger.warning(f"Formato de data inválido '{date_string}'.") # Log mais detalhado abaixo
        return None


def get_google_sheets_service():
    logger.info("Attempting to get Google Sheets service.")
    creds = None
    service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    # SHEET_NAME não é mais usado globalmente para range, mas pode ser mantido para logs se necessário

    if not service_account_file:
        logger.error(
            "Erro: A variável de ambiente GOOGLE_SERVICE_ACCOUNT_JSON não está configurada."
        )
        return None

    try:
        creds = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
        service = build("sheets", "v4", credentials=creds)
        logger.info("Successfully built Google Sheets service object.")
        return service
    except FileNotFoundError:
        logger.error(
            f"Arquivo da conta de serviço não encontrado em {service_account_file}",
            exc_info=True,
        )
        return None
    except DefaultCredentialsError:
        logger.error("Credenciais padrão não encontradas.", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"Erro ao autenticar com Google Sheets API: {e}", exc_info=True)
        return None


def get_google_sheets_data(service, full_sheet_range: str) -> Optional[List[List[str]]]:
    logger.info(
        f"Attempting to fetch data from Google Sheets API for range: {full_sheet_range}"
    )
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        logger.error(
            "Erro: A variável de ambiente SPREADSHEET_ID não está configurada."
        )
        return None
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=full_sheet_range)
            .execute()
        )
        values = result.get("values", [])
        logger.info(
            f"Successfully fetched {len(values)} rows for range: {full_sheet_range}."
        )
        return values
    except Exception as e:
        logger.error(
            f"Erro ao buscar dados do Google Sheets para range {full_sheet_range}: {e}",
            exc_info=True,
        )
        return None


def parse_datetime(datetime_str, default_now_if_invalid=True):
    if not datetime_str:
        return datetime.now() if default_now_if_invalid else None

    datetime_str_cleaned = datetime_str.strip()
    if not datetime_str_cleaned:
        return datetime.now() if default_now_if_invalid else None

    formatos_tentar = [
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y",
    ]
    for fmt in formatos_tentar:
        try:
            dt_obj = datetime.strptime(datetime_str_cleaned, fmt)
            if fmt == "%d/%m/%Y":  # Apenas data, hora será meia-noite
                dt_obj = dt_obj.replace(hour=0, minute=0, second=0)
            return dt_obj
        except ValueError:
            continue

    # logger.warning(f"Formato de data/hora inválido para '{datetime_str}'. Usando data/hora atual se default.") # Log mais detalhado abaixo
    return datetime.now() if default_now_if_invalid else None


@click.command("import-clients")
@with_appcontext
def import_clients_cli():
    logger.info("Starting import_clients_cli command.")
    click.echo("Iniciando importação de clientes do Google Sheets...")

    service = get_google_sheets_service()
    if not service:
        logger.error("Failed to get Google Sheets service. Aborting import.")
        click.echo(
            "ERRO: Falha ao conectar com Google Sheets. Verifique as configurações e logs."
        )
        return

    # Configuração das abas e seus respectivos mapeadores e ranges
    # Os ranges devem ser suficientes para cobrir todos os dados. Ex: 'Respostas!A:U'
    # Verifique os nomes das colunas nas suas planilhas para ajustar os ranges.
    # Exemplo de range para aba "Respostas" (até coluna U): "Respostas!A:U"
    # Exemplo de range para aba "Antigos" (até coluna S): "Antigos!A:S"
    sheets_to_import_config = [
        {
            "name": "Respostas",
            "range": os.getenv("SHEET_RANGE_RESPOSTAS", "Respostas!A:XFD"),
            "mapper": MAP_RESPOSTAS,
        },
        {
            "name": "Antigos",
            "range": os.getenv("SHEET_RANGE_ANTIGOS", "Antigos!A:XFD"),
            "mapper": MAP_ANTIGOS,
        },
    ]

    standardized_clientes_para_processar = []
    skipped_empty_count = 0

    logger.info(
        f"Iniciando processamento de {len(sheets_to_import_config)} abas: {', '.join([s['name'] for s in sheets_to_import_config])}"
    )

    for config in sheets_to_import_config:
        sheet_name = config["name"]
        sheet_full_range = config["range"]
        mapper_func = config["mapper"]  # O dicionário de mapeamento em si

        logger.info(f"Processando aba: '{sheet_name}' com range: '{sheet_full_range}'")
        click.echo(f"Processando aba: {sheet_name}...")

        sheet_values = get_google_sheets_data(service, sheet_full_range)

        if not sheet_values:
            logger.warning(f"Nenhum dado retornado para a aba '{sheet_name}'. Pulando.")
            click.echo(f"Nenhum dado ou erro ao ler a aba '{sheet_name}'. Pulando.")
            continue

        if len(sheet_values) < 1:  # Precisa de pelo menos o cabeçalho
            logger.warning(f"Aba '{sheet_name}' não contém cabeçalho. Pulando.")
            click.echo(f"Aba '{sheet_name}' não contém cabeçalho. Pulando.")
            continue

        current_sheet_headers = [str(header).strip() for header in sheet_values[0]]
        logger.info(
            f"Cabeçalhos detectados na aba '{sheet_name}': {', '.join(current_sheet_headers)}"
        )

        current_sheet_data_rows = sheet_values[1:]

        if not current_sheet_data_rows:
            logger.info(
                f"Nenhuma linha de dados encontrada na aba '{sheet_name}' (após o cabeçalho)."
            )
            click.echo(f"Nenhuma linha de dados em '{sheet_name}'.")

        processed_rows_in_sheet = 0
        for r_idx, row_data_list in enumerate(current_sheet_data_rows):
            # Converte a linha da planilha (lista) para um dicionário usando os cabeçalhos da aba atual
            row_as_dict_original_keys = {}
            for c_idx, header_name in enumerate(current_sheet_headers):
                if c_idx < len(row_data_list):
                    cell_value = row_data_list[c_idx]
                    row_as_dict_original_keys[header_name] = (
                        str(cell_value).strip() if cell_value is not None else ""
                    )
                else:
                    row_as_dict_original_keys[header_name] = ""

            if all(not value for value in row_as_dict_original_keys.values()):
                logger.debug(
                    f"Linha {r_idx + 2} da aba '{sheet_name}' ignorada por ser vazia (antes do mapeamento)."
                )
                skipped_empty_count += 1
                continue

            # Aplica o mapeador específico da aba para padronizar as chaves
            standardized_row_data = apply_mapper_and_specific_logic(
                row_as_dict_original_keys, mapper_func, sheet_name
            )

            # Adiciona identificador da aba de origem para referência, se necessário
            standardized_row_data["_source_sheet"] = sheet_name
            standardized_row_data["_source_row_num"] = (
                r_idx + 2
            )  # +1 para index 0, +1 para pular cabeçalho

            # Processamento específico de campos complexos ANTES de adicionar à lista final
            if sheet_name == "Antigos":
                # Parse RG Combinado para a aba "Antigos"
                # Assumindo que MAP_ANTIGOS mapeia a coluna RG para STANDARDIZED_KEYS['rg_completo_raw']
                rg_completo_str = standardized_row_data.get(
                    STANDARDIZED_KEYS["rg_completo_raw"]
                )
                cpf_para_log = standardized_row_data.get(
                    STANDARDIZED_KEYS["cpf_raw"], "N/A"
                )  # Para logging
                source_row_num_log = standardized_row_data.get("_source_row_num", "N/A")

                if rg_completo_str:
                    logger.debug(
                        f"Antigos - Linha {source_row_num_log} (CPF: {cpf_para_log}) - Parsing RG: '{rg_completo_str}'"
                    )
                    parsed_rg_data = parse_rg_completo(rg_completo_str)

                    standardized_row_data["rg_numero"] = parsed_rg_data.get("numero")
                    standardized_row_data["rg_orgao_expedidor"] = parsed_rg_data.get(
                        "orgao"
                    )
                    standardized_row_data["rg_uf_emissor"] = parsed_rg_data.get("uf")
                    logger.info(
                        f"Antigos - Linha {source_row_num_log} (CPF: {cpf_para_log}) - Parsed RG: Num='{standardized_row_data.get('rg_numero')}', Org='{standardized_row_data.get('rg_orgao_expedidor')}', UF='{standardized_row_data.get('rg_uf_emissor')}'"
                    )
                else:
                    logger.debug(
                        f"Antigos - Linha {source_row_num_log} (CPF: {cpf_para_log}) - Campo RG ('{STANDARDIZED_KEYS['rg_completo_raw']}') não encontrado ou vazio."
                    )

                # Parse Endereço Completo para Antigos
                endereco_completo_str = standardized_row_data.get(
                    STANDARDIZED_KEYS["endereco_completo_raw"]
                )
                if endereco_completo_str:
                    logger.debug(
                        f"Antigos - Linha {source_row_num_log} (CPF: {cpf_para_log}) - Parsing Endereço: '{endereco_completo_str}'"
                    )
                    parsed_endereco = parse_endereco_completo_antigos(
                        endereco_completo_str
                    )

                    standardized_row_data["endereco_logradouro"] = parsed_endereco.get(
                        "logradouro"
                    )
                    standardized_row_data["endereco_numero"] = parsed_endereco.get(
                        "numero"
                    )
                    standardized_row_data["endereco_complemento"] = parsed_endereco.get(
                        "complemento"
                    )
                    standardized_row_data["endereco_bairro"] = parsed_endereco.get(
                        "bairro"
                    )
                    logger.info(
                        f"Antigos - Linha {source_row_num_log} (CPF: {cpf_para_log}) - Parsed Endereço: Logr='{standardized_row_data.get('endereco_logradouro')}', Num='{standardized_row_data.get('endereco_numero')}', Comp='{standardized_row_data.get('endereco_complemento')}', Bairro='{standardized_row_data.get('endereco_bairro')}'"
                    )
                else:
                    logger.debug(
                        f"Antigos - Linha {source_row_num_log} (CPF: {cpf_para_log}) - Campo Endereço ('{STANDARDIZED_KEYS['endereco_completo_raw']}') não encontrado ou vazio."
                    )

            standardized_clientes_para_processar.append(standardized_row_data)
            processed_rows_in_sheet += 1

        logger.info(
            f"Concluído processamento da aba '{sheet_name}'. {processed_rows_in_sheet} linhas de dados válidas adicionadas de {len(current_sheet_data_rows)} lidas."
        )

    logger.info(
        f"Total de {len(standardized_clientes_para_processar)} clientes agregados de todas as abas para processamento final."
    )
    logger.info(
        f"Total de {skipped_empty_count} linhas vazias ignoradas em todas as abas (antes do mapeamento)."
    )

    total_rows_to_process = len(standardized_clientes_para_processar)
    imported_count = 0
    skipped_cpf_count = 0
    skipped_email_count = 0
    error_count = 0

    for idx, standardized_data in enumerate(standardized_clientes_para_processar):
        # Adicionar log detalhado para CPFs específicos para depuração
        cpf_debug_list = [
            "22065254882",
            "69651744987",
        ]  # Adicione outros CPFs se necessário
        current_cpf_raw_for_debug = standardized_data.get(
            STANDARDIZED_KEYS["cpf_raw"], ""
        )
        current_cpf_cleaned_for_debug = re.sub(r"[^0-9]", "", current_cpf_raw_for_debug)

        if current_cpf_cleaned_for_debug in cpf_debug_list:
            logger.debug(
                f"{log_prefix} INICIANDO DEBUG DETALHADO PARA CPF: {current_cpf_cleaned_for_debug}"
            )
            logger.debug(
                f"  Dados brutos completos da linha mapeada: {standardized_data}"
            )
            logger.debug(
                f"  Campo {STANDARDIZED_KEYS['email_raw']}: '{standardized_data.get(STANDARDIZED_KEYS['email_raw']) }'"
            )
            logger.debug(
                f"  Campo {STANDARDIZED_KEYS['telefone_celular_raw']}: '{standardized_data.get(STANDARDIZED_KEYS['telefone_celular_raw']) }'"
            )
            logger.debug(
                f"  Campo {STANDARDIZED_KEYS['telefone_outro_raw']}: '{standardized_data.get(STANDARDIZED_KEYS['telefone_outro_raw']) }'"
            )
            logger.debug(
                f"  Campo {STANDARDIZED_KEYS['endereco_estado_raw']} (para endereço): '{standardized_data.get(STANDARDIZED_KEYS['endereco_estado_raw']) }'"
            )
            logger.debug(
                f"  Campo {STANDARDIZED_KEYS['rg_numero_raw']}: '{standardized_data.get(STANDARDIZED_KEYS['rg_numero_raw']) }'"
            )
            logger.debug(
                f"  Campo {STANDARDIZED_KEYS['rg_estado_emissor_raw']} (para RG): '{standardized_data.get(STANDARDIZED_KEYS['rg_estado_emissor_raw']) }'"
            )
            logger.debug(
                f"  Campo {STANDARDIZED_KEYS['endereco_completo_raw']} (de Antigos): '{standardized_data.get(STANDARDIZED_KEYS['endereco_completo_raw']) }'"
            )
            logger.debug(
                f"  Campo {STANDARDIZED_KEYS['endereco_logradouro_raw']} (de Respostas): '{standardized_data.get(STANDARDIZED_KEYS['endereco_logradouro_raw']) }'"
            )

        dados_cliente_final = {}  # Dicionário para construir o objeto Cliente

        source_sheet_log = standardized_data.get("_source_sheet", "N/A")
        source_row_log = standardized_data.get("_source_row_num", "N/A")
        log_prefix = f"Aba '{source_sheet_log}', Linha {source_row_log}:"

        try:
            # 1. CPF (obrigatório)
            cpf_bruto = standardized_data.get(STANDARDIZED_KEYS["cpf_raw"], "")
            if not cpf_bruto:
                logger.warning(f"{log_prefix} CPF não fornecido. Ignorando.")
                error_count += 1
                continue
            cpf_limpo = re.sub(r"[^0-9]", "", cpf_bruto)
            if not cpf_limpo:
                logger.warning(
                    f"{log_prefix} CPF inválido ou vazio após limpeza: '{cpf_bruto}'. Ignorando."
                )
                error_count += 1
                continue

            if Cliente.query.filter_by(cpf=cpf_limpo).first():
                logger.info(
                    f"{log_prefix} Cliente com CPF {cpf_limpo} já existe. Ignorando."
                )
                skipped_cpf_count += 1
                continue
            dados_cliente_final["cpf"] = cpf_limpo

            # 2. Email (opcional, mas verificar duplicidade se presente)
            email_bruto = standardized_data.get(STANDARDIZED_KEYS["email_raw"], "")
            email_limpo = None
            if email_bruto:
                email_limpo = email_bruto.lower()
                if Cliente.query.filter_by(email=email_limpo).first():
                    logger.info(
                        f"{log_prefix} Cliente com email '{email_limpo}' (CPF: {cpf_limpo}) já existe. Ignorando."
                    )
                    skipped_email_count += 1
                    continue
            else:
                logger.debug(
                    f"{log_prefix} Email não fornecido (CPF: {cpf_limpo}). Campo email será nulo."
                )
            dados_cliente_final["email"] = email_limpo

            # 3. Nomes
            pn_bruto = standardized_data.get(STANDARDIZED_KEYS["primeiro_nome"], "")
            sn_bruto = standardized_data.get(STANDARDIZED_KEYS["sobrenome"], "")

            if not pn_bruto:
                logger.warning(
                    f"{log_prefix} Primeiro nome vazio (CPF: {cpf_limpo}). Definido como None."
                )
                dados_cliente_final["primeiro_nome"] = None
            else:
                pn_modelo_limite = 64  # Limite do modelo Cliente.primeiro_nome
                if len(pn_bruto) > pn_modelo_limite:
                    logger.warning(
                        f"{log_prefix} Primeiro nome ('{pn_bruto}') truncado para {pn_modelo_limite} chars (CPF: {cpf_limpo})."
                    )
                    dados_cliente_final["primeiro_nome"] = pn_bruto[:pn_modelo_limite]
                else:
                    dados_cliente_final["primeiro_nome"] = pn_bruto

            sn_modelo_limite = 128  # Limite do modelo Cliente.sobrenome
            if sn_bruto and len(sn_bruto) > sn_modelo_limite:
                logger.warning(
                    f"{log_prefix} Sobrenome ('{sn_bruto}') truncado para {sn_modelo_limite} chars (CPF: {cpf_limpo})."
                )
                dados_cliente_final["sobrenome"] = sn_bruto[:sn_modelo_limite]
            else:
                dados_cliente_final["sobrenome"] = sn_bruto if sn_bruto else None

            # 4. Tipo de Pessoa (Padrão para FISICA)
            dados_cliente_final["tipo_pessoa"] = TipoPessoaEnum.FISICA

            # 5. Datas
            ts_raw = standardized_data.get(STANDARDIZED_KEYS["timestamp_raw"])
            dados_cliente_final["data_criacao"] = (
                parse_datetime(ts_raw) if ts_raw else datetime.now()
            )

            dt_nasc_raw = standardized_data.get(
                STANDARDIZED_KEYS["data_nascimento_raw"]
            )
            dados_cliente_final["data_nascimento"] = parse_data(dt_nasc_raw)
            if dt_nasc_raw and not dados_cliente_final["data_nascimento"]:
                logger.warning(
                    f"{log_prefix} Data de nascimento inválida: '{dt_nasc_raw}' (CPF: {cpf_limpo}). Será nula."
                )

            # 6. Estados (UF)
            uf_end_raw = standardized_data.get(STANDARDIZED_KEYS["endereco_estado_raw"])
            dados_cliente_final["endereco_estado"] = obter_sigla_estado(uf_end_raw)
            if uf_end_raw and not dados_cliente_final["endereco_estado"]:
                logger.warning(
                    f"{log_prefix} UF Endereço inválida: '{uf_end_raw}' (CPF: {cpf_limpo}). Será nula."
                )

            uf_rg_raw = standardized_data.get(
                STANDARDIZED_KEYS["rg_estado_emissor_raw"]
            )
            dados_cliente_final["rg_uf_emissor"] = obter_sigla_estado(uf_rg_raw)
            if uf_rg_raw and not dados_cliente_final["rg_uf_emissor"]:
                logger.warning(
                    f"{log_prefix} UF RG Emissor inválida: '{uf_rg_raw}' (CPF: {cpf_limpo}). Será nula."
                )

            # 7. Endereço
            # Para "Antigos", endereco_completo_raw vai para logradouro.
            # Para "Respostas", endereco_logradouro_raw é usado.
            if source_sheet_log == "Antigos":
                dados_cliente_final["endereco_logradouro"] = standardized_data.get(
                    STANDARDIZED_KEYS["endereco_completo_raw"], None
                )
                dados_cliente_final["endereco_numero"] = None
                dados_cliente_final["endereco_complemento"] = None
                dados_cliente_final["endereco_bairro"] = None
            else:  # "Respostas" ou outro formato que possa ter campos separados
                dados_cliente_final["endereco_logradouro"] = standardized_data.get(
                    STANDARDIZED_KEYS["endereco_logradouro_raw"], None
                )
                dados_cliente_final["endereco_numero"] = standardized_data.get(
                    STANDARDIZED_KEYS["endereco_numero_raw"], None
                )
                dados_cliente_final["endereco_complemento"] = standardized_data.get(
                    STANDARDIZED_KEYS["endereco_complemento_raw"], None
                )
                dados_cliente_final["endereco_bairro"] = standardized_data.get(
                    STANDARDIZED_KEYS["endereco_bairro_raw"], None
                )

            # Campos de endereço comuns a ambos os formatos (se existirem nas chaves padronizadas)
            dados_cliente_final["endereco_cidade"] = standardized_data.get(
                STANDARDIZED_KEYS["endereco_cidade_raw"], None
            )
            dados_cliente_final["endereco_cep"] = standardized_data.get(
                STANDARDIZED_KEYS["endereco_cep_raw"], None
            )

            # 8. Outros campos diretos (após normalização de chaves)
            # Os valores já foram ".strip()" durante apply_mapper_and_specific_logic
            dados_cliente_final["nacionalidade"] = standardized_data.get(
                STANDARDIZED_KEYS["nacionalidade_raw"], None
            )
            if (
                dados_cliente_final["nacionalidade"]
                and len(dados_cliente_final["nacionalidade"]) > 32
            ):
                logger.warning(
                    f"{log_prefix} Nacionalidade ('{dados_cliente_final['nacionalidade']}') truncada para 32 chars (CPF: {cpf_limpo})."
                )
                dados_cliente_final["nacionalidade"] = dados_cliente_final[
                    "nacionalidade"
                ][:32]

            dados_cliente_final["estado_civil"] = standardized_data.get(
                STANDARDIZED_KEYS["estado_civil_raw"], None
            )
            dados_cliente_final["profissao"] = standardized_data.get(
                STANDARDIZED_KEYS["profissao_raw"], None
            )
            dados_cliente_final["telefone_celular"] = standardized_data.get(
                STANDARDIZED_KEYS["telefone_celular_raw"], None
            )
            dados_cliente_final["telefone_outro"] = standardized_data.get(
                STANDARDIZED_KEYS["telefone_outro_raw"], None
            )
            dados_cliente_final["rg_numero"] = standardized_data.get(
                STANDARDIZED_KEYS["rg_numero_raw"], None
            )
            dados_cliente_final["cnh_numero"] = standardized_data.get(
                STANDARDIZED_KEYS["cnh_numero_raw"], None
            )

            # 9. Defaults e Auditoria
            dados_cliente_final.setdefault("data_atualizacao", datetime.now())

            # 10. Filtrar para colunas válidas do modelo Cliente
            colunas_validas_cliente = [c.name for c in Cliente.__table__.columns]
            dados_para_modelo_final = {
                k: v
                for k, v in dados_cliente_final.items()
                if k in colunas_validas_cliente
            }

            # Log de dados finais antes de criar o objeto (para depuração)
            # logger.debug(f"{log_prefix} Dados finais para modelo (CPF: {cpf_limpo}): {dados_para_modelo_final}")

            # 11. Criar e adicionar à sessão
            novo_cliente = Cliente(**dados_para_modelo_final)
            db.session.add(novo_cliente)
            imported_count += 1

        except Exception as e_row:
            db.session.rollback()
            logger.error(
                f"{log_prefix} !!! ERRO AO PROCESSAR LINHA (CPF: {standardized_data.get(STANDARDIZED_KEYS['cpf_raw'], 'N/A')}) !!! Dados padronizados: {standardized_data}. Erro: {e_row}",
                exc_info=True,
            )
            error_count += 1
            # Não interromper todo o processo por causa de uma linha, apenas logar e continuar
            # Se quiser interromper, descomente as linhas abaixo e o 'return'
            # click.echo(f"\n!!! ERRO FATAL AO PROCESSAR LINHA {source_row_log} da aba {source_sheet_log} !!!")
            # click.echo(f"Erro: {e_row}. INTERROMPENDO. Verifique os logs.")
            # return

    if error_count > 0:
        click.echo(
            f"AVISO: {error_count} linhas encontraram erros durante o processamento e foram ignoradas. Verifique os logs."
        )

    if imported_count > 0:
        try:
            db.session.commit()
            logger.info(f"{imported_count} clientes comitados ao banco de dados.")
            click.echo(f"{imported_count} clientes comitados ao banco de dados.")
        except Exception as e_commit_final:
            db.session.rollback()
            logger.error(
                f"Erro ao commitar clientes ao banco de dados no final: {e_commit_final}",
                exc_info=True,
            )
            click.echo(
                f"ERRO AO COMMITAR: {e_commit_final}. {imported_count} clientes não foram salvos."
            )
            error_count += imported_count
            imported_count = 0
    elif (
        error_count == 0 and total_rows_to_process > 0
    ):  # Nenhum importado, mas sem erros e havia linhas
        click.echo(
            "Nenhum cliente novo para importar (todos já existentes ou filtrados)."
        )
    elif total_rows_to_process == 0:
        click.echo("Nenhuma linha de dados encontrada nas planilhas para processar.")

    logger.info("Importação do Google Sheets concluída!")
    final_summary = (
        f"\nImportação do Google Sheets concluída!\n"
        f"Total de linhas de dados lidas e padronizadas: {total_rows_to_process}\n"
        f"Clientes novos importados com sucesso: {imported_count}\n"
        f"Clientes ignorados (CPF já existente): {skipped_cpf_count}\n"
        f"Clientes ignorados (Email já existente): {skipped_email_count}\n"
        f"Linhas com erro de processamento (ignoradas): {error_count}\n"
        f"Linhas vazias ignoradas (antes do mapeamento): {skipped_empty_count}"
    )
    logger.info(final_summary.replace("\n", " | "))  # Log em uma linha para facilitar
    click.echo(final_summary)


# Comandos find-client-by-cpf e find-client-by-email permanecem os mesmos
@click.command("find-client-by-cpf")
@click.argument("cpf_input")
@with_appcontext
def find_client_by_cpf_cli(cpf_input):
    """Busca e exibe informações de um cliente pelo CPF."""
    cpf_limpo = re.sub(r"[^0-9]", "", cpf_input)
    if not cpf_limpo:
        click.echo(
            "Erro: CPF fornecido é inválido após limpeza. Forneça um CPF com apenas números ou no formato XXX.XXX.XXX-XX."
        )
        return

    cliente = Cliente.query.filter_by(cpf=cpf_limpo).first()

    if cliente:
        click.echo(f"Cliente encontrado com CPF: {cpf_input} (limpo: {cpf_limpo})")
        click.echo(f"  ID: {cliente.id}")
        click.echo(
            f"  Nome: {cliente.primeiro_nome} {cliente.sobrenome if cliente.sobrenome else ''}"
        )
        click.echo(f"  Email: {cliente.email}")
        click.echo(f"  Telefone Celular: {cliente.telefone_celular}")
        click.echo(
            f"  Data de Nascimento: {cliente.data_nascimento.strftime('%d/%m/%Y') if cliente.data_nascimento else 'N/A'}"
        )
        click.echo(
            f"  Endereço: {cliente.endereco_logradouro}, {cliente.endereco_cidade} - {cliente.endereco_estado}"
        )
        click.echo(
            f"  Data de Criação: {cliente.data_criacao.strftime('%d/%m/%Y %H:%M:%S') if cliente.data_criacao else 'N/A'}"
        )
    else:
        click.echo(
            f"Nenhum cliente encontrado com o CPF: {cpf_input} (limpo: {cpf_limpo})"
        )


@click.command("find-client-by-email")
@click.argument("email_input")
@with_appcontext
def find_client_by_email_cli(email_input):
    """Busca e exibe informações de um cliente pelo email."""
    email_para_busca = email_input.strip()
    if not email_para_busca:
        click.echo("Erro: Email fornecido está vazio.")
        return

    cliente = Cliente.query.filter_by(email=email_para_busca).first()

    if cliente:
        click.echo(f"Cliente encontrado com Email: {email_para_busca}")
        click.echo(f"  ID: {cliente.id}")
        click.echo(
            f"  Nome: {cliente.primeiro_nome} {cliente.sobrenome if cliente.sobrenome else ''}"
        )
        click.echo(f"  CPF: {cliente.cpf}")
        click.echo(f"  Telefone Celular: {cliente.telefone_celular}")
        click.echo(
            f"  Data de Nascimento: {cliente.data_nascimento.strftime('%d/%m/%Y') if cliente.data_nascimento else 'N/A'}"
        )
        click.echo(
            f"  Endereço: {cliente.endereco_logradouro}, {cliente.endereco_cidade} - {cliente.endereco_estado}"
        )
        click.echo(
            f"  Data de Criação: {cliente.data_criacao.strftime('%d/%m/%Y %H:%M:%S') if cliente.data_criacao else 'N/A'}"
        )
    else:
        click.echo(f"Nenhum cliente encontrado com o Email: {email_para_busca}")
