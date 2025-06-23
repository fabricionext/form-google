import os
from unittest import mock

import psycopg2
from dotenv import load_dotenv


def perform_db_connection_checks():
    project_root = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.join(project_root, ".env")
    load_dotenv(dotenv_path=dotenv_path, verbose=True)

    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    dsn_ssl_require = f"user='{db_user}' password='{db_pass}' host='{db_host}' port='{db_port}' dbname='{db_name}' sslmode='require'"
    dsn_ssl_prefer = f"user='{db_user}' password='{db_pass}' host='{db_host}' port='{db_port}' dbname='{db_name}' sslmode='prefer'"
    dsn_no_ssl_explicit = f"user='{db_user}' password='{db_pass}' host='{db_host}' port='{db_port}' dbname='{db_name}'"

    results = []
    for dsn in [dsn_ssl_require, dsn_ssl_prefer, dsn_no_ssl_explicit]:
        try:
            conn = psycopg2.connect(dsn)
            cur = conn.cursor()
            cur.execute("SELECT version();")
            _ = cur.fetchone()
            cur.close()
            conn.close()
            results.append(True)
        except Exception:
            results.append(False)
    return all(results)


if __name__ == "__main__":
    print("Running database connection checks...")
    print("Success" if perform_db_connection_checks() else "Failure")


def test_db_connection(monkeypatch):
    """Valida que o script tenta conectar ao banco sem usar rede."""

    class FakeConn:
        def cursor(self):
            return self

        def execute(self, *_args, **_kwargs):
            pass

        def fetchone(self):
            return ("PostgreSQL 15",)

        def close(self):
            pass

    def fake_connect(*_args, **_kwargs):
        return FakeConn()

    monkeypatch.setattr(psycopg2, "connect", fake_connect)
    assert perform_db_connection_checks() is True
