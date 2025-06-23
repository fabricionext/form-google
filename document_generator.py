import datetime
import json
import logging
import os
import re

from dateutil import parser as dateutil_parser  # Para formatação de datas
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import CONFIG

logger = logging.getLogger(__name__)

MAPEAMENTO_CHAVES_TEMPLATE_PF = {
    "primeiroNome": "Primeiro Nome",
    "sobrenome": "Sobrenome",
    "nacionalidade": "Nacionalidade",
    "estadoCivil": "Estado Civil",
    "profissao": "Profissão",
    "dataNascimento": "Nascimento",
    "cpf": "CPF",
    "rg": "RG",
    "estadoEmissorRG": "Estado emissor do RG",
    "cnh": "CNH",
    "cep": "Endereço_CEP",
    "logradouro": "Endereço_Logradouro",
    "numero": "Endereço_Numero",
    "complemento": "Endereço_Complemento",
    "bairro": "Endereço_Bairro",
    "cidade": "Endereço_Cidade",
    "estado": "Endereço_Estado",
    "email": "E-mail",
    "telefoneCelular": "Telefone Celular",
    "outroTelefone": "Outro telefone",
}

MAPEAMENTO_CHAVES_TEMPLATE_PJ = {
    "razaoSocial": "Razão Social",
    "nomeFantasia": "Nome Fantasia",
    "cnpj": "CNPJ",
    "inscricaoEstadual": "Inscrição Estadual",
    "dataFundacao": "Data de Fundação",
    "cep": "Endereço_CEP",
    "logradouro": "Endereço_Logradouro",
    "numero": "Endereço_Numero",
    "complemento": "Endereço_Complemento",
    "bairro": "Endereço_Bairro",
    "cidade": "Endereço_Cidade",
    "estado": "Endereço_Estado",
    "email": "E-mail",  # Email principal da PJ
    "telefoneCelular": "Telefone Celular",  # Telefone principal da PJ (pode ser fixo ou móvel)
    "outroTelefone": "Outro telefone",
    # Campos de contato para PJ (ajuste os placeholders conforme seu template)
    "nomeCompletoContato": "Nome Contato PJ",  # Ex: se o payload enviar 'nomeCompletoContato'
    "emailContato": "E-mail Contato PJ",
    "telefoneContato": "Telefone Contato PJ",
    "cargoContato": "Cargo Contato PJ",
}
# Configurar o logger se ainda não estiver configurado no app principal
if not logger.hasHandlers():
    logging.basicConfig(
        level=logging.INFO
    )  # Ajustado para INFO, DEBUG pode ser muito verboso

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


def _initialize_google_services(credentials_json_str):
    """
    Inicializa e retorna as instâncias dos serviços Google Drive e Docs.
    """
    if not credentials_json_str:
        logger.error(
            "_initialize_google_services: String JSON de credenciais está vazia ou nula."
        )
        raise ValueError("A string JSON de credenciais não pode ser vazia.")
    try:
        creds_info = json.loads(credentials_json_str)
    except json.JSONDecodeError as e:
        logger.error(
            f"_initialize_google_services: Erro ao decodificar string JSON de credenciais: {e}"
        )
        raise ValueError(f"String JSON de credenciais inválida: {e}")

    credentials = service_account.Credentials.from_service_account_info(
        creds_info, scopes=SCOPES
    )
    drive_service = build("drive", "v3", credentials=credentials)
    docs_service = build("docs", "v1", credentials=credentials)
    logger.info(
        "_initialize_google_services: Serviços Google Drive e Docs inicializados com sucesso."
    )
    return drive_service, docs_service


