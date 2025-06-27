"""
Ponto de entrada principal da aplicação Flask.

Este arquivo cria a instância da aplicação Flask utilizando o padrão de 'Application Factory'.
Ele é o arquivo que deve ser apontado pelo servidor WSGI (Gunicorn).
"""

import os
from app import create_app

# Obtém a configuração do ambiente (ex: 'development', 'production')
# a partir da variável de ambiente. O padrão é 'development'.
env = os.getenv("FLASK_CONFIG") or "development"

# Cria a instância da aplicação Flask
app = create_app()

if __name__ == "__main__":
    # Este bloco só é executado quando o script é chamado diretamente.
    # Útil para o desenvolvimento local.
    app.run() 