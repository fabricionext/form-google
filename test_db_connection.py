# test_db_connection.py
import os

import psycopg2
from dotenv import load_dotenv

# Ajusta o caminho para o diretório raiz do projeto, onde o script estará
project_root = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(project_root, ".env")

print(f"--- test_db_connection.py ---")
print(f"Project root (expected location of .env): {project_root}")
print(f"Attempting to load .env from: {dotenv_path}")

loaded = load_dotenv(dotenv_path=dotenv_path, verbose=True)
print(f"load_dotenv result: {loaded}\n")

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")

print(f"Credentials from .env:")
print(f"  User: {db_user}")
print(
    f"  Pass: {db_pass[:3] if db_pass else 'None'}..."
)  # Mostra apenas os primeiros 3 caracteres da senha
print(f"  Host: {db_host}")
print(f"  Port: {db_port}")
print(f"  DB Name: {db_name}\n")

# String de conexão DSN (Data Source Name) para psycopg2
# Usaremos esta forma pois é mais próxima do que o SQLAlchemy faz internamente
# e permite passar sslmode diretamente.

print("--- Attempt 1: Connection with sslmode='require' ---")
dsn_ssl_require = f"user='{db_user}' password='{db_pass}' host='{db_host}' port='{db_port}' dbname='{db_name}' sslmode='require'"
print(
    f"Using DSN (password masked): user='{db_user}' password='****' host='{db_host}' port='{db_port}' dbname='{db_name}' sslmode='require'"
)
try:
    conn_ssl = psycopg2.connect(dsn_ssl_require)
    print("SUCCESS with sslmode='require'!")
    cur = conn_ssl.cursor()
    cur.execute("SELECT version();")
    print(f"PostgreSQL version: {cur.fetchone()}")
    cur.close()
    conn_ssl.close()
except Exception as e:
    print(f"FAILED with sslmode='require':")
    print(f"  Error type: {type(e)}")
    print(f"  Error message: {e}\n")

print(
    "--- Attempt 2: Connection with sslmode='prefer' (driver default often falls to this if SSL available) ---"
)
dsn_ssl_prefer = f"user='{db_user}' password='{db_pass}' host='{db_host}' port='{db_port}' dbname='{db_name}' sslmode='prefer'"
print(
    f"Using DSN (password masked): user='{db_user}' password='****' host='{db_host}' port='{db_port}' dbname='{db_name}' sslmode='prefer'"
)
try:
    conn_prefer = psycopg2.connect(dsn_ssl_prefer)
    print("SUCCESS with sslmode='prefer'!")
    cur = conn_prefer.cursor()
    cur.execute("SELECT version();")
    print(f"PostgreSQL version: {cur.fetchone()}")
    cur.close()
    conn_prefer.close()
except Exception as e:
    print(f"FAILED with sslmode='prefer':")
    print(f"  Error type: {type(e)}")
    print(f"  Error message: {e}\n")


print("--- Attempt 3: Connection WITHOUT explicit sslmode (driver default) ---")
# Esta string de conexão não especifica sslmode, usando o default da libpq
dsn_no_ssl_explicit = f"user='{db_user}' password='{db_pass}' host='{db_host}' port='{db_port}' dbname='{db_name}'"
print(
    f"Using DSN (password masked): user='{db_user}' password='****' host='{db_host}' port='{db_port}' dbname='{db_name}'"
)
try:
    conn_no_ssl = psycopg2.connect(dsn_no_ssl_explicit)
    print("SUCCESS without explicit sslmode!")
    cur = conn_no_ssl.cursor()
    cur.execute("SELECT version();")
    print(f"PostgreSQL version: {cur.fetchone()}")
    cur.close()
    conn_no_ssl.close()
except Exception as e:
    print(f"FAILED without explicit sslmode:")
    print(f"  Error type: {type(e)}")
    print(f"  Error message: {e}\n")

print("--- test_db_connection.py finished ---")
