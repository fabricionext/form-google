# alembic/env.py
print("!!! env.py: Script starts !!!")

import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from sqlalchemy.engine.url import URL

from alembic import context

# --- Determine path to .env file ---
# alembic/env.py is here: project_root/alembic/env.py
# .env is in project_root: project_root/.env
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
print(f"!!! env.py: Attempting to load .env from: {env_path} !!!")

# --- Load .env file ---
dotenv_loaded = load_dotenv(dotenv_path=env_path, verbose=True)
print(
    f"!!! env.py: load_dotenv(path='{env_path}') returned: {dotenv_loaded} !!!"
)  # verbose=True might show if file not found

# --- Print critical environment variables AFTER attempting to load .env ---
print(
    f"!!! env.py: AFTER load_dotenv - os.getenv('DB_USER'): {os.getenv('DB_USER')} !!!"
)
print(
    f"!!! env.py: AFTER load_dotenv - os.getenv('DB_PASS') (first 3 chars): {str(os.getenv('DB_PASS'))[:3] if os.getenv('DB_PASS') else 'None'}... !!!"
)
print(
    f"!!! env.py: AFTER load_dotenv - os.getenv('DB_HOST'): {os.getenv('DB_HOST')} !!!"
)
print(
    f"!!! env.py: AFTER load_dotenv - os.getenv('DB_PORT'): {os.getenv('DB_PORT')} !!!"
)
print(
    f"!!! env.py: AFTER load_dotenv - os.getenv('DB_NAME'): {os.getenv('DB_NAME')} !!!"
)


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Flask-SQLAlchemy setup ---
import sys
from pathlib import Path

project_root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root_path))
print(f"!!! env.py: Added to sys.path: {str(project_root_path)} !!!")
try:
    from app import app, db  # Import app and db from your Flask app

    print("!!! env.py: Successfully imported 'app' and 'db' from 'app.py' !!!")
    target_metadata = db.metadata
    print("!!! env.py: target_metadata set from db.metadata !!!")
except ImportError as e:
    print(f"!!! env.py: FAILED to import 'app' or 'db' from 'app.py': {e} !!!")
    print(
        "!!! env.py: Ensure your Flask app ('app.py') and its SQLAlchemy instance ('db') are correctly defined and accessible."
    )
    target_metadata = None  # Keep this for safety
    raise ImportError(
        "Could not import 'app' or 'db' from app.py, Alembic cannot proceed."
    ) from e
# --- End Flask-SQLAlchemy setup ---


def run_migrations_offline() -> None:
    print("!!! env.py: Running migrations OFFLINE !!!")
    """Run migrations in 'offline' mode."""
    # Simplified for now, as online mode is the primary concern
    url = config.get_main_option(
        "sqlalchemy.url"
    )  # This would likely be from alembic.ini
    print(f"!!! env.py OFFLINE: sqlalchemy.url from config: {url} !!!")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    print("!!! env.py: Running migrations ONLINE !!!")
    """Run migrations in 'online' mode."""

    with app.app_context():
        # 'db' is the instance imported from app.py, which should be configured by the Flask app.
        # The Flask app itself (app.py) handles loading .env and setting up its database URI.
        # db.engine should reflect that configuration.
        connectable = db.engine
        print(f"!!! env.py ONLINE: Using db.engine from Flask app: {connectable} !!!")
        # We expect app.py to have correctly configured the DB_URI, including any SSL requirements if necessary.
        # For example, if app.py sets SQLALCHEMY_DATABASE_URI to '...?...sslmode=require', db.engine will use it.

        try:
            with connectable.connect() as connection:
                print("!!! env.py ONLINE: Connection to DB successful !!!")
                context.configure(
                    connection=connection, target_metadata=target_metadata
                )
                print("!!! env.py ONLINE: Context configured !!!")
                with context.begin_transaction():
                    print("!!! env.py ONLINE: Beginning transaction for migrations !!!")
                    context.run_migrations()
                    print("!!! env.py ONLINE: run_migrations() called !!!")
        except Exception as e:
            print(
                f"!!! env.py ONLINE: ERROR during connectable.connect() or migration: {e} !!!"
            )
            raise  # Re-raise the exception to see the full traceback


if context.is_offline_mode():
    print("!!! env.py: Context is OFFLINE !!!")
    run_migrations_offline()
else:
    print("!!! env.py: Context is ONLINE !!!")
    run_migrations_online()

print("!!! env.py: Script ends !!!")
