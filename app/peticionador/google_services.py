import datetime
import locale
import logging
import re

from googleapiclient.errors import HttpError

from config import CONFIG

# Importa os serviços do google_client que usa a conta de serviço
from google_client import get_docs_service as gdocs_service_global
from google_client import get_drive_service as gdrive_service_global

logger = logging.getLogger(__name__)

# --- Funções de Interação com Google Drive e Docs usando Conta de Serviço ---


def extract_placeholders(docs_service, document_id):
    """Retorna uma lista de placeholders encontrados em um documento Google Docs.
    Placeholders são identificados no formato {{chave}} ou {{{{chave}}}}.
    """
    try:
        doc = docs_service.documents().get(documentId=document_id).execute()
        text = ""
        for content in doc.get("body", {}).get("content", []):
            if "paragraph" in content:
                elements = content["paragraph"].get("elements", [])
                for el in elements:
                    text_run = el.get("textRun")
                    if text_run and "content" in text_run:
                        text += text_run["content"]
            elif "table" in content:
                # Concatenate table cell text too
                for row in content["table"].get("tableRows", []):
                    for cell in row.get("tableCells", []):
                        for ce in cell.get("content", []):
                            for el in ce.get("paragraph", {}).get("elements", []):
                                tr = el.get("textRun")
                                if tr and "content" in tr:
                                    text += tr["content"]
        import re

        pattern = re.compile(r"\{\{\s*([\w\.-]+)\s*\}\}|\{\{\{\s*([\w\.-]+)\s*\}\}\}")
        ordered = []
        seen = set()
        for match in pattern.finditer(text):
            chave = match.group(1) or match.group(2)
            if chave not in seen:
                ordered.append(chave)
                seen.add(chave)
        return ordered
    except Exception as e:
        logger.error(f"Erro ao extrair placeholders do documento {document_id}: {e}")
        return []


def get_drive_service():
    """Retorna uma instância do serviço Google Drive autenticado via conta de serviço."""
    return gdrive_service_global()


def get_docs_service():
    """Retorna uma instância do serviço Google Docs autenticado via conta de serviço."""
    return gdocs_service_global()


