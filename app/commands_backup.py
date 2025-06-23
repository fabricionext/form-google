import csv
import logging
import re
from typing import Any, Dict, List, Optional

import click

# Configure basic logging to output to console
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to capture all levels of logs
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[logging.StreamHandler()],  # Output to stderr by default
)
logger = logging.getLogger(__name__)

import os
from datetime import datetime

from flask.cli import with_appcontext
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2 import service_account
from googleapiclient.discovery import build

from extensions import db  # Alterado para importar de extensions.py
from models import (  # Importa Cliente e TipoPessoaEnum de models.py
    Cliente,
    TipoPessoaEnum,
)

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


def obter_sigla_estado(valor_estado_csv):
    if not valor_estado_csv:
        return None

    valor_limpo = valor_estado_csv.strip().upper()

    # Tenta extrair sigla do formato "XX - NOME COMPLETO"
    if " - " in valor_limpo:
        partes = valor_limpo.split(" - ", 1)
        sigla_potencial = partes[0]
        if len(sigla_potencial) == 2 and sigla_potencial in ESTADOS_SIGLAS.values():
            return sigla_potencial

    # Tenta mapear pelo nome completo
    if valor_limpo in ESTADOS_SIGLAS:
        return ESTADOS_SIGLAS[valor_limpo]

    # Se já for uma sigla válida
    if len(valor_limpo) == 2 and valor_limpo in ESTADOS_SIGLAS.values():
        return valor_limpo

    click.echo(
        f"Aviso: Não foi possível mapear o estado '{valor_estado_csv}' para uma sigla. Será deixado em branco."
    )
    return None


def parse_data(date_string, default_format="%d/%m/%Y"):
    """Converte uma string de data para um objeto date.
    Tenta limpar a string e também formatos como dd/mm/yy."""
    if not date_string:
        return None
    date_str_cleaned = date_string.strip()
    if not date_str_cleaned:
        return None

    try:
        return datetime.strptime(date_str_cleaned, default_format).date()
    except ValueError:
        # Tentar remover caracteres não numéricos exceto '/' e ver se forma uma data válida
        # Ex: '01/05/198_' -> '01/05/198'
        cleaned_further = re.sub(r"[^0-9/]", "", date_str_cleaned)
        try:
            # Tentar com ano completo
            return datetime.strptime(cleaned_further, "%d/%m/%Y").date()
        except ValueError:
            try:
                # Tentar com ano de dois dígitos (ex: 01/01/8_) - pode ser problemático para séculos
                if len(cleaned_further.split("/")[-1]) < 4:
                    return datetime.strptime(cleaned_further, "%d/%m/%y").date()
            except ValueError:
                click.echo(
                    f"Aviso: Formato de data de nascimento inválido '{date_string}' (tentativa com '{cleaned_further}'). Será deixado nulo."
                )
                return None
        click.echo(
            f"Aviso: Formato de data de nascimento inválido '{date_string}'. Será deixado nulo."
        )
        return None


def get_google_sheets_service():
    """Autentica com a API do Google Sheets usando uma conta de serviço e retorna o objeto de serviço."""
    logger.info("Attempting to get Google Sheets service.")
    creds = None
    service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    sheet_name = os.getenv("SHEET_NAME")

    logger.debug(f"Service account file from env: {service_account_file}")
    logger.debug(f"Spreadsheet ID from env: {spreadsheet_id}")
    logger.debug(f"Sheet name from env: {sheet_name}")

    if not service_account_file:
        logger.error(
            "Erro: A variável de ambiente GOOGLE_SERVICE_ACCOUNT_JSON não está configurada."
        )
        return None
    if not spreadsheet_id:
        logger.error(
            "Erro: A variável de ambiente SPREADSHEET_ID não está configurada."
        )
        return None
    if not sheet_name:
        logger.error("Erro: A variável de ambiente SHEET_NAME não está configurada.")
        return None

    try:
        logger.debug(f"Attempting to load credentials from: {service_account_file}")
        creds = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )
        logger.info("Successfully loaded credentials from service account file.")

        logger.debug("Attempting to build Google Sheets service object.")
        service = build("sheets", "v4", credentials=creds)
        logger.info("Successfully built Google Sheets service object.")

        logger.info("Returning Google Sheets service object.")
        return service
    except FileNotFoundError:
        logger.error(
            f"Arquivo da conta de serviço não encontrado em {service_account_file}",
            exc_info=True,
        )
        logger.info("Returning None due to FileNotFoundError.")
        return None
    except DefaultCredentialsError:
        logger.error(
            "Credenciais padrão não encontradas. Verifique a configuração da conta de serviço.",
            exc_info=True,
        )
        logger.info("Returning None due to DefaultCredentialsError.")
        return None
    except Exception as e:
        logger.error(f"Erro ao autenticar com Google Sheets API: {e}", exc_info=True)
        logger.info("Returning None due to other exception during authentication.")
        return None


