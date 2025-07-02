#!/usr/bin/env python3
"""
Serviço híbrido para Google Drive - OAuth + Service Account
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.services.google_service_account import GoogleServiceAccountAuth
from app.utils.exceptions import GoogleDriveException

logger = logging.getLogger(__name__)


class HybridGoogleService:
    """
    Serviço híbrido que usa OAuth quando disponível, 
    com fallback para conta de serviço.
    """
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/documents'
    ]
    
    def __init__(self):
        """Inicializa serviço híbrido."""
        self.oauth_available = False
        self.service_account_available = False
        self.active_service = None
        
        # Verificar OAuth
        self.credentials_file = self._find_credentials_file()
        self.token_file = self._find_token_file()
        
        if self.credentials_file:
            logger.info("✅ Credenciais OAuth encontradas")
            self.oauth_available = True
        
        # Verificar Service Account
        try:
            self.service_account = GoogleServiceAccountAuth()
            self.service_account_available = True
            logger.info("✅ Service Account disponível")
        except Exception as e:
            logger.warning(f"Service Account não disponível: {e}")
        
        # Determinar serviço ativo
        self._determine_active_service()
    
    def _find_credentials_file(self) -> Optional[str]:
        """Busca arquivo de credenciais OAuth."""
        possible_paths = [
            '/home/app/client_secret.json',
            'client_secret.json',
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'client_secret.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Credenciais OAuth encontradas: {path}")
                return path
        
        return None
    
    def _find_token_file(self) -> Optional[str]:
        """Busca arquivo de tokens OAuth."""
        possible_paths = [
            '/home/app/token.json',
            'token.json',
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'token.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Token OAuth encontrado: {path}")
                return path
        
        return None
    
    def _determine_active_service(self):
        """Determina qual serviço usar com base na disponibilidade."""
        if self.oauth_available and self._has_valid_oauth_token():
            self.active_service = 'oauth'
            logger.info("🔐 Usando autenticação OAuth")
        elif self.service_account_available:
            self.active_service = 'service_account'
            logger.info("🤖 Usando Service Account")
        else:
            self.active_service = None
            logger.error("❌ Nenhum método de autenticação disponível")
    
    def _has_valid_oauth_token(self) -> bool:
        """Verifica se tem token OAuth válido."""
        if not self.token_file:
            return False
        
        try:
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            return creds and creds.valid
        except:
            return False
    
    def _get_oauth_credentials(self) -> Optional[Credentials]:
        """Obtém credenciais OAuth válidas."""
        if not self.credentials_file:
            return None
        
        creds = None
        
        # Carregar token existente
        if self.token_file:
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            except Exception as e:
                logger.warning(f"Erro ao carregar token: {e}")
        
        # Renovar se expirado
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_token(creds)
                logger.info("✅ Token OAuth renovado")
            except Exception as e:
                logger.error(f"Erro ao renovar token: {e}")
                return None
        
        return creds if creds and creds.valid else None
    
    def _save_token(self, creds: Credentials):
        """Salva token OAuth."""
        token_path = self.token_file or '/home/app/token.json'
        
        try:
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
            logger.info("✅ Token OAuth salvo")
        except Exception as e:
            logger.error(f"Erro ao salvar token: {e}")
    
    def initialize_oauth(self) -> str:
        """
        Inicializa OAuth e retorna URL de autorização.
        
        Returns:
            URL de autorização ou string vazia se erro
        """
        if not self.credentials_file:
            logger.error("Arquivo de credenciais OAuth não encontrado")
            return ""
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.SCOPES)
            
            # Executar fluxo local (requer interação do usuário)
            creds = flow.run_local_server(
                port=8080,
                prompt='consent',
                authorization_prompt_message='Abrindo navegador para autenticação...',
                success_message='Autenticação concluída!'
            )
            
            # Salvar token
            self._save_token(creds)
            
            # Atualizar status
            self.token_file = '/home/app/token.json'
            self.active_service = 'oauth'
            
            logger.info("🎉 OAuth configurado com sucesso!")
            return "success"
            
        except Exception as e:
            logger.error(f"Erro no fluxo OAuth: {e}")
            return f"error: {e}"
    
    def get_drive_service(self):
        """Obtém serviço do Google Drive usando método ativo."""
        if self.active_service == 'oauth':
            creds = self._get_oauth_credentials()
            if creds:
                return build('drive', 'v3', credentials=creds)
            else:
                logger.warning("OAuth falhou, tentando Service Account...")
                self.active_service = 'service_account'
        
        if self.active_service == 'service_account' and self.service_account_available:
            return self.service_account.get_drive_service()
        
        raise GoogleDriveException("Nenhum método de autenticação disponível")
    
    def get_docs_service(self):
        """Obtém serviço do Google Docs usando método ativo."""
        if self.active_service == 'oauth':
            creds = self._get_oauth_credentials()
            if creds:
                return build('docs', 'v1', credentials=creds)
            else:
                logger.warning("OAuth falhou, tentando Service Account...")
                self.active_service = 'service_account'
        
        if self.active_service == 'service_account' and self.service_account_available:
            return self.service_account.get_docs_service()
        
        raise GoogleDriveException("Nenhum método de autenticação disponível")
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """Cria pasta usando serviço ativo."""
        if self.active_service == 'service_account' and self.service_account_available:
            return self.service_account.create_folder(folder_name, parent_folder_id)
        
        raise GoogleDriveException("Nenhum método de autenticação disponível para criar pasta")
    
    def copy_file(self, file_id: str, new_name: str, destination_folder_id: str = None) -> Dict[str, str]:
        """Copia arquivo usando serviço ativo."""
        if self.active_service == 'service_account' and self.service_account_available:
            return self.service_account.copy_file(file_id, new_name, destination_folder_id)
        
        raise GoogleDriveException("Nenhum método de autenticação disponível para copiar arquivo")
    
    def list_files(self, query: str = None, max_results: int = 10) -> List[Dict[str, Any]]:
        """Lista arquivos usando serviço ativo."""
        try:
            drive_service = self.get_drive_service()
            
            kwargs = {
                'pageSize': max_results,
                'fields': 'files(id, name, mimeType, webViewLink)'
            }
            
            if query:
                kwargs['q'] = query
            
            results = drive_service.files().list(**kwargs).execute()
            
            files = results.get('files', [])
            logger.info(f"✅ {len(files)} arquivo(s) listado(s) via {self.active_service}")
            
            return files
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos: {e}")
            raise GoogleDriveException(f"Falha ao listar arquivos: {e}")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o serviço ativo."""
        return {
            'active_service': self.active_service,
            'oauth_available': self.oauth_available,
            'service_account_available': self.service_account_available,
            'credentials_file': self.credentials_file,
            'token_file': self.token_file,
            'has_valid_oauth': self._has_valid_oauth_token()
        } 