def _gerar_nome_arquivo_unico(drive_service, nome_base_com_ano, id_pasta_cliente):
    """
    Verifica se um arquivo com nome_base_com_ano já existe na id_pasta_cliente.
    Se existir, retorna um novo nome com a data (AAAA-MM-DD) atual como prefixo.
    Caso contrário, retorna o nome_base_com_ano.
    """
    nome_final = nome_base_com_ano
    logger.debug(
        f"_gerar_nome_arquivo_unico: Verificando nome '{nome_base_com_ano}' na pasta '{id_pasta_cliente}'"
    )
    try:
        # Escapar apóstrofos no nome_base_com_ano para a query
        nome_base_escapado = nome_base_com_ano.replace("'", "\\'")
        query = f"name='{nome_base_escapado}' and '{id_pasta_cliente}' in parents and trashed=false and mimeType != 'application/vnd.google-apps.folder'"
        response = (
            drive_service.files()
            .list(
                q=query,
                fields="files(id)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,  # Importante para Shared Drives
            )
            .execute()
        )
        logger.debug(f"_gerar_nome_arquivo_unico: Resposta da busca: {response}")
        if response.get("files"):
            data_prefixo = datetime.datetime.now().strftime("%Y-%m-%d")  # AAAA-MM-DD
            nome_final = f"{data_prefixo} - {nome_base_com_ano}"  # Ex: 2025-06-07 - 2025-Nome Sobrenome-Tipo de Arquivo
    except HttpError as error:
        logger.error(
            f"_gerar_nome_arquivo_unico: HttpError ao verificar nome de arquivo existente: {error}. Query: {query}"
        )
        pass  # Em caso de erro na verificação, prossegue com o nome base
    return nome_final