def get_google_sheets_data(service, full_sheet_range: str) -> Optional[List[List[str]]]:
    """Retorna os dados da planilha do Google Sheets."""
    logger.info("Attempting to fetch data from Google Sheets API...")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=full_sheet_range)
            .execute()
        )
        logger.info("Successfully fetched data from Google Sheets API.")
        logger.debug(
            f"Raw API result (summary): keys={result.keys() if isinstance(result, dict) else 'Not a dict'}, range={result.get('range', 'N/A') if isinstance(result, dict) else 'N/A'}, num_values_rows={len(result.get('values', [])) if isinstance(result, dict) else 'N/A'})"
        )
        values = result.get("values", [])
        logger.debug(
            f"Extracted values (first 3 rows if many, total {len(values)} rows): {values[:3]}"
        )
        return values
    except Exception as e:
        logger.error(f"Erro ao buscar dados do Google Sheets: {e}", exc_info=True)
        return None


def parse_datetime(datetime_str, default_now_if_invalid=True):
    """Converte uma string de data/hora para um objeto datetime.
    Tenta múltiplos formatos comuns."""
    if not datetime_str:
        return datetime.now() if default_now_if_invalid else None

    datetime_str_cleaned = datetime_str.strip()
    if not datetime_str_cleaned:
        return datetime.now() if default_now_if_invalid else None

    formatos_tentar = [
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d %H:%M:%S",  # Formato ISO comum
        "%Y-%m-%d %H:%M",  # Formato ISO comum sem segundos
        "%d/%m/%Y",  # Apenas data, hora será meia-noite
    ]

    for fmt in formatos_tentar:
        try:
            dt_obj = datetime.strptime(datetime_str_cleaned, fmt)
            # Se o formato for apenas data, definir hora como 00:00:00 para consistência
            if fmt == "%d/%m/%Y":
                dt_obj = dt_obj.replace(hour=0, minute=0, second=0)
            return dt_obj
        except ValueError:
            continue

    click.echo(
        f"Aviso: Formato de data/hora inválido para '{datetime_str}'. Tentados formatos: {formatos_tentar}. Usando data/hora atual."
    )
    return datetime.now() if default_now_if_invalid else None


