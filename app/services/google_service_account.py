"""
Serviço de autenticação via Service Account para Google Drive API.
Implementa autenticação com conta de serviço para acesso server-side.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.utils.exceptions import (
    GoogleDriveException,
    ConfigurationException,
    AuthenticationException
)

logger = logging.getLogger(__name__)


class GoogleServiceAccountAuth:
    """
    Serviço de autenticação usando Service Account.
    
    Usa conta de serviço ubuntu-server@app-script-459322.iam.gserviceaccount.com
    para acessar Google Drive API sem necessidade de OAuth interativo.
    """
    
    # Escopos necessários para o sistema
    SCOPES = [
        'https://www.googleapis.com/auth/drive',  # Acesso completo ao Drive
        'https://www.googleapis.com/auth/documents',  # Acesso completo ao Docs
        'https://www.googleapis.com/auth/drive.file',  # Criar e modificar arquivos
        'https://www.googleapis.com/auth/drive.metadata'  # Metadados
    ]
    
    # Informações da conta de serviço
    SERVICE_ACCOUNT_EMAIL = 'ubuntu-server@app-script-459322.iam.gserviceaccount.com'
    SERVICE_ACCOUNT_ID = '117107719744923312244'
    
    def __init__(self):
        """Inicializa o serviço de autenticação."""
        self.credentials_file = self._get_service_account_file()
        self.credentials = None
        self._initialize_credentials()
        
    def _get_service_account_file(self) -> str:
        """Obtém o caminho do arquivo da conta de serviço."""
        # Tenta várias possibilidades de localização
        possible_paths = [
            os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'),
            '/var/www/estevaoalmeida.com.br/form-google/app-script-459322-990ad4e6c8ea.json',
            'app-script-459322-990ad4e6c8ea.json',
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app-script-459322-990ad4e6c8ea.json')
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                logger.info(f"Arquivo de conta de serviço encontrado: {path}")
                return path
        
        raise ConfigurationException(
            'GOOGLE_SERVICE_ACCOUNT_JSON',
            f'Arquivo de conta de serviço não encontrado. Tentativas: {possible_paths}'
        )
    
    def _initialize_credentials(self):
        """Inicializa as credenciais da conta de serviço."""
        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=self.SCOPES
            )
            logger.info(f"Credenciais da conta de serviço inicializadas: {self.SERVICE_ACCOUNT_EMAIL}")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar credenciais: {e}")
            raise AuthenticationException(f"Falha na inicialização da conta de serviço: {e}")
    
    def get_drive_service(self):
        """
        Obtém serviço do Google Drive autenticado.
        
        Returns:
            Serviço do Google Drive
        """
        try:
            if not self.credentials:
                self._initialize_credentials()
            
            service = build('drive', 'v3', credentials=self.credentials)
            return service
            
        except Exception as e:
            logger.error(f"Erro ao criar serviço Drive: {e}")
            raise GoogleDriveException(f"Falha ao conectar com Drive: {e}")
    
    def get_docs_service(self):
        """
        Obtém serviço do Google Docs autenticado.
        
        Returns:
            Serviço do Google Docs
        """
        try:
            if not self.credentials:
                self._initialize_credentials()
            
            service = build('docs', 'v1', credentials=self.credentials)
            return service
            
        except Exception as e:
            logger.error(f"Erro ao criar serviço Docs: {e}")
            raise GoogleDriveException(f"Falha ao conectar com Docs: {e}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa conexão com Google Drive usando conta de serviço.
        
        Returns:
            Informações sobre a conexão
        """
        try:
            drive_service = self.get_drive_service()
            
            # Testa acesso básico listando arquivos (limitado)
            results = drive_service.files().list(
                pageSize=1,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            
            return {
                'authenticated': True,
                'service_account': {
                    'email': self.SERVICE_ACCOUNT_EMAIL,
                    'id': self.SERVICE_ACCOUNT_ID
                },
                'access_test': {
                    'can_list_files': True,
                    'sample_files_count': len(files)
                },
                'connection_time': datetime.now().isoformat(),
                'scopes': self.SCOPES
            }
            
        except HttpError as e:
            logger.error(f"Erro HTTP ao testar conexão: {e}")
            return {
                'authenticated': False,
                'error': f'HTTP Error: {e}',
                'error_code': e.resp.status if hasattr(e, 'resp') else None,
                'connection_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return {
                'authenticated': False,
                'error': str(e),
                'connection_time': datetime.now().isoformat()
            }
    
    def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """
        Obtém informações de um arquivo específico.
        
        Args:
            file_id: ID do arquivo no Google Drive
            
        Returns:
            Informações do arquivo
        """
        try:
            drive_service = self.get_drive_service()
            
            file_info = drive_service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,createdTime,modifiedTime,owners,permissions'
            ).execute()
            
            return {
                'success': True,
                'file': file_info,
                'accessible': True
            }
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Arquivo não encontrado: {file_id}")
                return {
                    'success': False,
                    'error': 'file_not_found',
                    'message': f'Arquivo {file_id} não encontrado'
                }
            elif e.resp.status == 403:
                logger.warning(f"Acesso negado ao arquivo: {file_id}")
                return {
                    'success': False,
                    'error': 'access_denied',
                    'message': f'Sem permissão para acessar arquivo {file_id}'
                }
            else:
                logger.error(f"Erro HTTP ao acessar arquivo {file_id}: {e}")
                return {
                    'success': False,
                    'error': 'http_error',
                    'message': f'Erro ao acessar arquivo: {e}'
                }
                
        except Exception as e:
            logger.error(f"Erro inesperado ao acessar arquivo {file_id}: {e}")
            return {
                'success': False,
                'error': 'unexpected_error',
                'message': str(e)
            }
    
    def list_files_in_folder(self, folder_id: str, page_size: int = 50) -> Dict[str, Any]:
        """
        Lista arquivos em uma pasta específica.
        
        Args:
            folder_id: ID da pasta no Google Drive
            page_size: Quantidade de arquivos por página
            
        Returns:
            Lista de arquivos na pasta
        """
        try:
            drive_service = self.get_drive_service()
            
            # Query para arquivos na pasta
            query = f"'{folder_id}' in parents and trashed=false"
            
            results = drive_service.files().list(
                q=query,
                pageSize=page_size,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, createdTime)"
            ).execute()
            
            files = results.get('files', [])
            next_page_token = results.get('nextPageToken')
            
            # Filtra apenas Google Docs
            google_docs = [
                f for f in files 
                if f.get('mimeType') == 'application/vnd.google-apps.document'
            ]
            
            return {
                'success': True,
                'folder_id': folder_id,
                'total_files': len(files),
                'google_docs_count': len(google_docs),
                'files': files,
                'google_docs': google_docs,
                'next_page_token': next_page_token,
                'has_more_pages': next_page_token is not None
            }
            
        except HttpError as e:
            logger.error(f"Erro HTTP ao listar pasta {folder_id}: {e}")
            return {
                'success': False,
                'error': 'http_error',
                'message': f'Erro ao acessar pasta: {e}'
            }
            
        except Exception as e:
            logger.error(f"Erro ao listar pasta {folder_id}: {e}")
            return {
                'success': False,
                'error': 'unexpected_error',
                'message': str(e)
            }
    
    def search_documents(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """
        Busca documentos no Google Drive.
        
        Args:
            query: Termo de busca
            max_results: Máximo de resultados
            
        Returns:
            Resultados da busca
        """
        try:
            drive_service = self.get_drive_service()
            
            # Query para buscar apenas Google Docs
            search_query = f"name contains '{query}' and mimeType='application/vnd.google-apps.document' and trashed=false"
            
            results = drive_service.files().list(
                q=search_query,
                pageSize=max_results,
                fields="files(id, name, mimeType, size, modifiedTime, createdTime, owners)"
            ).execute()
            
            files = results.get('files', [])
            
            return {
                'success': True,
                'query': query,
                'results_count': len(files),
                'max_results': max_results,
                'documents': files
            }
            
        except Exception as e:
            logger.error(f"Erro na busca de documentos: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def get_service_account_info(self) -> Dict[str, Any]:
        """
        Obtém informações da conta de serviço.
        
        Returns:
            Informações da conta de serviço
        """
        return {
            'email': self.SERVICE_ACCOUNT_EMAIL,
            'unique_id': self.SERVICE_ACCOUNT_ID,
            'scopes': self.SCOPES,
            'credentials_file': self.credentials_file,
            'authenticated': self.credentials is not None,
            'project_id': getattr(self.credentials, 'project_id', None) if self.credentials else None
        }
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """
        Cria uma pasta no Google Drive.
        
        Args:
            folder_name: Nome da pasta
            parent_folder_id: ID da pasta pai (opcional)
            
        Returns:
            ID da pasta criada
            
        Raises:
            GoogleDriveException: Se falhar ao criar pasta
        """
        try:
            drive_service = self.get_drive_service()
            
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]
            
            folder = drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Pasta criada com sucesso: {folder_name} (ID: {folder_id})")
            
            return folder_id
            
        except Exception as e:
            logger.error(f"Erro ao criar pasta {folder_name}: {e}")
            raise GoogleDriveException(f"Falha ao criar pasta: {e}")
    
    def copy_file(self, file_id: str, new_name: str, destination_folder_id: str = None) -> Dict[str, str]:
        """
        Copia um arquivo no Google Drive.
        
        Args:
            file_id: ID do arquivo a ser copiado
            new_name: Nome do novo arquivo
            destination_folder_id: ID da pasta de destino (opcional)
            
        Returns:
            Dicionário com id, name e webViewLink do arquivo copiado
            
        Raises:
            GoogleDriveException: Se falhar ao copiar arquivo
        """
        try:
            drive_service = self.get_drive_service()
            
            copy_metadata = {
                'name': new_name
            }
            
            if destination_folder_id:
                copy_metadata['parents'] = [destination_folder_id]
            
            copied_file = drive_service.files().copy(
                fileId=file_id,
                body=copy_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            logger.info(f"Arquivo copiado com sucesso: {new_name} (ID: {copied_file['id']})")
            
            return {
                'id': copied_file['id'],
                'name': copied_file['name'],
                'webViewLink': copied_file.get('webViewLink', '')
            }
            
        except Exception as e:
            logger.error(f"Erro ao copiar arquivo {file_id}: {e}")
            raise GoogleDriveException(f"Falha ao copiar arquivo: {e}")
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete um arquivo do Google Drive.
        
        Args:
            file_id: ID do arquivo a ser deletado
            
        Returns:
            True se deletado com sucesso
        """
        try:
            drive_service = self.get_drive_service()
            drive_service.files().delete(fileId=file_id).execute()
            logger.info(f"Arquivo deletado com sucesso: {file_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo {file_id}: {e}")
            return False


# Instância global do serviço
google_service_account = GoogleServiceAccountAuth()