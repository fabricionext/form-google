import os

from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]

SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

if not SERVICE_ACCOUNT_FILE or not os.path.exists(SERVICE_ACCOUNT_FILE):
    raise Exception(
        "Arquivo de credenciais da Service Account não encontrado. Configure GOOGLE_SERVICE_ACCOUNT_JSON no .env"
    )

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)


def get_sheets_service():
    return build("sheets", "v4", credentials=credentials)


def get_drive_service():
    return build("drive", "v3", credentials=credentials)


def get_docs_service():
    return build("docs", "v1", credentials=credentials)
