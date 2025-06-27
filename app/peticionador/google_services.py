import datetime
import locale
import logging
import re
import uuid

from googleapiclient.errors import HttpError

from config import CONFIG

logger = logging.getLogger(__name__)

# NENHUMA importação de google_client aqui

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


def get_current_date_formatted():
    """Retorna a data atual no formato dd/mm/AAAA.
    Ex: 25/06/2025
    """
    now = datetime.datetime.now()
    return now.strftime("%d/%m/%Y")

class DocumentGenerationService:
    def __init__(self):
        self.drive_service = None
        self.docs_service = None

    def _initialize_services(self):
        if not self.drive_service or not self.docs_service:
            from google_client import get_drive_service, get_docs_service
            self.drive_service = get_drive_service()
            self.docs_service = get_docs_service()

    def find_or_create_client_folder(self, client_folder_name):
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

        if not self.drive_service:
            logger.error(
                "Serviço do Drive não disponível para find_or_create_client_folder"
            )
            return None

        # Extrair o ano e o nome do cliente do formato padrão "AAAA-Nome Sobrenome"
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
                self.drive_service.files()
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
                self.drive_service.files()
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
                self.drive_service.files()
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

    def check_document_exists(self, file_name_base, target_folder_id):
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
        if not self.drive_service or not target_folder_id:
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
                self.drive_service.files()
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
                self.drive_service.files()
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

    def copy_template_and_fill(self, template_id, new_file_name, target_folder_id, replacements):
        """
        Copia um template do Google Docs, move para a pasta de destino e substitui os placeholders.
        Sempre cria um novo documento (nome único).
        Retorna o ID do novo documento e o link para visualização, ou (None, None) em caso de erro.
        """
        logger.info(f"[copy_template_and_fill] Iniciando geração de documento: template_id={template_id}, nome_base={new_file_name}, pasta_destino={target_folder_id}")

        if not self.drive_service or not self.docs_service:
            logger.error(
                "Serviços do Drive ou Docs não disponíveis para copy_template_and_fill"
            )
            return None, None

        try:
            # Forçar nome único: adicionar timestamp e UUID curto
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            unique_suffix = uuid.uuid4().hex[:6]
            unique_file_name = f"{new_file_name} - {timestamp}-{unique_suffix}"
            logger.info(f"[copy_template_and_fill] Nome final do documento: {unique_file_name}")

            # 1. Copiar o template
            copied_file_metadata = {"name": unique_file_name, "parents": [target_folder_id]}
            logger.info(f"[copy_template_and_fill] Copiando template {template_id} para pasta {target_folder_id}...")
            copied_file = (
                self.drive_service.files()
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
                f"Template '{template_id}' copiado para novo documento '{unique_file_name}' (ID: {new_document_id}) na pasta '{target_folder_id}'."
            )

            # 2. Substituir placeholders no documento copiado
            requests_list = []
            for key, value in replacements.items():
                if value is not None:
                    text_to_replace = str(value)
                    requests_list.append(
                        {
                            "replaceAllText": {
                                "containsText": {"text": f"{{{{{key}}}}}", "matchCase": False},
                                "replaceText": text_to_replace,
                            }
                        }
                    )
                    requests_list.append(
                        {
                            "replaceAllText": {
                                "containsText": {"text": f"{{{{{{{key}}}}}}}", "matchCase": False},
                                "replaceText": text_to_replace,
                            }
                        }
                    )
            if requests_list:
                logger.info(f"[copy_template_and_fill] Substituindo {len(requests_list)} placeholders no documento {new_document_id}...")
                self.docs_service.documents().batchUpdate(
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
            return None, None
        except Exception as e:
            logger.error(
                f"Erro inesperado ao copiar/preencher template (ID: {template_id}, Novo Nome: {new_file_name}): {e}"
            )
            return None, None

    def generate_documents(self, dados_cliente, tipo_pessoa, documentos_requeridos):
        """
        Orquestra a geração de todos os documentos para um cliente.
        """
        self._initialize_services()
        
        links_documentos_gerados = []
        
        # Define o nome da pasta do cliente
        nome_cliente_para_pasta = f"{dados_cliente.get('primeiroNome', 'Cliente')} {dados_cliente.get('sobrenome', '')}".strip()
        ano_atual = datetime.datetime.now().year
        nome_pasta_cliente = f"{ano_atual}-{nome_cliente_para_pasta}"

        # Encontra ou cria a pasta do cliente no Drive
        id_pasta_cliente = self.find_or_create_client_folder(nome_pasta_cliente)
        if not id_pasta_cliente:
            logger.error(f"Não foi possível criar ou encontrar a pasta para o cliente: {nome_cliente_para_pasta}")
            return []

        # Itera sobre os documentos requeridos e os templates correspondentes
        for doc_nome, template_id in CONFIG.get("DOCUMENT_TEMPLATES", {}).get(tipo_pessoa, {}).items():
            if documentos_requeridos and documentos_requeridos.get(doc_nome):
                
                data_formatada = datetime.datetime.now().strftime("%Y-%m-%d")
                nome_base_arquivo = f"{data_formatada} - {nome_cliente_para_pasta} - {doc_nome.replace('_', ' ').title()}"
                
                # Prepara os placeholders para substituição
                replacements = {f"{{{{{key}}}}}": str(value) for key, value in dados_cliente.items() if value is not None}
                replacements["{{data_extenso}}"] = get_current_date_extenso()

                # Gera o documento
                id_documento, link_documento = self.copy_template_and_fill(
                    template_id=template_id,
                    new_file_name=nome_base_arquivo,
                    target_folder_id=id_pasta_cliente,
                    replacements=replacements
                )
                
                if link_documento:
                    links_documentos_gerados.append(link_documento)

        return links_documentos_gerados


# === FUNÇÕES DE COMPATIBILIDADE ===
# Essas funções são necessárias para manter compatibilidade com o código existente

def extract_placeholders(docs_service, document_id):
    """
    Extrai placeholders de um documento do Google Docs.
    Função melhorada que retorna apenas as chaves como strings para evitar problemas de compatibilidade.
    """
    try:
        document = docs_service.documents().get(documentId=document_id).execute()
        from app.peticionador.routes import extract_placeholders_keys_only
        return extract_placeholders_keys_only(document)
    except Exception as e:
        logger.error(f"Erro ao extrair placeholders do documento {document_id}: {e}")
        return []


def copy_template_and_fill(drive_service, docs_service, template_id, new_file_name, target_folder_id, replacements):
    """
    Função de compatibilidade que usa a classe DocumentGenerationService.
    """
    doc_service = DocumentGenerationService()
    doc_service.drive_service = drive_service
    doc_service.docs_service = docs_service
    return doc_service.copy_template_and_fill(template_id, new_file_name, target_folder_id, replacements)


def find_or_create_client_folder(drive_service, client_folder_name):
    """
    Função de compatibilidade que usa a classe DocumentGenerationService.
    """
    doc_service = DocumentGenerationService()
    doc_service.drive_service = drive_service
    return doc_service.find_or_create_client_folder(client_folder_name)


def create_drive_service():
    """
    Função de compatibilidade para criar o serviço do Drive.
    """
    from google_client import get_drive_service
    return get_drive_service()


def create_docs_service():
    """
    Função de compatibilidade para criar o serviço do Docs.
    """
    from google_client import get_docs_service
    return get_docs_service()


def create_folder_if_not_exists(drive_service, folder_name, parent_folder_id):
    """
    Função de compatibilidade para criar pasta se não existir.
    """
    doc_service = DocumentGenerationService()
    doc_service.drive_service = drive_service
    return doc_service.find_or_create_client_folder(folder_name)


def generate_google_docs_from_template_peticionador(drive_service, docs_service, template_id, new_file_name, target_folder_id, replacements):
    """
    Função de compatibilidade para gerar documento a partir de template.
    """
    return copy_template_and_fill(drive_service, docs_service, template_id, new_file_name, target_folder_id, replacements)
