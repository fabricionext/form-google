import logging
import os

logging.basicConfig(level=logging.DEBUG)
logging.debug("WSGI.PY: Inicializando aplicação")

# Importa a instância da aplicação já configurada
from application import app

if __name__ == "__main__":
    # Este bloco é para executar o servidor de desenvolvimento do Flask.
    # Não é usado pelo Gunicorn em produção.

    # Define o host e a porta para o servidor de desenvolvimento.
    # Pode ser configurado via variáveis de ambiente FLASK_RUN_HOST e FLASK_RUN_PORT.
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))

    # Habilita o modo debug baseado na variável de ambiente FLASK_DEBUG.
    debug_mode = (
        os.environ.get("FLASK_DEBUG", "1") == "1"
    )  # '1' para True, '0' para False

    logging.info(
        "Iniciando servidor de desenvolvimento em http://%s:%s/ (Debug: %s)",
        host,
        port,
        debug_mode,
    )
    app.run(host=host, port=port, debug=debug_mode)
