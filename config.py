import json  # Adicionado para carregar o JSON
import logging  # Adicionado para logar erros de carregamento
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# Permite logs de depuração extensos apenas quando DEBUG_CONFIG=1
DEBUG_CONFIG = os.getenv("DEBUG_CONFIG") == "1"

if DEBUG_CONFIG:
    logger.debug("=" * 50)
    logger.debug("[CONFIG_DEBUG_ENV] INICIANDO config.py")
    logger.debug("[CONFIG_DEBUG_ENV] CONTEÚDO COMPLETO DE os.environ:")
    for key, value in os.environ.items():
        logger.debug("[CONFIG_DEBUG_ENV]   %s = %s", key, value)
    logger.debug("=" * 50)

def _load_templates_from_db(db_uri: str) -> dict:
    """Retorna dicionário de templates armazenados no banco de dados."""
    templates: dict[str, dict[str, str]] = {}
    try:
        engine = create_engine(db_uri)
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT tipo_pessoa, nome, template_id FROM document_templates")
            )
            for tipo, nome, t_id in result:
                templates.setdefault(tipo, {})[nome] = t_id
    except Exception as exc:
        logger.error("Erro ao carregar templates do banco: %s", exc)
    return templates

# Carregar credenciais do Google como string JSON
GOOGLE_SERVICE_ACCOUNT_JSON_PATH = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
GOOGLE_CREDENTIALS_AS_JSON_STR = None
path_exists = (
    os.path.exists(GOOGLE_SERVICE_ACCOUNT_JSON_PATH)
    if GOOGLE_SERVICE_ACCOUNT_JSON_PATH
    else False
)
if GOOGLE_SERVICE_ACCOUNT_JSON_PATH and path_exists:
    try:
        with open(GOOGLE_SERVICE_ACCOUNT_JSON_PATH, "r") as f:
            # Carrega o JSON do arquivo e o converte de volta para uma string JSON compacta
            # Isso garante que temos uma string JSON válida e não um objeto Python dict
            loaded_json = json.load(f)
            GOOGLE_CREDENTIALS_AS_JSON_STR = json.dumps(loaded_json)
        logger.info(
            f"Credenciais Google carregadas com sucesso de {GOOGLE_SERVICE_ACCOUNT_JSON_PATH}"
        )
    except Exception as e:
        logger.error(
            f"Erro ao carregar ou processar o arquivo de credenciais JSON do Google ({GOOGLE_SERVICE_ACCOUNT_JSON_PATH}): {e}",
            exc_info=True,
        )
        # GOOGLE_CREDENTIALS_AS_JSON_STR permanecerá None, o que deve ser tratado na aplicação
elif GOOGLE_SERVICE_ACCOUNT_JSON_PATH:
    logger.warning(
        "Arquivo de credenciais JSON do Google especificado (%s) não encontrado.",
        GOOGLE_SERVICE_ACCOUNT_JSON_PATH,
    )
else:
    logger.warning("Variável de ambiente GOOGLE_SERVICE_ACCOUNT_JSON não definida.")

DB_URI = os.getenv(
    "SQLALCHEMY_DATABASE_URI",
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}",
)
TEMPLATES_FROM_DB = _load_templates_from_db(DB_URI)

# Configurações principais do sistema
CONFIG = {
    # Configuração do banco de dados
    "SQLALCHEMY_DATABASE_URI": DB_URI,
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    # Configuração de segurança
    "SECRET_KEY": os.getenv("SECRET_KEY")
    or os.getenv("FLASK_SECRET_KEY", "chave-secreta-padrao-mude-isso-em-producao"),
    "WTF_CSRF_SECRET_KEY": os.getenv("SECRET_KEY")
    or os.getenv("FLASK_SECRET_KEY", "chave-secreta-padrao-mude-isso-em-producao"),
    "WTF_CSRF_ENABLED": True,
    # IDs e nomes essenciais
    "SPREADSHEET_ID": os.getenv("SPREADSHEET_ID"),
    "PARENT_FOLDER_ID": os.getenv("PARENT_FOLDER_ID"),
    "SHEET_NAME": os.getenv("SHEET_NAME", "Respostas"),
    "LOG_SHEET_NAME": os.getenv("LOG_SHEET_NAME", "LOG_Processamento"),
    "GOOGLE_CREDENTIALS_AS_JSON_STR": GOOGLE_CREDENTIALS_AS_JSON_STR,  # Adicionada a string JSON das credenciais
    "ADMIN_EMAIL": os.getenv("ADMIN_EMAIL"),
    "BACKUP_FOLDER_ID": os.getenv("BACKUP_FOLDER_ID"),
    "INTERNAL_API_KEY": os.getenv("INTERNAL_API_KEY"),
    # Templates
    "TEMPLATES": TEMPLATES_FROM_DB,
    # Subpastas
    "FOLDER_FOR_CLIENT_ANNEXES": os.getenv(
        "FOLDER_FOR_CLIENT_ANNEXES", "Anexos Cliente"
    ),
    "FOLDER_FOR_GENERATED_PDFS": os.getenv(
        "FOLDER_FOR_GENERATED_PDFS", "Documentos PDF"
    ),
    # Cabeçalhos da planilha
    "SHEET_HEADERS": [
        "Timestamp Processamento",
        "Submission ID",
        "Tipo Pessoa",
        "Primeiro Nome",
        "Sobrenome",
        "CPF",
        "Data de Nascimento",
        "RG",
        "Estado Emissor RG",
        "Nacionalidade",
        "Estado Civil",
        "Profissão",
        "CNH",
        "Razão Social",
        "CNPJ",
        "Nome Representante Legal",
        "CPF Representante Legal",
        "Cargo Representante Legal",
        "CEP",
        "Endereço",
        "Complemento",
        "Bairro",
        "Cidade",
        "UF Endereço",
        "Telefone Celular",
        "Outro Telefone",
        "E-mail",
        "Nome Cliente/Pasta",
        "IDs Arquivos Anexados",
        "Link Pasta Cliente",
        "Status Processamento",
        "Observações de Processamento",
    ],
}


# -------------------------
# Configurações baseadas em classe
# -------------------------
class BaseConfig(object):
    """Configuração base construída a partir do dicionário CONFIG legacy."""
    # As configurações são adicionadas dinamicamente abaixo
    DEBUG = False


# Copia dinamicamente todas as entradas do dicionário CONFIG para a BaseConfig
for _key, _value in CONFIG.items():
    setattr(BaseConfig, _key, _value)


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV = "development"


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"
    SQLALCHEMY_ECHO = True


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = False
    ENV = "testing"


# Mapeamento de nome -> classe
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}

logger.debug(
    "GOOGLE_CREDENTIALS_AS_JSON_STR definido? %s",
    CONFIG.get("GOOGLE_CREDENTIALS_AS_JSON_STR") is not None,
)
logger.debug("Finalizando config.py")