def buscar_ou_criar_pasta_cliente(drive_service, primeiro_nome, sobrenome, ano=None):
    """
    Busca ou cria a pasta do cliente no Google Drive seguindo o padrão [[ano]]-[[Nome]] [[Sobrenome]].
    Retorna o ID da pasta.
    """
    if not ano:
        ano = datetime.datetime.now().year
    nome_pasta = f"{ano}-{primeiro_nome} {sobrenome}"
    parent_id = CONFIG["PARENT_FOLDER_ID"]
    logger.debug(
        f"buscar_ou_criar_pasta_cliente: Buscando/criando pasta '{nome_pasta}' com PARENT_FOLDER_ID = '{parent_id}'"
    )

    # Busca pasta existente
    query = f"name='{nome_pasta}' and mimeType='application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed=false"
    response = (
        drive_service.files()
        .list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,  # Adicionado/Confirmado
            includeItemsFromAllDrives=True,  # Adicionado
        )
        .execute()
    )
    logger.debug(
        f"buscar_ou_criar_pasta_cliente: Resposta da busca de pasta: {response}"
    )
    files = response.get("files", [])
    if files:
        return files[0]["id"]

    # Cria pasta se não existir
    file_metadata = {
        "name": nome_pasta,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    logger.debug(
        f"buscar_ou_criar_pasta_cliente: Criando pasta com metadata: {file_metadata}"
    )
    pasta = (
        drive_service.files()
        .create(body=file_metadata, fields="id", supportsAllDrives=True)
        .execute()
    )
    logger.debug(f"buscar_ou_criar_pasta_cliente: Pasta criada: {pasta}")
    return pasta["id"]


def duplicar_template_para_pasta(drive_service, id_template, nome_arquivo, id_pasta):
    """
    Duplica o template no Drive e move para a pasta do cliente.
    Retorna o ID do novo arquivo.
    """
    logger.debug(
        f"duplicar_template_para_pasta: Duplicando template ID '{id_template}' para '{nome_arquivo}' na pasta '{id_pasta}'"
    )
    # Copia o arquivo
    body = {"name": nome_arquivo, "parents": [id_pasta]}
    try:
        copia = (
            drive_service.files()
            .copy(fileId=id_template, body=body, fields="id", supportsAllDrives=True)
            .execute()
        )
        logger.debug(
            f"duplicar_template_para_pasta: Template duplicado. Novo ID: {copia.get('id')}"
        )
    except HttpError as error:
        logger.error(
            f"duplicar_template_para_pasta: HttpError ao copiar template ID '{id_template}': {error}. Body: {body}"
        )
        raise
    return copia["id"]


def preencher_variaveis_doc(docs_service, id_documento, dados_cliente):
    """
    Preenche as variáveis do template no Google Docs.
    """
    logger.debug(
        f"preencher_variaveis_doc: Preenchendo documento ID '{id_documento}' com dados: {dados_cliente}"
    )
    requests = []
    variaveis = dados_cliente
    for chave, valor in variaveis.items():
        if valor is not None:
            texto_a_substituir = str(valor)

            # Se a chave for um campo de data conhecido e o valor estiver no formato DD/MM/AAAA,
            # adiciona um Zero-Width Space para tentar evitar auto-formatação pelo Google Docs.
            if chave in ["Data de Nascimento", "Data de Fundação"]:
                if isinstance(texto_a_substituir, str) and texto_a_substituir:
                    # Verifica se o formato é DD/MM/YYYY antes de adicionar ZWSP
                    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", texto_a_substituir):
                        texto_a_substituir = "\u200b" + texto_a_substituir

            placeholder = f"{{{{{chave}}}}}"
            requests.append(
                {
                    "replaceAllText": {
                        "containsText": {"text": placeholder, "matchCase": True},
                        "replaceText": texto_a_substituir,
                    }
                }
            )
    try:
        docs_service.documents().batchUpdate(
            documentId=id_documento, body={"requests": requests}
        ).execute()
        logger.debug(
            f"preencher_variaveis_doc: Variáveis preenchidas com sucesso no documento ID '{id_documento}'. Requests: {requests}"
        )
    except HttpError as e:
        logger.error(
            f"preencher_variaveis_doc: HttpError ao preencher variáveis do documento ID '{id_documento}': {e}. Requests: {requests}"
        )
        raise


def gerar_documento_cliente(
    drive_service,
    docs_service,
    id_template,
    tipo_doc,
    dados_cliente,
    id_pasta_cliente,
    tipo_pessoa,
):
    logger.info(
        f"[gerar_documento_cliente] Iniciando geração para tipo_doc: {tipo_doc}, tipo_pessoa: {tipo_pessoa}"
    )
    logger.info(
        f"[gerar_documento_cliente] Dados do cliente recebidos: {dados_cliente}"
    )
    logger.debug(
        f"gerar_documento_cliente: Iniciando geração para tipo_doc='{tipo_doc}', tipo_pessoa='{tipo_pessoa}', id_pasta_cliente='{id_pasta_cliente}'. Dados cliente: {dados_cliente}"
    )
    primeiro_nome = dados_cliente.get("Primeiro Nome") or dados_cliente.get(
        "primeiro_nome"
    )
    sobrenome = dados_cliente.get("Sobrenome") or dados_cliente.get("sobrenome")
    # ano e id_pasta não são mais tratados aqui, id_pasta_cliente é recebido como argumento

    # Acessar CONFIG diretamente pode ser problemático em threads se não inicializado corretamente no contexto da app.
    # Idealmente, CONFIG também seria passado ou acessado de forma segura.
    # Por agora, mantemos, mas é um ponto de atenção para robustez em threads complexas.
    id_template = CONFIG["TEMPLATES"][tipo_pessoa][tipo_doc]

    ano_documento = datetime.datetime.now().year  # Ano de criação do documento

    nome_identificador_cliente = ""
    ano_atual = datetime.datetime.now().year
    logger.info(
        f"[gerar_documento_cliente] Gerando nome de arquivo para tipo_pessoa: {tipo_pessoa}"
    )

    if tipo_pessoa == "pf":
        primeiro_nome_val = dados_cliente.get("primeiroNome")
        sobrenome_val = dados_cliente.get("sobrenome")
        logger.info(
            f"[gerar_documento_cliente] PF - primeiroNome: '{primeiro_nome_val}', sobrenome: '{sobrenome_val}'"
        )

        nome_parts = []
        if (
            primeiro_nome_val
            and str(primeiro_nome_val).strip().lower() != "none"
            and str(primeiro_nome_val).strip() != ""
        ):
            nome_parts.append(str(primeiro_nome_val).strip())
        if (
            sobrenome_val
            and str(sobrenome_val).strip().lower() != "none"
            and str(sobrenome_val).strip() != ""
        ):
            nome_parts.append(str(sobrenome_val).strip())

        if nome_parts:
            nome_identificador_cliente = " ".join(nome_parts)
        else:
            logger.warning(
                "[gerar_documento_cliente] PF - Nome e Sobrenome ausentes ou 'None'. Usando fallback."
            )

    elif tipo_pessoa == "pj":
        razao_social_val = dados_cliente.get("razaoSocial")
        nome_fantasia_val = dados_cliente.get("nomeFantasia")
        logger.info(
            f"[gerar_documento_cliente] PJ - razaoSocial: '{razao_social_val}', nomeFantasia: '{nome_fantasia_val}'"
        )

        if (
            razao_social_val
            and str(razao_social_val).strip().lower() != "none"
            and str(razao_social_val).strip() != ""
        ):
            nome_identificador_cliente = str(razao_social_val).strip()
        elif (
            nome_fantasia_val
            and str(nome_fantasia_val).strip().lower() != "none"
            and str(nome_fantasia_val).strip() != ""
        ):
            nome_identificador_cliente = str(nome_fantasia_val).strip()
        else:
            logger.warning(
                "[gerar_documento_cliente] PJ - Razão Social e Nome Fantasia ausentes ou 'None'. Usando fallback."
            )

    # Sanitizar nome_identificador_cliente para remover caracteres que podem ser problemáticos em nomes de arquivo
    # Esta é uma sanitização básica, pode ser necessário expandir.
    if not nome_identificador_cliente:  # Se após as lógicas acima, continuar vazio
        nome_identificador_cliente = "Cliente"
        logger.info(
            "[gerar_documento_cliente] Usando 'Cliente' como identificador padrão."
        )

    logger.info(
        f"[gerar_documento_cliente] Nome identificador bruto: '{nome_identificador_cliente}'"
    )
    nome_identificador_cliente_sanitizado = (
        nome_identificador_cliente.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("*", "_")
        .replace("?", "_")
        .replace('"', "_")
        .replace("<", "_")
        .replace(">", "_")
        .replace("|", "_")
        .strip()
    )
    if (
        not nome_identificador_cliente_sanitizado
    ):  # Caso o nome resulte em string vazia após sanitização
        nome_identificador_cliente_sanitizado = "Cliente"
        logger.info(
            "[gerar_documento_cliente] Nome sanitizado resultou em vazio, usando 'Cliente'."
        )
    logger.info(
        f"[gerar_documento_cliente] Nome identificador sanitizado: '{nome_identificador_cliente_sanitizado}'"
    )

    # --- AJUSTE DO PADRÃO DO NOME DO ARQUIVO ---
    data_atual = datetime.datetime.now().strftime("%d-%m-%Y")
    nome_arquivo_base_formatado = (
        f"{data_atual}-{nome_identificador_cliente_sanitizado}-{tipo_doc}"
    )
    logger.info(
        f"[gerar_documento_cliente] Nome base do arquivo formatado: '{nome_arquivo_base_formatado}'"
    )

    # Gerar nome único para o arquivo, verificando duplicidade do nome formatado
    nome_arquivo_final = _gerar_nome_arquivo_unico(
        drive_service, nome_arquivo_base_formatado, id_pasta_cliente
    )

    id_novo_doc = duplicar_template_para_pasta(
        drive_service, id_template, nome_arquivo_final, id_pasta_cliente
    )
    # Selecionar o mapa de chaves apropriado
    if tipo_pessoa == "pf":
        mapa_chaves = MAPEAMENTO_CHAVES_TEMPLATE_PF
    elif tipo_pessoa == "pj":
        mapa_chaves = MAPEAMENTO_CHAVES_TEMPLATE_PJ
    else:
        logger.error(
            f"Tipo de pessoa '{tipo_pessoa}' desconhecido para mapeamento de chaves."
        )
        # Fallback para um mapa vazio ou levantar um erro, dependendo da política desejada
        mapa_chaves = {}

    dados_para_template = {}
    logger.info(
        f"[gerar_documento_cliente] Iniciando mapeamento de dados para template. Mapa usado: {mapa_chaves}"
    )
    for chave_payload, valor_payload in dados_cliente.items():
        logger.debug(
            f"[gerar_documento_cliente] Processando payload: chave='{chave_payload}', valor='{valor_payload}'"
        )
        chave_template = mapa_chaves.get(chave_payload)
        if chave_template:
            if valor_payload is not None:
                # Formatação especial para datas conhecidas
                if chave_template in ["Nascimento", "Data de Fundação"]:
                    try:
                        logger.debug(
                            f"[gerar_documento_cliente] Tentando formatar data para chave_template '{chave_template}' com valor_payload '{valor_payload}'"
                        )
                        data_obj = dateutil_parser.parse(str(valor_payload))
                        valor_formatado = data_obj.strftime("%d/%m/%Y")
                        dados_para_template[chave_template] = valor_formatado
                        logger.debug(
                            f"[gerar_documento_cliente] Data formatada para '{chave_template}': '{valor_formatado}'"
                        )
                    except (ValueError, TypeError, OverflowError) as e_date:
                        logger.warning(
                            f"Não foi possível formatar a data para a chave_template '{chave_template}' com valor_payload '{valor_payload}'. Erro: {e_date}. Usando valor original."
                        )
                        dados_para_template[chave_template] = str(
                            valor_payload
                        )  # Fallback para string original
                else:
                    dados_para_template[chave_template] = str(valor_payload)
                logger.debug(
                    f"[gerar_documento_cliente] Mapeado: dados_para_template['{chave_template}'] = '{dados_para_template[chave_template]}' (original: '{valor_payload}')"
                )
            else:
                dados_para_template[chave_template] = ""
        else:
            # Opcional: Logar chaves não mapeadas. Pode ser útil durante o desenvolvimento.
            # logger.debug(f"Chave do payload '{chave_payload}' não mapeada para template para tipo_pessoa '{tipo_pessoa}'.")
            # Se quiser passar chaves não mapeadas diretamente (caso haja placeholders que coincidam):
            # dados_para_template[chave_payload] = str(valor_payload) if valor_payload is not None else ''
            pass  # Ignorar chaves não mapeadas por padrão para evitar poluir o template com dados inesperados

    # Adicionar data de preenchimento formatada
    data_preenchimento_valor = datetime.datetime.now().strftime("%d/%m/%Y")
    dados_para_template["Data_Preenchimento"] = data_preenchimento_valor
    logger.info(
        f"[gerar_documento_cliente] Adicionada 'Data_Preenchimento': '{data_preenchimento_valor}'"
    )

    logger.info(
        f"[gerar_documento_cliente] Dados finais para template antes de preencher_variaveis_doc: {dados_para_template}"
    )
    preencher_variaveis_doc(docs_service, id_novo_doc, dados_para_template)
    link = f"https://docs.google.com/document/d/{id_novo_doc}/edit"
    return {
        "id_documento": id_novo_doc,
        "link_documento": link,
        "pasta_id": id_pasta_cliente,
        "nome_arquivo": nome_arquivo_final,
        "tipo_doc": tipo_doc,
    }  # Retorna id_pasta_cliente, nome_arquivo_final e tipo_doc


# Exemplo de uso (agora seria mais complexo devido à necessidade dos services):
# drive_s, docs_s = _initialize_google_services(json_credentials_string)
# pasta_id = buscar_ou_criar_pasta_cliente(drive_s, 'Nome', 'Teste')
# resultado = gerar_documento_cliente(drive_s, docs_s, 'Ficha Cadastral', dados_cliente, 'pf', pasta_id)
# print(resultado)


def gerar_todos_os_documentos_para_cliente(
    form_data, tipo_pessoa, credentials_json_str, documentos_solicitados=None
):
    """
    Função orquestradora principal para gerar todos os documentos para um cliente.
    Esta função será chamada em uma thread.
    """
    logger.info(
        f"gerar_todos_os_documentos_para_cliente: Iniciando para tipo_pessoa='{tipo_pessoa}'."
    )
    try:
        drive_service, docs_service = _initialize_google_services(credentials_json_str)
    except ValueError as e:
        logger.error(
            f"gerar_todos_os_documentos_para_cliente: Falha ao inicializar serviços Google: {e}"
        )
        return {
            "status": "erro",
            "mensagem": f"Falha ao inicializar serviços Google: {e}",
            "documentos_gerados": [],
        }

    # Determinar nome e sobrenome para a pasta
    if tipo_pessoa == "pf":
        primeiro_nome_pasta = form_data.get("primeiroNome") or form_data.get(
            "Primeiro Nome"
        )
        sobrenome_pasta = form_data.get("sobrenome") or form_data.get("Sobrenome")

        if not primeiro_nome_pasta and form_data.get("nomeCompleto"):
            nome_completo_str = str(form_data.get("nomeCompleto", ""))
            partes_nome = nome_completo_str.split(" ", 1)
            primeiro_nome_pasta = partes_nome[0]
            if len(partes_nome) > 1:
                sobrenome_pasta = partes_nome[1]
            else:
                # Se não houver sobrenome após a divisão, podemos deixar None ou vazio.
                # A função buscar_ou_criar_pasta_cliente concatenará o que tiver.
                sobrenome_pasta = None
        elif not primeiro_nome_pasta and not form_data.get("nomeCompleto"):
            logger.warning(
                "Nem 'primeiroNome'/'Primeiro Nome' nem 'nomeCompleto' foram fornecidos para PF."
            )
    elif tipo_pessoa == "pj":
        primeiro_nome_pasta = form_data.get("razaoSocial") or form_data.get(
            "Razão Social"
        )  # Usar Razao Social como "primeiro nome" para pasta PJ
        sobrenome_pasta = "PJ"  # Usar "PJ" como "sobrenome" para pasta PJ, ou deixar em branco/outro identificador
    else:
        logger.error(
            f"gerar_todos_os_documentos_para_cliente: Tipo de pessoa desconhecido: {tipo_pessoa}"
        )
        return {
            "status": "erro",
            "mensagem": f"Tipo de pessoa desconhecido: {tipo_pessoa}",
            "documentos_gerados": [],
        }

    if not primeiro_nome_pasta:
        logger.error(
            f"gerar_todos_os_documentos_para_cliente: Não foi possível determinar o nome principal para a pasta do cliente."
        )
        return {
            "status": "erro",
            "mensagem": "Nome principal para pasta do cliente ausente.",
            "documentos_gerados": [],
        }

    try:
        id_pasta_cliente = buscar_ou_criar_pasta_cliente(
            drive_service, primeiro_nome_pasta, sobrenome_pasta
        )
        logger.info(
            f"gerar_todos_os_documentos_para_cliente: Pasta do cliente '{primeiro_nome_pasta} {sobrenome_pasta}' ID: {id_pasta_cliente}"
        )
    except Exception as e:
        logger.error(
            f"gerar_todos_os_documentos_para_cliente: Erro ao buscar/criar pasta do cliente: {e}",
            exc_info=True,
        )
        return {
            "status": "erro",
            "mensagem": f"Erro ao buscar/criar pasta do cliente: {e}",
            "documentos_gerados": [],
        }

    documentos_gerados = []
    templates_para_gerar = CONFIG.get("TEMPLATES", {}).get(tipo_pessoa, {})
    if not templates_para_gerar:
        logger.warning(
            f"gerar_todos_os_documentos_para_cliente: Nenhum template definido em CONFIG para tipo_pessoa='{tipo_pessoa}'"
        )
        return {
            "status": "aviso",
            "mensagem": f"Nenhum template definido para {tipo_pessoa}",
            "documentos_gerados": [],
            "id_pasta_cliente": id_pasta_cliente,
        }

    for tipo_doc, id_template in templates_para_gerar.items():
        if documentos_solicitados and tipo_doc not in documentos_solicitados:
            logger.info(
                f"gerar_todos_os_documentos_para_cliente: Documento '{tipo_doc}' não solicitado. Pulando..."
            )
            continue  # Pula para o próximo template se este não foi solicitado
        if not id_template:
            logger.warning(
                f"Template ID para '{tipo_doc}' não encontrado ou vazio em CONFIG. Pulando..."
            )
            continue
        try:
            logger.info(
                f"gerar_todos_os_documentos_para_cliente: Gerando documento '{tipo_doc}' com template ID '{id_template}'..."
            )
            resultado_doc = gerar_documento_cliente(
                drive_service=drive_service,
                docs_service=docs_service,
                id_template=id_template,
                tipo_doc=tipo_doc,
                dados_cliente=form_data,
                id_pasta_cliente=id_pasta_cliente,
                tipo_pessoa=tipo_pessoa,
            )
            documentos_gerados.append(resultado_doc)
            logger.info(
                f"gerar_todos_os_documentos_para_cliente: Documento '{tipo_doc}' gerado: {resultado_doc.get('link_documento')}"
            )
        except Exception as e:
            logger.error(
                f"gerar_todos_os_documentos_para_cliente: Erro ao gerar documento '{tipo_doc}': {e}",
                exc_info=True,
            )
            documentos_gerados.append(
                {"tipo_doc": tipo_doc, "status": "erro", "mensagem": str(e)}
            )

    sucessos = [d for d in documentos_gerados if d.get("status") == "sucesso"]
    erros = [d for d in documentos_gerados if d.get("status") == "erro"]

    mensagem_retorno = f"{len(sucessos)} documento(s) gerado(s) com sucesso."
    if erros:
        mensagem_retorno += f" {len(erros)} com erro."
    if not documentos_gerados and documentos_solicitados:
        mensagem_retorno = "Nenhum dos documentos solicitados foi encontrado nos templates configurados ou pôde ser gerado."
    elif not documentos_gerados:
        mensagem_retorno = "Nenhum documento foi gerado."

    logger.info(
        f"gerar_todos_os_documentos_para_cliente: Processo finalizado. {mensagem_retorno} Documentos processados: {documentos_gerados}"
    )
    return {
        "status": "sucesso",
        "mensagem": mensagem_retorno,
        "documentos_processados": documentos_gerados,
        "id_pasta_cliente": id_pasta_cliente,
    }
