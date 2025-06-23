import os

from flask import Flask
from flask_migrate import Migrate

from app.peticionador.models import (
    AutoridadeTransito,
    Cliente,
    PeticaoGerada,
    PeticaoModelo,
    User,
)
from extensions import db  # Importa a instância compartilhada

# Importar todos os modelos para que o Alembic os reconheça
from models import FormularioGerado, RespostaForm

# Carregar a URI do banco de dados a partir das variáveis de ambiente
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não está configurada.")

# Criar uma instância mínima do Flask
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar as extensões com a instância da aplicação
db.init_app(app)
migrate = Migrate(app, db)
