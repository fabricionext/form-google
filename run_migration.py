import os
from flask_migrate import Migrate, upgrade
from app import create_app, db

# Cria uma instância da aplicação usando a factory
# Isso garante que toda a configuração, incluindo a DATABASE_URL, seja carregada
app = create_app(os.getenv('FLASK_CONFIG') or None)
migrate = Migrate(app, db)

# Aplicar as migrações ao iniciar
with app.app_context():
    print("INFO: Aplicando migrações do banco de dados...")
    upgrade()
    print("INFO: Migrações aplicadas com sucesso.")