def find_or_create_client_folder(drive_service, client_folder_name):
    """
    Procura uma pasta do cliente no Google Drive dentro do PARENT_FOLDER_ID configurado.
    Verifica se já existe uma pasta com o nome e sobrenome do cliente, independentemente do formato exato.
    Se não encontrar, cria uma nova pasta com o formato padronizado.

    client_folder_name: Nome da pasta do cliente (ex: "2024-Nome Sobrenome").
    Retorna o ID da pasta.
    """
    # Normaliza espaços extras no nome para evitar duplicação de pastas causadas por "  "
    client_folder_name = re.sub(r"\s+", " ", client_folder_name).strip()

    parent_folder_id = CONFIG.get("PARENT_FOLDER_ID")
    if not parent_folder_id:
        logger.error("PARENT_FOLDER_ID não configurado no .env ou config.py")
        return None

    if not drive_service:
        logger.error(
            "Serviço do Drive não disponível para find_or_create_client_folder"
        )
        return None

    # Extrair o ano e o nome do cliente do formato padrão "AAAA-Nome Sobrenome"
    import re

    match = re.match(r"^(\d{4})-(.*?)$", client_folder_name)

    if match:
        ano = match.group(1)
        nome_completo = match.group(2).strip()
    else:
        # Se não estiver no formato padrão, usar o ano atual e o nome completo como está
        from datetime import datetime

        ano = str(datetime.now().year)
        nome_completo = client_folder_name.strip()

    logger.info(f"Buscando pasta para cliente: Ano={ano}, Nome={nome_completo}")

    # Primeiro, tentar encontrar a pasta com o nome exato
    safe_client_folder_name = client_folder_name.replace("'", "\\'")
    query = f"name='{safe_client_folder_name}' and mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents and trashed=false"

    try:
        # Busca exata pelo nome completo da pasta
        response = (
            drive_service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )
        folders = response.get("files", [])

        if folders:
            logger.info(
                f"Pasta '{client_folder_name}' encontrada com ID: {folders[0]['id']} dentro de {parent_folder_id}"
            )
            return folders[0]["id"]

        # Se não encontrou com nome exato, buscar todas as pastas e filtrar pelo nome do cliente
        # Isso permite encontrar pastas mesmo que o formato seja ligeiramente diferente
        query_all_folders = f"mimeType='application/vnd.google-apps.folder' and '{parent_folder_id}' in parents and trashed=false"
        response = (
            drive_service.files()
            .list(
                q=query_all_folders,
                spaces="drive",
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        all_folders = response.get("files", [])
        nome_completo_lower = nome_completo.lower()

        # Verificar se alguma pasta contém o nome do cliente (ignorando maiúsculas/minúsculas)
        for folder in all_folders:
            folder_name = folder["name"]
            # Verificar se o nome da pasta contém o nome completo do cliente
            if nome_completo_lower in folder_name.lower():
                logger.info(
                    f"Pasta para '{nome_completo}' encontrada com nome similar: '{folder_name}', ID: {folder['id']}"
                )
                return folder["id"]
            # Verificar também se o nome da pasta contém o ano e o nome do cliente
            if ano in folder_name and nome_completo_lower in folder_name.lower():
                logger.info(
                    f"Pasta para '{ano}-{nome_completo}' encontrada com nome similar: '{folder_name}', ID: {folder['id']}"
                )
                return folder["id"]

        # Se não encontrou nenhuma pasta, criar uma nova com o formato padronizado
        logger.info(
            f"Pasta para '{nome_completo}' não encontrada. Criando pasta '{client_folder_name}' dentro de {parent_folder_id}..."
        )
        file_metadata = {
            "name": client_folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id],
        }
        folder = (
            drive_service.files()
            .create(body=file_metadata, fields="id", supportsAllDrives=True)
            .execute()
        )
        logger.info(f"Pasta '{client_folder_name}' criada com ID: {folder.get('id')}")
        return folder.get("id")
    except HttpError as error:
        logger.error(
            f"Erro ao procurar/criar pasta do cliente ({client_folder_name}): {error}"
        )
        return None


def check_document_exists(drive_service, file_name_base, target_folder_id):
    """
    Verifica se já existe um documento com o nome base fornecido na pasta de destino.
    Considera também variações com prefixo de data (ex: '2025-06-17 - Nome Original').

    Args:
        drive_service: Serviço do Google Drive autenticado.
        file_name_base: Nome base do arquivo a verificar.
        target_folder_id: ID da pasta onde verificar.

    Returns:
        Tuple (bool, str, str): (existe_documento, id_documento, link_documento)
            - existe_documento: True se encontrou documento existente, False caso contrário
            - id_documento: ID do documento encontrado ou None
            - link_documento: Link para o documento encontrado ou None
    """
    if not drive_service or not target_folder_id:
        logger.error(
            "Serviço do Drive não disponível ou pasta de destino não especificada"
        )
        return False, None, None

    try:
        # Escapar apóstrofos no nome do arquivo para a query
        safe_file_name = file_name_base.replace("'", "\\'")

        # Primeiro, verificar se existe um arquivo com o nome exato
        query = f"name='{safe_file_name}' and '{target_folder_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.document'"
        response = (
            drive_service.files()
            .list(
                q=query,
                fields="files(id, name, webViewLink)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        files = response.get("files", [])
        if files:
            logger.info(
                f"Documento com nome exato '{file_name_base}' encontrado: {files[0]['id']}"
            )
            return True, files[0]["id"], files[0].get("webViewLink")

        # Se não encontrou com nome exato, procurar por variações com prefixo de data
        # Padrão: YYYY-MM-DD - Nome Original
        date_prefix_pattern = r"^\d{4}-\d{2}-\d{2} - "
        query = f"'{target_folder_id}' in parents and trashed=false and mimeType='application/vnd.google-apps.document'"
        response = (
            drive_service.files()
            .list(
                q=query,
                fields="files(id, name, webViewLink)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        for file in response.get("files", []):
            # Verificar se o nome do arquivo corresponde ao padrão: DATA - NOME_BASE
            if re.match(date_prefix_pattern, file["name"]) and file["name"].endswith(
                file_name_base
            ):
                logger.info(
                    f"Documento com prefixo de data '{file['name']}' encontrado: {file['id']}"
                )
                return True, file["id"], file.get("webViewLink")
            # Verificar se o nome do arquivo é: DATA - NOME_BASE
            if re.match(
                date_prefix_pattern + re.escape(file_name_base) + "$", file["name"]
            ):
                logger.info(
                    f"Documento com prefixo de data '{file['name']}' encontrado: {file['id']}"
                )
                return True, file["id"], file.get("webViewLink")

        # Nenhum documento encontrado
        return False, None, None

    except HttpError as error:
        logger.error(
            f"Erro ao verificar existência do documento '{file_name_base}': {error}"
        )
        return False, None, None
    except Exception as e:
        logger.error(
            f"Erro inesperado ao verificar existência do documento '{file_name_base}': {e}"
        )
        return False, None, None


def copy_template_and_fill(
    drive_service,
    docs_service,
    template_id,
    new_file_name,
    target_folder_id,
    replacements,
):
    """
    Copia um template do Google Docs, move para a pasta de destino e substitui os placeholders.
    Verifica primeiro se já existe um documento com o mesmo nome para evitar duplicação.

    template_id: ID do arquivo de template no Google Docs.
    new_file_name: Nome do novo arquivo a ser criado.
    target_folder_id: ID da pasta onde o novo arquivo será salvo.
    replacements: Dicionário com {placeholder_sem_chaves: valor_a_substituir}.
                  Ex: {'cliente.nome': 'João Silva', 'processo.numero': '123'}
    Retorna o ID do novo documento e o link para visualização, ou (None, None) em caso de erro.
    """
    if not drive_service or not docs_service:
        logger.error(
            "Serviços do Drive ou Docs não disponíveis para copy_template_and_fill"
        )
        return None, None

    try:
        # 0. Verificar se já existe um documento com o mesmo nome ou variação com data
        document_exists, existing_doc_id, existing_doc_link = check_document_exists(
            drive_service, new_file_name, target_folder_id
        )

        if document_exists and existing_doc_id and existing_doc_link:
            logger.info(
                f"Documento '{new_file_name}' já existe (ID: {existing_doc_id}). Retornando referência ao documento existente."
            )
            return existing_doc_id, existing_doc_link

        # 1. Copiar o template se não existir documento
        # O nome do arquivo já deve ser o final, tratado pela rota que chama esta função.
        copied_file_metadata = {"name": new_file_name, "parents": [target_folder_id]}
        copied_file = (
            drive_service.files()
            .copy(
                fileId=template_id,
                body=copied_file_metadata,
                fields="id, webViewLink",  # Solicitar webViewLink para retorno
                supportsAllDrives=True,
            )
            .execute()
        )
        new_document_id = copied_file.get("id")
        new_document_link = copied_file.get("webViewLink")

        if not new_document_id:
            logger.error(
                f"Falha ao copiar o template '{template_id}'. ID do novo documento não encontrado."
            )
            return None, None
        logger.info(
            f"Template '{template_id}' copiado para novo documento '{new_file_name}' (ID: {new_document_id}) na pasta '{target_folder_id}'."
        )

        # 2. Substituir placeholders no documento copiado
        # Placeholders no template podem ser no formato {{CHAVE}} ou {{{CHAVE}}}
        # O dicionário 'replacements' deve ter chaves simples, ex: 'proprietario.nome_completo'
        requests_list = []
        for key, value in replacements.items():
            if value is not None:  # Não substituir se o valor for None
                text_to_replace = str(value)
                # Adicionar lógica de ZWSP para datas se necessário, como em document_generator.py
                # if key in ["data.nascimento", "data.fundacao"] and re.fullmatch(r'\d{2}/\d{2}/\d{4}', text_to_replace):
                #    text_to_replace = '\u200B' + text_to_replace

                # Tentar substituir placeholders no formato {{chave}}
                requests_list.append(
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": f"{{{{{key}}}}}",
                                "matchCase": False,
                            },
                            "replaceText": text_to_replace,
                        }
                    }
                )

                # Tentar substituir placeholders no formato {{{chave}}}
                requests_list.append(
                    {
                        "replaceAllText": {
                            "containsText": {
                                "text": f"{{{{{{{key}}}}}}}",
                                "matchCase": False,
                            },
                            "replaceText": text_to_replace,
                        }
                    }
                )

        if requests_list:
            docs_service.documents().batchUpdate(
                documentId=new_document_id, body={"requests": requests_list}
            ).execute()
            logger.info(
                f"Placeholders substituídos no documento {new_document_id} com {len(requests_list)} substituições."
            )
        else:
            logger.info(
                f"Nenhum placeholder para substituir no documento {new_document_id}"
            )

        return new_document_id, new_document_link

    except HttpError as error:
        logger.error(
            f"Erro ao copiar/preencher template (ID: {template_id}, Novo Nome: {new_file_name}): {error}"
        )
        # Considerar excluir o arquivo copiado se o preenchimento falhar e o ID for conhecido
        if new_document_id:
            try:
                drive_service.files().delete(
                    fileId=new_document_id, supportsAllDrives=True
                ).execute()
                logger.info(
                    f"Documento {new_document_id} excluído devido a erro no preenchimento."
                )
            except HttpError as delete_error:
                logger.error(
                    f"Erro ao tentar excluir documento {new_document_id} após falha: {delete_error}"
                )
        return None, None
    except Exception as e:
        logger.error(
            f"Erro inesperado em copy_template_and_fill (ID: {template_id}, Novo Nome: {new_file_name}): {e}"
        )
        return None, None


def get_current_date_extenso():
    """Retorna a data atual por extenso em português.
    Ex: 08 de junho de 2025
    """
    now = datetime.datetime.now()
    try:
        # Tenta configurar o locale para português do Brasil
        locale.setlocale(locale.LC_TIME, "pt_BR.UTF-8")
        # Formato: dia de NOMEDOMES de ANO
        # %d para dia com zero à esquerda (08), %B para nome completo do mês, %Y para ano com 4 dígitos.
        return now.strftime("%d de %B de %Y")
    except locale.Error:
        # Fallback para nomes de meses manuais se o locale pt_BR não estiver disponível
        logger.warning(
            "Locale 'pt_BR.UTF-8' não disponível. Usando fallback para nomes de meses."
        )
        meses = [
            "janeiro",
            "fevereiro",
            "março",
            "abril",
            "maio",
            "junho",
            "julho",
            "agosto",
            "setembro",
            "outubro",
            "novembro",
            "dezembro",
        ]
        return f"{now.day:02d} de {meses[now.month - 1]} de {now.year}"
    except Exception as e:
        logger.error(f"Erro inesperado ao formatar data por extenso: {e}")
        # Fallback muito básico em caso de outro erro
        return f"{now.day:02d}/{now.month:02d}/{now.year}"
