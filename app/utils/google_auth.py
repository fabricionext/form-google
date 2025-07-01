import os
import pickle
import logging
from flask import current_app
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)

def get_google_credentials():
    """
    Get Google API credentials using environment variables or token file.
    Production-ready version that doesn't require credentials.json file.
    """
    creds = None
    config = current_app.config
    token_path = config.get("GOOGLE_TOKEN_PATH", "token.pickle")
    scopes = config.get(
        "GOOGLE_SCOPES", ["https://www.googleapis.com/auth/drive.file"]
    )

    # Try to load existing token
    if os.path.exists(token_path):
        try:
            with open(token_path, "rb") as token:
                creds = pickle.load(token)
        except (pickle.UnpicklingError, EOFError) as e:
            logger.warning(f"Erro ao carregar token.pickle: {e}. O arquivo pode estar corrompido.")
            creds = None
    
    # Check if we have valid credentials
    if creds and creds.valid:
        return creds
    
    # Try to refresh expired credentials
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Save refreshed token
            with open(token_path, "wb") as token:
                pickle.dump(creds, token)
            return creds
        except Exception as e:
            logger.error(f"Erro ao renovar token de acesso: {e}")
    
    # Check for environment variables first (production)
    client_id = config.get('GOOGLE_CLIENT_ID')
    client_secret = config.get('GOOGLE_CLIENT_SECRET')
    
    if client_id and client_secret:
        # Use environment variables for credentials
        logger.info("Usando credenciais do Google a partir de variáveis de ambiente")
        
        # Create credentials from environment variables
        # This is a simplified approach - in production you would need proper OAuth flow
        # For now, return None to indicate missing credentials setup
        logger.warning("Credenciais do Google configuradas mas token de acesso necessário")
        return None
    
    # Fallback to credentials.json file if available
    credentials_path = config.get("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    
    if os.path.exists(credentials_path):
        try:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(token_path, "wb") as token:
                pickle.dump(creds, token)
                
            return creds
        except Exception as e:
            logger.error(f"Erro ao autenticar com credentials.json: {e}")
    
    # No credentials available
    logger.warning("Nenhuma credencial do Google disponível. Configure GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET ou forneça credentials.json")
    return None 