"""
Serviço de autenticação OAuth 2.0 para Google Drive API.
Implementa autenticação segura e gerenciamento de tokens.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.utils.exceptions import (
    AuthenticationException,
    GoogleDriveException,
    ConfigurationException
)

logger = logging.getLogger(__name__)


class GoogleAuthService:
    """
    Serviço de autenticação para Google Drive API.
    
    Gerencia OAuth 2.0, tokens de acesso, refresh tokens e 
    integração segura com a API do Google Drive.
    """
    
    # Escopos necessários para o sistema
    SCOPES = [
        'https://www.googleapis.com/auth/drive.readonly',  # Leitura do Drive
        'https://www.googleapis.com/auth/documents.readonly',  # Leitura de Docs
        'https://www.googleapis.com/auth/drive.metadata.readonly'  # Metadados
    ]
    
    def __init__(self):
        """Inicializa o serviço de autenticação."""
        self.credentials_file = self._get_credentials_file()
        self.google_auth_available = self.credentials_file is not None
        
        if self.google_auth_available:
            self.token_dir = self._get_token_directory()
            self._ensure_token_directory()
        else:
            logger.info("Google Auth Service iniciado em modo limitado")
        
    def _get_credentials_file(self) -> str:
        """Obtém o caminho do arquivo de credenciais."""
        creds_file = os.environ.get('GOOGLE_CREDENTIALS_FILE')
        if not creds_file:
            # Fallback para arquivo padrão
            creds_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'client_secret.json'
            )
        
        if not os.path.exists(creds_file):
            logger.warning(f'Arquivo de credenciais não encontrado: {creds_file}')
            logger.warning('Sistema funcionará em modo limitado sem Google Drive')
            return None
        
        return creds_file
    
    def _get_token_directory(self) -> str:
        """Obtém o diretório para armazenamento de tokens."""
        token_dir = os.environ.get('GOOGLE_TOKEN_DIR', '/tmp/google_tokens')
        return token_dir
    
    def _ensure_token_directory(self):
        """Garante que o diretório de tokens existe."""
        Path(self.token_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_token_file_path(self, user_id: str) -> str:
        """Obtém o caminho do arquivo de token para um usuário."""
        return os.path.join(self.token_dir, f'token_{user_id}.json')
    
    def _load_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Carrega credenciais existentes para um usuário.
        
        Args:
            user_id: ID único do usuário
            
        Returns:
            Credenciais carregadas ou None se não existirem
        """
        token_file = self._get_token_file_path(user_id)
        
        if os.path.exists(token_file):
            try:
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
                logger.info(f"Credenciais carregadas para usuário {user_id}")
                return creds
            except Exception as e:
                logger.error(f"Erro ao carregar credenciais para {user_id}: {e}")
                # Remove arquivo corrompido
                os.remove(token_file)
        
        return None
    
    def _save_credentials(self, user_id: str, creds: Credentials):
        """
        Salva credenciais para um usuário.
        
        Args:
            user_id: ID único do usuário
            creds: Credenciais a serem salvas
        """
        token_file = self._get_token_file_path(user_id)
        
        try:
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"Credenciais salvas para usuário {user_id}")
        except Exception as e:
            logger.error(f"Erro ao salvar credenciais para {user_id}: {e}")
            raise GoogleDriveException(f"Falha ao salvar credenciais: {e}")
    
    def _refresh_credentials(self, creds: Credentials) -> bool:
        """
        Atualiza credenciais expiradas.
        
        Args:
            creds: Credenciais a serem atualizadas
            
        Returns:
            True se atualizadas com sucesso, False caso contrário
        """
        try:
            creds.refresh(Request())
            logger.info("Credenciais atualizadas com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar credenciais: {e}")
            return False
    
    def get_authorization_url(self, user_id: str, redirect_uri: str) -> str:
        """
        Gera URL de autorização para OAuth 2.0.
        
        Args:
            user_id: ID único do usuário
            redirect_uri: URI de callback após autorização
            
        Returns:
            URL de autorização do Google
        """
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            # Adiciona estado para segurança
            flow.flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                state=user_id,
                prompt='consent'  # Força nova aprovação para refresh token
            )
            
            auth_url, _ = flow.authorization_url()
            logger.info(f"URL de autorização gerada para usuário {user_id}")
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar URL de autorização: {e}")
            raise AuthenticationException(f"Falha na autorização: {e}")
    
    def handle_callback(self, user_id: str, authorization_code: str, redirect_uri: str) -> bool:
        """
        Processa callback do OAuth e obtém tokens.
        
        Args:
            user_id: ID único do usuário
            authorization_code: Código de autorização recebido
            redirect_uri: URI de callback usada na autorização
            
        Returns:
            True se autenticação bem-sucedida, False caso contrário
        """
        try:
            flow = Flow.from_client_secrets_file(
                self.credentials_file,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            # Troca código por tokens
            flow.fetch_token(code=authorization_code)
            creds = flow.credentials
            
            # Salva credenciais
            self._save_credentials(user_id, creds)
            
            logger.info(f"Autenticação concluída para usuário {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro no callback de autenticação: {e}")
            raise AuthenticationException(f"Falha no callback: {e}")
    
    def get_valid_credentials(self, user_id: str) -> Optional[Credentials]:
        """
        Obtém credenciais válidas para um usuário.
        
        Args:
            user_id: ID único do usuário
            
        Returns:
            Credenciais válidas ou None se não autenticado
        """
        creds = self._load_credentials(user_id)
        
        if not creds:
            logger.warning(f"Nenhuma credencial encontrada para usuário {user_id}")
            return None
        
        # Verifica se credenciais estão válidas
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                # Tenta renovar
                if self._refresh_credentials(creds):
                    self._save_credentials(user_id, creds)
                    return creds
                else:
                    logger.warning(f"Falha ao renovar credenciais para {user_id}")
                    return None
            else:
                logger.warning(f"Credenciais inválidas para usuário {user_id}")
                return None
        
        return creds
    
    def is_authenticated(self, user_id: str) -> bool:
        """
        Verifica se usuário está autenticado.
        
        Args:
            user_id: ID único do usuário
            
        Returns:
            True se autenticado, False caso contrário
        """
        return self.get_valid_credentials(user_id) is not None
    
    def revoke_access(self, user_id: str) -> bool:
        """
        Revoga acesso e remove credenciais armazenadas.
        
        Args:
            user_id: ID único do usuário
            
        Returns:
            True se revogação bem-sucedida, False caso contrário
        """
        try:
            creds = self._load_credentials(user_id)
            
            if creds:
                # Revoga token no Google
                creds.revoke(Request())
                logger.info(f"Token revogado no Google para usuário {user_id}")
            
            # Remove arquivo local
            token_file = self._get_token_file_path(user_id)
            if os.path.exists(token_file):
                os.remove(token_file)
                logger.info(f"Arquivo de token removido para usuário {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao revogar acesso para {user_id}: {e}")
            return False
    
    def get_drive_service(self, user_id: str):
        """
        Obtém serviço do Google Drive autenticado.
        
        Args:
            user_id: ID único do usuário
            
        Returns:
            Serviço do Google Drive
            
        Raises:
            AuthenticationException: Se usuário não autenticado
        """
        creds = self.get_valid_credentials(user_id)
        
        if not creds:
            raise AuthenticationException(
                f"Usuário {user_id} não autenticado"
            )
        
        try:
            service = build('drive', 'v3', credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Erro ao criar serviço Drive: {e}")
            raise GoogleDriveException(f"Falha ao conectar com Drive: {e}")
    
    def get_docs_service(self, user_id: str):
        """
        Obtém serviço do Google Docs autenticado.
        
        Args:
            user_id: ID único do usuário
            
        Returns:
            Serviço do Google Docs
            
        Raises:
            AuthenticationException: Se usuário não autenticado
        """
        creds = self.get_valid_credentials(user_id)
        
        if not creds:
            raise AuthenticationException(
                f"Usuário {user_id} não autenticado"
            )
        
        try:
            service = build('docs', 'v1', credentials=creds)
            return service
        except Exception as e:
            logger.error(f"Erro ao criar serviço Docs: {e}")
            raise GoogleDriveException(f"Falha ao conectar com Docs: {e}")
    
    def test_connection(self, user_id: str) -> Dict[str, Any]:
        """
        Testa conexão com Google Drive.
        
        Args:
            user_id: ID único do usuário
            
        Returns:
            Informações sobre a conexão e usuário
        """
        try:
            drive_service = self.get_drive_service(user_id)
            
            # Obtém informações do usuário
            about = drive_service.about().get(fields='user,storageQuota').execute()
            
            user_info = about.get('user', {})
            quota_info = about.get('storageQuota', {})
            
            return {
                'authenticated': True,
                'user': {
                    'name': user_info.get('displayName'),
                    'email': user_info.get('emailAddress'),
                    'photo': user_info.get('photoLink')
                },
                'storage': {
                    'limit': quota_info.get('limit'),
                    'usage': quota_info.get('usage'),
                    'usageInDrive': quota_info.get('usageInDrive')
                },
                'connection_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return {
                'authenticated': False,
                'error': str(e),
                'connection_time': datetime.now().isoformat()
            }
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        Obtém informações básicas do usuário Google.
        
        Args:
            user_id: ID único do usuário
            
        Returns:
            Informações do usuário ou None se erro
        """
        try:
            connection_info = self.test_connection(user_id)
            
            if connection_info.get('authenticated'):
                return connection_info.get('user')
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do usuário: {e}")
            return None


# Instância global do serviço
google_auth_service = GoogleAuthService()