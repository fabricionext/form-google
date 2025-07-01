import logging
from flask import current_app
from googleapiclient.discovery import build
from ...utils.google_auth import get_google_credentials

logger = logging.getLogger(__name__)


class GoogleDriveService:
    def __init__(self):
        try:
            self.creds = get_google_credentials()
            self.service = build("drive", "v3", credentials=self.creds)
        except Exception as e:
            logger.error(f"Erro ao inicializar GoogleDriveService: {e}", exc_info=True)
            raise

    def copy_file(self, file_id: str, new_name: str, destination_folder_id: str):
        pass 