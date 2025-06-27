"""
Arquivo de entrada para servidores WSGI como o Gunicorn.
"""
from application import app

if __name__ == "__main__":
    # Este bloco permite executar o servidor de desenvolvimento diretamente
    # com `python wsgi.py`, mas a prática recomendada é usar `flask run`
    # ou o servidor Gunicorn.
    app.run()
