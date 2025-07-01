import os
import sys
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

# Adiciona o diretório raiz do projeto ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config.settings import _get_database_uri
from dotenv import load_dotenv

def main():
    """Cria o banco de dados se ele não existir."""
    load_dotenv() # Garante que as variáveis de ambiente sejam carregadas
    db_url = _get_database_uri()
    
    if not db_url or 'sqlite' in db_url:
        print("Erro: A URI do banco de dados não está configurada corretamente para PostgreSQL.")
        sys.exit(1)
        
    engine = create_engine(db_url)

    if not database_exists(engine.url):
        print(f"Banco de dados não encontrado. Criando banco: {db_url}")
        try:
            create_database(engine.url)
            print("Banco de dados criado com sucesso.")
        except Exception as e:
            print(f"Erro ao criar banco de dados: {e}")
            sys.exit(1)
    else:
        print("Banco de dados já existe.")

if __name__ == "__main__":
    main()
