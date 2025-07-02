"""
Enhanced Google Drive Adapter - Advanced integration with Google Drive API.

Provides enhanced functionality for document organization, batch operations,
image handling, and folder management with retry mechanisms.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
import re
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
import io

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
except ImportError:
    # Fallback for development/testing
    logging.warning("Google API client not available - using mock implementation")

from app.utils.exceptions import (
    GoogleDriveException,
    IntegrationException,
    ValidationException
)
from app.config.constants import GOOGLE_DRIVE_CONFIG


logger = logging.getLogger(__name__)


class EnhancedGoogleDriveAdapter:
    """
    Enhanced adapter for Google Drive operations.
    
    Provides:
    - Advanced folder organization
    - Batch document operations
    - Image insertion capabilities
    - Retry mechanisms with circuit breaker
    - Comprehensive error handling
    """
    
    # Google Drive folder structure
    TEMPLATES_FOLDER_ID = "1LvPsvml7bkN2TQjyAqnNAYAy7qRebrDf"
    CLIENTS_ROOT_FOLDER_ID = None  # Will be set during initialization
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/documents'
        ]
        self.retry_attempts = 3
        self.retry_delay = 2  # seconds
        self.circuit_breaker = {
            'failures': 0,
            'last_failure': None,
            'threshold': 5,
            'timeout': 300  # 5 minutes
        }
        
        self._initialize_service()
    
    def authenticate(self) -> bool:
        """
        Authenticates with Google Drive API.
        
        Returns:
            True if authentication successful
            
        Raises:
            GoogleDriveException: If authentication fails
        """
        logger.info("Authenticating with Google Drive API")
        
        try:
            service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON') or \
                '/home/app/app-script-459322-990ad4e6c8ea.json'

            if service_account_json and os.path.exists(service_account_json):
                # ---- Conta de serviço ----
                from google.oauth2 import service_account as sa
                creds = sa.Credentials.from_service_account_file(service_account_json, scopes=self.scopes)
                self.credentials = creds
                self.service = build('drive', 'v3', credentials=creds)
                # Test connection
                self.service.about().get(fields="user").execute()
                logger.info('Autenticado via Service Account')
                return True
            else:
                raise GoogleDriveException(f'Service account file not found: {service_account_json}')
            
        except Exception as e:
            logger.error(f"Google Drive authentication failed: {str(e)}")
            raise GoogleDriveException(f"Authentication failed: {str(e)}")
    
    def organize_by_client(self, client_name: str, client_cpf: str = None) -> str:
        """
        Creates or locates client folder with standardized naming.
        
        Format: [AAAA]-Nome Sobrenome ou [AAAA]-Razão Social
        
        Args:
            client_name: Name of the client
            client_cpf: Optional CPF for disambiguation
            
        Returns:
            Google Drive folder ID
            
        Raises:
            GoogleDriveException: If folder operations fail
        """
        logger.info(f"Organizing folder for client: {client_name}")
        
        try:
            # Generate standardized folder name
            current_date = datetime.now()
            year = current_date.strftime("%Y")
            sanitized_name = self._sanitize_folder_name(client_name)
            folder_name = f"[{year}]-{sanitized_name}"
            
            # Get or create clients root folder
            clients_root = self._get_or_create_clients_root()
            
            # Check if folder already exists
            existing_folder = self._find_folder_by_name(folder_name, clients_root)
            if existing_folder:
                logger.info(f"Using existing client folder: {folder_name}")
                return existing_folder['id']
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'parents': [clients_root],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self._execute_with_retry(
                lambda: self.service.files().create(body=folder_metadata, fields='id').execute()
            )
            
            logger.info(f"Created client folder: {folder_name} (ID: {folder['id']})")
            
            # Create subfolders for document types
            self._create_document_type_subfolders(folder['id'])
            
            return folder['id']
            
        except Exception as e:
            logger.error(f"Error organizing client folder: {str(e)}")
            raise GoogleDriveException(f"Failed to organize client folder: {str(e)}")
    
    def organize_by_document_type(self, client_folder_id: str, doc_type: str) -> str:
        """
        Creates or locates document type subfolder.
        
        Args:
            client_folder_id: Parent client folder ID
            doc_type: Type of document
            
        Returns:
            Document type subfolder ID
        """
        logger.debug(f"Organizing document type folder: {doc_type}")
        
        try:
            sanitized_type = self._sanitize_folder_name(doc_type)
            
            # Check if subfolder exists
            existing_folder = self._find_folder_by_name(sanitized_type, client_folder_id)
            if existing_folder:
                return existing_folder['id']
            
            # Create subfolder
            folder_metadata = {
                'name': sanitized_type,
                'parents': [client_folder_id],
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = self._execute_with_retry(
                lambda: self.service.files().create(body=folder_metadata, fields='id').execute()
            )
            
            logger.debug(f"Created document type folder: {sanitized_type}")
            return folder['id']
            
        except Exception as e:
            logger.error(f"Error creating document type folder: {str(e)}")
            raise GoogleDriveException(f"Failed to create document type folder: {str(e)}")
    
    def batch_create_documents(self, templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Creates multiple documents in batch with retry and error handling.
        
        Args:
            templates: List of template dictionaries with copy operations
            
        Returns:
            List of results with success/failure status
        """
        logger.info(f"Batch creating {len(templates)} documents")
        
        results = []
        successful = 0
        failed = 0
        
        for i, template_data in enumerate(templates):
            try:
                logger.debug(f"Processing template {i+1}/{len(templates)}")
                
                # Extract required data
                template_id = template_data['template_id']
                target_folder = template_data.get('target_folder')
                new_name = template_data.get('new_name', f"Document_{i+1}")
                
                # Copy document
                document_id = self.copy_document(
                    template_id, 
                    new_name, 
                    target_folder
                )
                
                results.append({
                    'index': i,
                    'success': True,
                    'document_id': document_id,
                    'name': new_name
                })
                
                successful += 1
                
                # Add small delay to avoid rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error creating document {i+1}: {str(e)}")
                results.append({
                    'index': i,
                    'success': False,
                    'error': str(e),
                    'name': template_data.get('new_name', f"Document_{i+1}")
                })
                failed += 1
        
        logger.info(f"Batch operation completed: {successful} successful, {failed} failed")
        return results
    
    def create_document_with_images(self, template_id: str, data: Dict[str, Any], 
                                  images: Dict[str, str]) -> str:
        """
        Creates document and inserts images at specified placeholders.
        
        Args:
            template_id: ID of template document
            data: Data to fill placeholders
            images: Dict mapping placeholder names to image file paths
            
        Returns:
            ID of created document
        """
        logger.info(f"Creating document with images from template {template_id}")
        
        try:
            # First copy the document
            document_id = self.copy_document(template_id, data.get('document_name', 'New Document'))
            
            # Fill text placeholders
            self.fill_placeholders(document_id, data)
            
            # Insert images
            for placeholder, image_path in images.items():
                if os.path.exists(image_path):
                    self._insert_image_at_placeholder(document_id, placeholder, image_path)
                else:
                    logger.warning(f"Image not found: {image_path}")
            
            logger.info(f"Document created with images: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error creating document with images: {str(e)}")
            raise GoogleDriveException(f"Failed to create document with images: {str(e)}")
    
    def copy_document(self, template_id: str, new_name: str, target_folder: str = None) -> str:
        """
        Copies a Google Doc template.
        
        Args:
            template_id: ID of template document
            new_name: Name for the new document
            target_folder: Optional target folder ID
            
        Returns:
            ID of copied document
        """
        try:
            copy_metadata = {'name': new_name}
            if target_folder:
                copy_metadata['parents'] = [target_folder]
            
            copied_file = self._execute_with_retry(
                lambda: self.service.files().copy(
                    fileId=template_id,
                    body=copy_metadata,
                    fields='id,name,webViewLink'
                ).execute()
            )
            
            logger.info(f"Document copied: {new_name} (ID: {copied_file['id']})")
            return copied_file['id']
            
        except Exception as e:
            logger.error(f"Error copying document: {str(e)}")
            raise GoogleDriveException(f"Failed to copy document: {str(e)}")
    
    def fill_placeholders(self, document_id: str, data: Dict[str, Any]) -> bool:
        """
        Fills placeholders in Google Doc.
        
        Args:
            document_id: ID of document to update
            data: Data to fill placeholders
            
        Returns:
            True if successful
        """
        try:
            # Build requests for batch update
            requests = []
            
            for key, value in data.items():
                if value is not None:
                    placeholder = f"{{{{{key}}}}}"
                    requests.append({
                        'replaceAllText': {
                            'containsText': {
                                'text': placeholder,
                                'matchCase': False
                            },
                            'replaceText': str(value)
                        }
                    })
            
            if requests:
                # Use Google Docs API for text replacement
                docs_service = build('docs', 'v1', credentials=self.credentials)
                
                self._execute_with_retry(
                    lambda: docs_service.documents().batchUpdate(
                        documentId=document_id,
                        body={'requests': requests}
                    ).execute()
                )
                
                logger.info(f"Filled {len(requests)} placeholders in document {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error filling placeholders: {str(e)}")
            raise GoogleDriveException(f"Failed to fill placeholders: {str(e)}")
    
    def extract_placeholders(self, document_id: str) -> List[Dict[str, Any]]:
        """
        Extracts placeholders from Google Doc.
        
        Args:
            document_id: ID of document to analyze
            
        Returns:
            List of placeholder dictionaries
        """
        try:
            docs_service = build('docs', 'v1', credentials=self.credentials)
            document = docs_service.documents().get(documentId=document_id).execute()
            
            content = document.get('body', {}).get('content', [])
            placeholders = []
            
            # Extract text and find placeholder patterns
            text_content = self._extract_text_from_content(content)
            placeholder_matches = re.findall(r'\{\{([^}]+)\}\}', text_content)
            
            for match in placeholder_matches:
                placeholders.append({
                    'chave': match,
                    'tipo': self._infer_placeholder_type(match),
                    'obrigatorio': self._is_required_placeholder(match),
                    'descricao': self._generate_placeholder_description(match)
                })
            
            # Remove duplicates
            unique_placeholders = []
            seen_keys = set()
            for p in placeholders:
                if p['chave'] not in seen_keys:
                    unique_placeholders.append(p)
                    seen_keys.add(p['chave'])
            
            logger.info(f"Extracted {len(unique_placeholders)} unique placeholders")
            return unique_placeholders
            
        except Exception as e:
            logger.error(f"Error extracting placeholders: {str(e)}")
            raise GoogleDriveException(f"Failed to extract placeholders: {str(e)}")
    
    def document_exists(self, document_id: str) -> bool:
        """
        Checks if document exists and is accessible.
        
        Args:
            document_id: ID of document to check
            
        Returns:
            True if document exists and is accessible
        """
        try:
            self._execute_with_retry(
                lambda: self.service.files().get(fileId=document_id, fields='id').execute()
            )
            return True
        except Exception:
            return False
    
    def get_folder_structure(self, folder_id: str) -> Dict[str, Any]:
        """
        Gets complete folder structure for organization analysis.
        
        Args:
            folder_id: Root folder ID
            
        Returns:
            Dict with folder structure information
        """
        try:
            def get_folder_contents(fid, path=""):
                query = f"'{fid}' in parents and trashed=false"
                results = self.service.files().list(
                    q=query,
                    fields="files(id, name, mimeType, createdTime)"
                ).execute()
                
                contents = {'folders': [], 'files': [], 'path': path}
                
                for item in results.get('files', []):
                    if item['mimeType'] == 'application/vnd.google-apps.folder':
                        subfolder = get_folder_contents(
                            item['id'], 
                            f"{path}/{item['name']}" if path else item['name']
                        )
                        contents['folders'].append({
                            'id': item['id'],
                            'name': item['name'],
                            'contents': subfolder
                        })
                    else:
                        contents['files'].append({
                            'id': item['id'],
                            'name': item['name'],
                            'mimeType': item['mimeType'],
                            'createdTime': item['createdTime']
                        })
                
                return contents
            
            structure = get_folder_contents(folder_id)
            logger.info(f"Retrieved folder structure for {folder_id}")
            return structure
            
        except Exception as e:
            logger.error(f"Error getting folder structure: {str(e)}")
            raise GoogleDriveException(f"Failed to get folder structure: {str(e)}")
    
    def _initialize_service(self) -> None:
        """Initializes Google Drive service."""
        try:
            self.authenticate()
            self._reset_circuit_breaker()
        except Exception as e:
            logger.warning(f"Failed to initialize Google Drive service: {str(e)}")
    
    def _execute_with_retry(self, operation, max_retries: int = None) -> Any:
        """Executes operation with retry logic and circuit breaker."""
        if self._is_circuit_breaker_open():
            raise GoogleDriveException("Circuit breaker is open - too many recent failures")
        
        max_retries = max_retries or self.retry_attempts
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                result = operation()
                self._reset_circuit_breaker()
                return result
                
            except HttpError as e:
                last_exception = e
                if e.resp.status in [403, 429]:  # Rate limiting or quota exceeded
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                elif e.resp.status in [500, 502, 503, 504]:  # Server errors
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Server error, retrying in {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                else:
                    break  # Don't retry for client errors
                    
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Operation failed, retrying in {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
        
        # All retries failed
        self._record_circuit_breaker_failure()
        raise GoogleDriveException(f"Operation failed after {max_retries} attempts: {str(last_exception)}")
    
    def _is_circuit_breaker_open(self) -> bool:
        """Checks if circuit breaker is open."""
        if self.circuit_breaker['failures'] >= self.circuit_breaker['threshold']:
            if self.circuit_breaker['last_failure']:
                time_since_failure = datetime.now() - self.circuit_breaker['last_failure']
                if time_since_failure.total_seconds() < self.circuit_breaker['timeout']:
                    return True
                else:
                    # Reset circuit breaker after timeout
                    self._reset_circuit_breaker()
        return False
    
    def _record_circuit_breaker_failure(self) -> None:
        """Records a failure for circuit breaker logic."""
        self.circuit_breaker['failures'] += 1
        self.circuit_breaker['last_failure'] = datetime.now()
    
    def _reset_circuit_breaker(self) -> None:
        """Resets circuit breaker after successful operation."""
        self.circuit_breaker['failures'] = 0
        self.circuit_breaker['last_failure'] = None
    
    def _get_or_create_clients_root(self) -> str:
        """Gets or creates the root folder for clients."""
        from app.config.constants import GOOGLE_DRIVE_CONFIG
        
        # Use the configured folder ID if available
        configured_folder_id = GOOGLE_DRIVE_CONFIG.get('CLIENT_FOLDERS_ROOT_ID')
        if configured_folder_id:
            # Verify the folder exists and is accessible
            try:
                folder = self.service.files().get(fileId=configured_folder_id).execute()
                logger.info(f"Using configured clients root folder: {configured_folder_id}")
                self.CLIENTS_ROOT_FOLDER_ID = configured_folder_id
                return self.CLIENTS_ROOT_FOLDER_ID
            except Exception as e:
                logger.warning(f"Configured folder {configured_folder_id} not accessible: {str(e)}")
        
        if self.CLIENTS_ROOT_FOLDER_ID:
            return self.CLIENTS_ROOT_FOLDER_ID
        
        # Look for existing "Clientes" folder
        query = "name='Clientes' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        
        files = results.get('files', [])
        if files:
            self.CLIENTS_ROOT_FOLDER_ID = files[0]['id']
            return self.CLIENTS_ROOT_FOLDER_ID
        
        # Create "Clientes" folder
        folder_metadata = {
            'name': 'Clientes',
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
        self.CLIENTS_ROOT_FOLDER_ID = folder['id']
        
        logger.info(f"Created Clientes root folder: {self.CLIENTS_ROOT_FOLDER_ID}")
        return self.CLIENTS_ROOT_FOLDER_ID
    
    def _find_folder_by_name(self, name: str, parent_id: str) -> Optional[Dict[str, Any]]:
        """Finds folder by name within parent folder."""
        query = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        
        files = results.get('files', [])
        return files[0] if files else None
    
    def _create_document_type_subfolders(self, client_folder_id: str) -> None:
        """Creates standard document type subfolders."""
        standard_folders = [
            "Fichas Cadastrais",
            "Defesas e Recursos", 
            "Termos de Acordo",
            "Ações Anulatórias",
            "Outros Documentos"
        ]
        
        for folder_name in standard_folders:
            try:
                existing = self._find_folder_by_name(folder_name, client_folder_id)
                if not existing:
                    folder_metadata = {
                        'name': folder_name,
                        'parents': [client_folder_id],
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    self.service.files().create(body=folder_metadata).execute()
            except Exception as e:
                logger.warning(f"Failed to create subfolder {folder_name}: {str(e)}")
    
    def _sanitize_folder_name(self, name: str) -> str:
        """Sanitizes folder name for Google Drive."""
        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized[:100]  # Limit length
    
    def _insert_image_at_placeholder(self, document_id: str, placeholder: str, image_path: str) -> None:
        """Inserts image at placeholder location in document."""
        # This would require more complex Google Docs API operations
        # For now, just log the operation
        logger.info(f"Would insert image {image_path} at placeholder {placeholder} in document {document_id}")
    
    def _extract_text_from_content(self, content: List[Dict[str, Any]]) -> str:
        """Extracts text content from Google Docs structure."""
        text_parts = []
        
        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_element in paragraph.get('elements', []):
                    if 'textRun' in text_element:
                        text_parts.append(text_element['textRun'].get('content', ''))
        
        return ''.join(text_parts)
    
    def _infer_placeholder_type(self, placeholder_key: str) -> str:
        """Infers placeholder type from key name."""
        key_lower = placeholder_key.lower()
        
        if 'email' in key_lower:
            return 'email'
        elif any(word in key_lower for word in ['cpf', 'cnpj', 'telefone', 'phone']):
            return 'text'
        elif any(word in key_lower for word in ['data', 'date']):
            return 'date'
        elif any(word in key_lower for word in ['valor', 'price', 'money']):
            return 'currency'
        elif 'endereco' in key_lower or 'address' in key_lower:
            return 'text'
        else:
            return 'text'
    
    def _is_required_placeholder(self, placeholder_key: str) -> bool:
        """Determines if placeholder should be required."""
        required_patterns = ['nome', 'cpf', 'cnpj', 'autor_1_', 'autoridade_1_']
        return any(pattern in placeholder_key.lower() for pattern in required_patterns)
    
    def _generate_placeholder_description(self, placeholder_key: str) -> str:
        """Generates description for placeholder."""
        descriptions = {
            'nome': 'Nome completo',
            'cpf': 'CPF (apenas números)',
            'cnpj': 'CNPJ (apenas números)',
            'telefone': 'Telefone com DDD',
            'email': 'Endereço de email',
            'endereco': 'Endereço completo',
            'data': 'Data no formato DD/MM/AAAA'
        }
        
        key_lower = placeholder_key.lower()
        for pattern, description in descriptions.items():
            if pattern in key_lower:
                return description
        
        return f"Campo: {placeholder_key}" 