@click.command("import-clients")
@with_appcontext
def import_clients_cli():
    """Importa clientes diretamente de uma planilha Google Sheets."""
    logger.info("Starting import_clients_cli command.")
    click.echo("Iniciando importação de clientes do Google Sheets...")

    logger.info("Calling get_google_sheets_service().")
    service = get_google_sheets_service()
    logger.info(f"get_google_sheets_service() returned: {service}")
    if not service:
        logger.error("Failed to get Google Sheets service. Aborting import.")
        return

    try:  # MAIN TRY BLOCK
        # SPREADSHEET_ID é usado por get_google_sheets_data internamente via os.getenv

        sheets_to_import_config = [
            {"name": "Respostas", "range": "Respostas!A1:Z278"},
            {"name": "Antigos", "range": "Antigos!A1:Z190"},
        ]

        clientes_para_importar = []
        skipped_empty_count = 0

        logger.info(
            f"Iniciando processamento de {len(sheets_to_import_config)} abas: {', '.join([s['name'] for s in sheets_to_import_config])}"
        )

        for config in sheets_to_import_config:
            sheet_display_name = config["name"]
            sheet_full_range = config["range"]

            logger.info(
                f"Processando aba: '{sheet_display_name}' com range: '{sheet_full_range}'"
            )
            click.echo(f"Processando aba: {sheet_display_name}...")

            sheet_values = get_google_sheets_data(service, sheet_full_range)

            if not sheet_values:
                logger.warning(
                    f"Nenhum dado retornado para a aba '{sheet_display_name}' (range: {sheet_full_range}). Pulando esta aba."
                )
                click.echo(
                    f"Nenhum dado ou erro ao ler a aba '{sheet_display_name}'. Pulando."
                )
                continue

            if len(sheet_values) == 0:
                logger.warning(
                    f"Aba '{sheet_display_name}' (range: {sheet_full_range}) retornou uma lista vazia. Pulando esta aba."
                )
                click.echo(f"Aba '{sheet_display_name}' está vazia. Pulando.")
                continue

            current_sheet_headers = [str(header).strip() for header in sheet_values[0]]
            logger.info(
                f"Cabeçalhos detectados na aba '{sheet_display_name}': {', '.join(current_sheet_headers)}"
            )
            # click.echo(f"Cabeçalhos da aba '{sheet_display_name}': {', '.join(current_sheet_headers)}") # Pode ser verboso

            current_sheet_data_rows = sheet_values[1:]

            if not current_sheet_data_rows:
                logger.info(
                    f"Nenhuma linha de dados encontrada na aba '{sheet_display_name}' (após o cabeçalho)."
                )

            processed_rows_in_sheet = 0
            for r_idx, row_data_list in enumerate(current_sheet_data_rows):
                row_as_dict = {}
                num_headers = len(current_sheet_headers)
                num_cells_in_row = len(row_data_list)

                for c_idx, header_name in enumerate(current_sheet_headers):
                    if c_idx < num_cells_in_row:
                        cell_value = row_data_list[c_idx]
                        row_as_dict[header_name] = (
                            str(cell_value).strip() if cell_value is not None else ""
                        )
                    else:
                        row_as_dict[header_name] = ""

                if all(not value for value in row_as_dict.values()):
                    logger.info(
                        f"Linha {r_idx + 2} da aba '{sheet_display_name}' ignorada por ser considerada vazia."
                    )
                    skipped_empty_count += 1
                    continue

                clientes_para_importar.append(row_as_dict)
                processed_rows_in_sheet += 1

            logger.info(
                f"Concluído processamento da aba '{sheet_display_name}'. {processed_rows_in_sheet} linhas de dados válidas adicionadas de {len(current_sheet_data_rows)} lidas (após cabeçalho)."
            )

        logger.info(
            f"Total de {len(clientes_para_importar)} clientes agregados de todas as abas para processamento."
        )
        logger.info(
            f"Total de {skipped_empty_count} linhas vazias ignoradas em todas as abas."
        )

        total_rows = len(clientes_para_importar)
        imported_count = 0
        skipped_cpf_count = 0
        skipped_email_count = 0
        error_count = 0

        mapeamento_colunas = {
            "Carimbo de data/hora": "data_criacao",
            "Primeiro Nome": "primeiro_nome",
            "Sobrenome": "sobrenome",
            "Nacionalidade": "nacionalidade",
            "Estado Civil": "estado_civil",
            "Profissão": "profissao",
            "Endereço": "endereco_logradouro",
            "Cidade": "endereco_cidade",
            "Estado": "endereco_estado_csv",
            "CEP": "endereco_cep",
            "Telefone celular": "telefone_celular",
            "Outro Telefone": "telefone_outro",
            "E-mail": "email",
            "Data de nascimento": "data_nascimento_csv",
            "RG": "rg_numero",
            "Estado emissor do RG": "rg_uf_emissor_csv",
            "CPF": "cpf",
            "Digite sua CNH (opcional):": "cnh_numero",
        }

        coluna_cpf_planilha_header = next(
            (k for k, v in mapeamento_colunas.items() if v == "cpf"), "CPF"
        )
        coluna_nacionalidade_header = next(
            (k for k, v in mapeamento_colunas.items() if v == "nacionalidade"),
            "Nacionalidade",
        )

        for idx, row_data in enumerate(clientes_para_importar):
            linha_num_planilha = idx + 2
            dados_cliente = {}

            # Tratamento especial para Primeiro Nome e Sobrenome (Aba "Antigos" vs "Respostas")
            # Cabeçalhos conforme definidos em mapeamento_colunas
            coluna_pn_header = "Primeiro Nome"
            coluna_sn_header = "Sobrenome"

            primeiro_nome_bruto_ws = row_data.get(coluna_pn_header, "")
            sobrenome_bruto_ws = row_data.get(coluna_sn_header, "")

            primeiro_nome_valor_limpo = (
                primeiro_nome_bruto_ws.strip() if primeiro_nome_bruto_ws else ""
            )
            sobrenome_valor_limpo = (
                sobrenome_bruto_ws.strip() if sobrenome_bruto_ws else ""
            )

            cpf_para_log = row_data.get(coluna_cpf_planilha_header, "N/A")

            if primeiro_nome_valor_limpo and not sobrenome_valor_limpo:
                # Provavelmente formato da aba "Antigos" (nome completo em "Primeiro Nome")
                # ou formato "Respostas" onde o sobrenome foi deixado em branco.
                partes_nome = primeiro_nome_valor_limpo.split(" ", 1)
                dados_cliente["primeiro_nome"] = partes_nome[0]
                dados_cliente["sobrenome"] = (
                    partes_nome[1] if len(partes_nome) > 1 else ""
                )
                if (
                    not sobrenome_bruto_ws
                ):  # Só loga a divisão se o campo sobrenome original da planilha estava realmente vazio
                    logger.info(
                        f"Linha {linha_num_planilha}: Nome completo '{primeiro_nome_valor_limpo}' (em '{coluna_pn_header}') dividido. PN='{dados_cliente['primeiro_nome']}', SN='{dados_cliente['sobrenome']}'. CPF: {cpf_para_log}"
                    )
            elif primeiro_nome_valor_limpo:
                # Formato "Respostas" com ambos os campos, ou "Antigos" onde por algum motivo o sobrenome foi preenchido.
                dados_cliente["primeiro_nome"] = primeiro_nome_valor_limpo
                dados_cliente["sobrenome"] = sobrenome_valor_limpo
            else:
                # Caso "Primeiro Nome" (da planilha) seja vazio. Sobrenome também será None.
                dados_cliente["primeiro_nome"] = None
                dados_cliente["sobrenome"] = None
                logger.warning(
                    f"Linha {linha_num_planilha}: '{coluna_pn_header}' está vazio. Nome e Sobrenome definidos como None. CPF: {cpf_para_log}"
                )

            # Truncamento e log se necessário (assumindo limites do modelo: primeiro_nome=64, sobrenome=128)
            # TODO: Verificar os limites reais no modelo Cliente e ajustar se necessário.
            pn_modelo_limite = 64
            sn_modelo_limite = 128

            if (
                dados_cliente.get("primeiro_nome")
                and len(dados_cliente["primeiro_nome"]) > pn_modelo_limite
            ):
                pn_original = dados_cliente["primeiro_nome"]
                dados_cliente["primeiro_nome"] = pn_original[:pn_modelo_limite]
                logger.warning(
                    f"Linha {linha_num_planilha}: Primeiro nome ('{pn_original}') truncado para '{dados_cliente['primeiro_nome']}' ({pn_modelo_limite} chars). CPF: {cpf_para_log}"
                )

            if (
                dados_cliente.get("sobrenome")
                and len(dados_cliente["sobrenome"]) > sn_modelo_limite
            ):
                sn_original = dados_cliente["sobrenome"]
                dados_cliente["sobrenome"] = sn_original[:sn_modelo_limite]
                logger.warning(
                    f"Linha {linha_num_planilha}: Sobrenome ('{sn_original}') truncado para '{dados_cliente['sobrenome']}' ({sn_modelo_limite} chars). CPF: {cpf_para_log}"
                )

            try:  # INNER TRY FOR EACH ROW
                # 1. Mapeamento e tratamento inicial da nacionalidade
                nacionalidade_bruta = row_data.get(coluna_nacionalidade_header, None)
                if nacionalidade_bruta and len(nacionalidade_bruta) > 32:
                    logger.warning(
                        f"Linha {linha_num_planilha}: Valor de nacionalidade ('{nacionalidade_bruta}') excede 32 caracteres. Será omitido. CPF: {row_data.get(coluna_cpf_planilha_header, '')}"
                    )
                    dados_cliente["nacionalidade"] = None
                else:
                    dados_cliente["nacionalidade"] = (
                        nacionalidade_bruta.strip() if nacionalidade_bruta else None
                    )

                # Mapear outros campos
                for nome_coluna_planilha, campo_modelo in mapeamento_colunas.items():
                    if campo_modelo not in [
                        "nacionalidade",
                        "primeiro_nome",
                        "sobrenome",
                    ]:  # Evita sobrescrever campos já tratados
                        dados_cliente[campo_modelo] = row_data.get(
                            nome_coluna_planilha, ""
                        ).strip()

                # Logs de depuração para campos problemáticos
                target_cpf_debug = "030.145.628-31"  # CPF da planilha para Valter Berti
                if cpf_para_log.strip() == target_cpf_debug:
                    logger.info(
                        f"--- DEBUGGING VALTER BERTI (CPF Planilha: {cpf_para_log}, Linha: {linha_num_planilha}) ---"
                    )
                    logger.info(f"Raw row_data: {row_data}")

                    email_key_original = "E-mail"  # Chave conforme planilha
                    email_val_raw = row_data.get(email_key_original)
                    logger.info(
                        f"Tentando obter '{email_key_original}'. Valor de row_data.get('{email_key_original}'): '{email_val_raw}'"
                    )
                    logger.info(
                        f"dados_cliente['email'] após mapeamento geral: '{dados_cliente.get('email')}'"
                    )

                    tel_key_original = "Telefone celular"  # Chave conforme planilha
                    tel_val_raw = row_data.get(tel_key_original)
                    logger.info(
                        f"Tentando obter '{tel_key_original}'. Valor de row_data.get('{tel_key_original}'): '{tel_val_raw}'"
                    )
                    logger.info(
                        f"dados_cliente['telefone_celular'] após mapeamento geral: '{dados_cliente.get('telefone_celular')}'"
                    )

                    estado_key_original = "Estado"  # Chave conforme planilha
                    estado_val_raw = row_data.get(estado_key_original)
                    logger.info(
                        f"Tentando obter '{estado_key_original}'. Valor de row_data.get('{estado_key_original}'): '{estado_val_raw}'"
                    )
                    logger.info(
                        f"dados_cliente['endereco_estado_csv'] após mapeamento geral: '{dados_cliente.get('endereco_estado_csv')}'"
                    )
                    logger.info(f"--- END DEBUGGING VALTER BERTI ---")

                # 2. Validação de CPF
                cpf_bruto = dados_cliente.get("cpf", "")  # Usa o campo_modelo 'cpf'
                if not cpf_bruto:
                    logger.warning(
                        f"Linha {linha_num_planilha} ignorada. CPF não fornecido."
                    )
                    error_count += 1
                    continue

                cpf_limpo = re.sub(r"[^0-9]", "", cpf_bruto)
                if not cpf_limpo:
                    logger.warning(
                        f"Linha {linha_num_planilha} ignorada. CPF inválido ou vazio após limpeza: '{cpf_bruto}'."
                    )
                    error_count += 1
                    continue

                if Cliente.query.filter_by(cpf=cpf_limpo).first():
                    logger.warning(
                        f"Cliente com CPF {cpf_limpo} (linha {linha_num_planilha}) já existe. Ignorando."
                    )
                    skipped_cpf_count += 1
                    continue
                dados_cliente["cpf"] = cpf_limpo

                # 3. Validação de Email
                email_bruto = dados_cliente.get(
                    "email", ""
                )  # Usa o campo_modelo 'email'
                email_limpo = None
                if email_bruto:
                    email_limpo = email_bruto.lower()
                    if Cliente.query.filter_by(email=email_limpo).first():
                        logger.warning(
                            f"Cliente com email '{email_limpo}' (linha {linha_num_planilha}, CPF: {cpf_limpo}) já existe. Ignorando."
                        )
                        skipped_email_count += 1
                        continue
                else:
                    logger.warning(
                        f"Email não fornecido na linha {linha_num_planilha} (CPF: {cpf_limpo}). O campo email será nulo."
                    )
                dados_cliente["email"] = email_limpo

                # 4. Definir tipo de pessoa
                dados_cliente["tipo_pessoa"] = TipoPessoaEnum.FISICA

                # 5. Conversões de dados
                if dados_cliente.get("data_criacao"):
                    dados_cliente["data_criacao"] = parse_datetime(
                        dados_cliente.get("data_criacao")
                    )
                else:
                    dados_cliente["data_criacao"] = datetime.now()

                if dados_cliente.get("data_nascimento_csv"):
                    dados_cliente["data_nascimento"] = parse_data(
                        dados_cliente.get("data_nascimento_csv")
                    )

                if dados_cliente.get("endereco_estado_csv"):
                    dados_cliente["endereco_estado"] = obter_sigla_estado(
                        dados_cliente.get("endereco_estado_csv")
                    )

                if dados_cliente.get("rg_uf_emissor_csv"):
                    dados_cliente["rg_uf_emissor"] = obter_sigla_estado(
                        dados_cliente.get("rg_uf_emissor_csv")
                    )

                # 6. Remover chaves auxiliares
                dados_cliente.pop("data_nascimento_csv", None)
                dados_cliente.pop("endereco_estado_csv", None)
                dados_cliente.pop("rg_uf_emissor_csv", None)

                # 7. Defaults
                dados_cliente.setdefault("data_atualizacao", datetime.now())

                # 8. Filtrar para colunas válidas do modelo
                colunas_validas_cliente = [c.name for c in Cliente.__table__.columns]
                dados_para_modelo = {
                    k: v
                    for k, v in dados_cliente.items()
                    if k in colunas_validas_cliente
                }

                # 9. Criar e adicionar
                novo_cliente = Cliente(**dados_para_modelo)
                db.session.add(novo_cliente)
                imported_count += 1

            except Exception as e_row:  # INNER EXCEPT FOR EACH ROW
                db.session.rollback()
                logger.error(
                    f"!!! ERRO AO PROCESSAR LINHA {linha_num_planilha} !!! Dados brutos: {row_data}. Erro: {e_row}",
                    exc_info=True,
                )
                error_count += 1
                click.echo(
                    f"\n!!! ERRO FATAL AO PROCESSAR LINHA {linha_num_planilha} !!!"
                )
                click.echo(f"Dados da linha problemática: {row_data}")
                click.echo(f"Erro específico: {e_row}")
                click.echo(
                    "INTERROMPENDO PROCESSAMENTO. Verifique os logs detalhados para o traceback completo."
                )

                if db.session.new:
                    try:
                        db.session.commit()
                        logger.info(
                            f"Progresso parcial ({imported_count} clientes) comitado antes da interrupção."
                        )
                        click.echo(
                            f"Progresso parcial ({imported_count} clientes) comitado antes da interrupção."
                        )
                    except Exception as e_commit_partial:
                        db.session.rollback()
                        logger.error(
                            f"Erro ao tentar commitar progresso parcial: {e_commit_partial}",
                            exc_info=True,
                        )
                        click.echo(
                            f"Erro ao tentar commitar progresso parcial: {e_commit_partial}"
                        )
                return

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
                    f"Erro ao commitar {imported_count} clientes ao banco de dados: {e_commit_final}"
                )
                error_count += imported_count
                imported_count = 0

        logger.info("Importação do Google Sheets concluída!")
        logger.info(f"Total de linhas de dados lidas (após cabeçalho): {total_rows}")
        logger.info(f"Clientes novos importados com sucesso: {imported_count}")
        logger.info(f"Clientes ignorados (CPF já existente): {skipped_cpf_count}")
        logger.info(f"Clientes ignorados (Email já existente): {skipped_email_count}")
        logger.info(f"Linhas com erro de processamento (ignoradas): {error_count}")
        logger.info(f"Linhas vazias ignoradas: {skipped_empty_count}")

        click.echo(f"\nImportação do Google Sheets concluída!")
        click.echo(f"Total de linhas de dados lidas (após cabeçalho): {total_rows}")
        click.echo(f"Clientes novos importados com sucesso: {imported_count}")
        click.echo(f"Clientes ignorados (CPF já existente): {skipped_cpf_count}")
        click.echo(f"Clientes ignorados (Email já existente): {skipped_email_count}")
        click.echo(f"Linhas com erro de processamento (ignoradas): {error_count}")
        click.echo(f"Linhas vazias ignoradas: {skipped_empty_count}")

    except Exception as e:  # MAIN EXCEPT BLOCK, CORRECTLY ALIGNED
        db.session.rollback()
        logger.error(
            f"Erro geral durante a importação do Google Sheets: {e}", exc_info=True
        )
        click.echo(f"Erro geral durante a importação do Google Sheets: {e}")


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
