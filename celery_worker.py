# /var/www/estevaoalmeida.com.br/form-google/celery_worker.py
"""
Ponto de entrada para o worker Celery, alinhado com o padrão de fábrica da aplicação.

Este script cria uma instância da aplicação Flask usando a função `create_app`
e garante que o contexto da aplicação esteja ativo. Isso permite que as tarefas
Celery acessem o banco de dados, as configurações e outras extensões do Flask
corretamente.

Para iniciar o worker, use o comando:
celery -A celery_worker.celery worker --loglevel=info
"""

from app import create_app
from app.celery_app import make_celery

# 1. Cria a aplicação Flask usando a fábrica
flask_app = create_app()

# 2. Cria a instância do Celery, passando a aplicação Flask para a fábrica do Celery
celery = make_celery(flask_app)

# 3. Garante que o contexto da aplicação esteja disponível para o worker
flask_app.app_context().push()

# 4. Importa as tarefas para que o worker possa executá-las
import app.tasks.document_generation
