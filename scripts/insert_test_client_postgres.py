import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Carrega variáveis de ambiente do .env que está na raiz do projeto
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# Prioriza DATABASE_URL (12factor) e depois SQLALCHEMY_DATABASE_URI para compatibilidade
DB_URL = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
if not DB_URL:
    # Monta a URL manualmente a partir de DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    if all([db_name, db_user, db_pass]):
        DB_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        print(f"Construída DATABASE_URL automaticamente: {DB_URL}")
    else:
        print(
            "ERRO: Não foi possível construir DATABASE_URL: verifique DB_NAME, DB_USER, DB_PASS no .env"
        )
        sys.exit(1)

# Dados do cliente de teste
TEST_CPF = "11122233344"
TEST_EMAIL = "peticionador.teste@example.com"

engine = create_engine(DB_URL, echo=False, future=True)

select_sql = text("SELECT id FROM respostas_form WHERE cpf = :cpf LIMIT 1;")
insert_sql = text(
    """
INSERT INTO respostas_form (
    submission_id,
    tipo_pessoa,
    primeiro_nome,
    sobrenome,
    cpf,
    email,
    status_processamento,
    timestamp_processamento
) VALUES (
    :submission_id,
    :tipo_pessoa,
    :primeiro_nome,
    :sobrenome,
    :cpf,
    :email,
    :status_processamento,
    NOW()
);
"""
)

params = {
    "submission_id": f"test_submission_{datetime.utcnow().timestamp()}",
    "tipo_pessoa": "pf",
    "primeiro_nome": "Cliente",
    "sobrenome": "Teste Peticionador",
    "cpf": TEST_CPF,
    "email": TEST_EMAIL,
    "status_processamento": "Completo",
}

with engine.begin() as conn:
    exists = conn.execute(select_sql, {"cpf": TEST_CPF}).first()
    if exists:
        print(
            f"Cliente com CPF {TEST_CPF} já existia no PostgreSQL. Nenhuma inserção realizada."
        )
    else:
        conn.execute(insert_sql, params)
        print(
            f"Cliente de teste com CPF {TEST_CPF} inserido com sucesso no PostgreSQL."
        )
