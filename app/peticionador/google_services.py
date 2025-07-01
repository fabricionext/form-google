import base64
import json
import logging
import os
import pickle
import io
import re

from flask import current_app
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

logger = logging.getLogger(__name__)


# Import the centralized Google authentication
from app.utils.google_auth import get_google_credentials as get_google_creds

def get_google_credentials():
    """Use the centralized Google authentication module."""
    return get_google_creds()


class GoogleDriveService:
    def __init__(self):
        self.creds = get_google_credentials()
        self.service = build("drive", "v3", credentials=self.creds)

    def copy_file(self, file_id: str, new_name: str, destination_folder_id: str):
        try:
            original_file = self.service.files().get(fileId=file_id, fields='mimeType').execute()
            mime_type = original_file.get('mimeType')

            if 'google-apps.document' in mime_type:
                file_metadata = {"name": new_name, "parents": [destination_folder_id]}
                copied_file = (
                    self.service.files()
                    .copy(fileId=file_id, body=file_metadata, fields="id, webViewLink")
                    .execute()
                )
                logger.info(f"Arquivo do Google Docs copiado com sucesso. ID: {copied_file['id']}")
                return copied_file["id"], copied_file.get("webViewLink")
            else:
                request = self.service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    logger.info(f"Download {int(status.progress() * 100)}%.")
                
                fh.seek(0)
                
                file_metadata = {'name': new_name, 'parents': [destination_folder_id]}
                media = MediaIoBaseUpload(fh, mimetype=mime_type, resumable=True)
                
                uploaded_file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()

                logger.info(f"Arquivo '{new_name}' enviado com sucesso para o Drive. ID: {uploaded_file['id']}")
                return uploaded_file["id"], uploaded_file.get("webViewLink")

        except HttpError as error:
            logger.error(f"Erro ao copiar arquivo no Drive: {error}")
            error_details = error.content.decode('utf-8')
            logger.error(f"Detalhes do erro: {error_details}")
            if 'file not found' in error_details.lower():
                raise FileNotFoundError(f"Arquivo com ID '{file_id}' não encontrado no Google Drive.")
            elif 'cannot be copied' in error_details.lower():
                 raise PermissionError(f"Permissões insuficientes para copiar o arquivo '{file_id}'.")
            else:
                 raise IOError(f"Erro genérico ao interagir com a API do Google Drive: {error_details}")
        except Exception as e:
            logger.error(f"Erro inesperado ao copiar arquivo: {e}", exc_info=True)
            raise


class GoogleDocsService:
    def __init__(self):
        self.creds = get_google_credentials()
        self.service = build("docs", "v1", credentials=self.creds)

    def replace_placeholders(self, doc_id: str, replacements: dict):
        try:
            requests_list = [
                {
                    "replaceAllText": {
                        "containsText": {"text": f"{{{{{key}}}}}", "matchCase": "true"},
                        "replaceText": str(value),
                    }
                }
                for key, value in replacements.items() if value is not None
            ]

            if requests_list:
                self.service.documents().batchUpdate(
                    documentId=doc_id, body={"requests": requests_list}
                ).execute()
                logger.info(f"Placeholders substituídos com sucesso no documento {doc_id}.")
            
            return True

        except HttpError as error:
            logger.error(f"Erro ao substituir placeholders no Docs: {error}")
            error_details = error.content.decode('utf-8')
            logger.error(f"Detalhes do erro: {error_details}")
            raise IOError(f"Erro ao interagir com a API do Google Docs: {error_details}")
        except Exception as e:
            logger.error(f"Erro inesperado ao substituir placeholders: {e}", exc_info=True)
            raise


def get_drive_service() -> GoogleDriveService:
    return GoogleDriveService()


def get_docs_service() -> GoogleDocsService:
    return GoogleDocsService()


def extract_placeholders_from_document(document_id: str) -> list:
    try:
        docs_service = get_docs_service().service
        document = docs_service.documents().get(documentId=document_id).execute()
        content = document.get("body").get("content")
        
        placeholders = set()
        regex = r"\{\{([^{}]+)\}\}"
        
        if content:
            for element in content:
                if "paragraph" in element:
                    for run in element.get("paragraph").get("elements"):
                        text = run.get("textRun", {}).get("content", "")
                        if text:
                            found = re.findall(regex, text)
                            if found:
                                placeholders.update(found)
                        
        logger.info(f"Placeholders encontrados em '{document_id}': {list(placeholders)}")
        return list(placeholders)

    except HttpError as error:
        logger.error(f"Erro ao extrair placeholders do documento '{document_id}': {error}")
        error_details = error.content.decode('utf-8')
        logger.error(f"Detalhes do erro: {error_details}")
        if 'not found' in error_details.lower():
            raise FileNotFoundError(f"Documento com ID '{document_id}' não encontrado.")
        elif 'permission' in error_details.lower():
            raise PermissionError(f"Sem permissão para ler o documento '{document_id}'.")
        else:
            raise
    except Exception as e:
        logger.error(f"Erro inesperado na extração de placeholders: {e}", exc_info=True)
        raise 