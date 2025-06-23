import os
import sys
import traceback
from pathlib import Path


def check_file_structure():
    """Verifica se todos os arquivos necessários existem"""
    print("=== VERIFICAÇÃO DE ESTRUTURA DE ARQUIVOS ===")

    required_files = [
        "app/__init__.py",
        "app/main.py",
        # 'app/peticionador.py',  # Removido pois é um diretório
        "extensions.py",
        "config.py",
        "document_generator.py",
        "security_middleware.py",
        "app/logging_config.py",
        "app/api/document_api.py",
    ]

    missing_files = []

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - ARQUIVO NÃO ENCONTRADO")
            missing_files.append(file_path)

    return missing_files


def check_imports():
    """Testa as importações principais"""
    print("\n=== VERIFICAÇÃO DE IMPORTAÇÕES ===")

    imports_to_test = [
        ("flask", "Flask"),
        ("flask_sqlalchemy", "SQLAlchemy"),
        ("flask_limiter", "Limiter"),
        ("flask_talisman", "Talisman"),
        ("flask_wtf.csrf", "CSRFProtect"),
        ("flask_migrate", "Migrate"),
    ]

    failed_imports = []

    for module, component in imports_to_test:
        try:
            exec(f"from {module} import {component}")
            print(f"✅ {module}.{component}")
        except ImportError as e:
            print(f"❌ {module}.{component} - ERRO: {e}")
            failed_imports.append((module, component, str(e)))

    return failed_imports


def check_blueprint_import():
    """Verifica especificamente a importação do blueprint peticionador"""
    print("\n=== VERIFICAÇÃO DO BLUEPRINT PETICIONADOR ===")

    try:
        # Adicionar o diretório atual ao path se necessário
        if "." not in sys.path:
            sys.path.insert(0, ".")

        from app.peticionador import peticionador_bp

        print("✅ Blueprint peticionador_bp importado com sucesso")
        print(f"   - Nome: {peticionador_bp.name}")
        print(f"   - URL Prefix: {peticionador_bp.url_prefix}")
        return True
    except Exception as e:
        print(f"❌ Erro ao importar peticionador_bp: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False


def check_config():
    """Verifica a configuração"""
    print("\n=== VERIFICAÇÃO DE CONFIGURAÇÃO ===")

    try:
        from config import CONFIG

        print("✅ CONFIG importado com sucesso")

        # Verificar chaves importantes
        important_keys = ["GOOGLE_CREDENTIALS_AS_JSON_STR", "TEMPLATES"]

        for key in important_keys:
            if key in CONFIG:
                print(f"✅ {key} presente na configuração")
            else:
                print(f"❌ {key} ausente na configuração")

    except Exception as e:
        print(f"❌ Erro ao importar CONFIG: {e}")
        return False

    return True


def check_database():
    """Verifica a configuração do banco de dados"""
    print("\n=== VERIFICAÇÃO DO BANCO DE DADOS ===")

    try:
        from extensions import db

        print("✅ Extensão db importada com sucesso")

        # Verificar se o arquivo de banco existe (se for SQLite)
        db_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            if os.path.exists(db_path):
                print(f"✅ Arquivo de banco encontrado: {db_path}")
            else:
                print(f"⚠️  Arquivo de banco não encontrado: {db_path}")
                print("   (Isso pode ser normal se for a primeira execução)")

    except Exception as e:
        print(f"❌ Erro com extensão db: {e}")
        return False

    return True


def test_app_creation():
    """Testa a criação da aplicação Flask"""
    print("\n=== TESTE DE CRIAÇÃO DA APLICAÇÃO ===")

    try:
        # Tentar importar e criar a app
        exec(
            open("your_main_file.py").read()
        )  # Substitua pelo nome do seu arquivo principal
        print("✅ Aplicação criada com sucesso")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar aplicação: {e}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False


def main():
    """Executa todos os diagnósticos"""
    print("DIAGNÓSTICO DA APLICAÇÃO FLASK")
    print("=" * 50)

    # Executar todas as verificações
    missing_files = check_file_structure()
    failed_imports = check_imports()
    blueprint_ok = check_blueprint_import()
    config_ok = check_config()
    db_ok = check_database()

    print("\n" + "=" * 50)
    print("RESUMO DO DIAGNÓSTICO")
    print("=" * 50)

    if missing_files:
        print(f"❌ {len(missing_files)} arquivo(s) não encontrado(s)")
        for file in missing_files:
            print(f"   - {file}")

    if failed_imports:
        print(f"❌ {len(failed_imports)} importação(ões) falharam")
        for module, component, error in failed_imports:
            print(f"   - {module}.{component}: {error}")

    if not blueprint_ok:
        print("❌ Problema com o blueprint peticionador")

    if not config_ok:
        print("❌ Problema com a configuração")

    if not db_ok:
        print("❌ Problema com o banco de dados")

    if not any(
        [missing_files, failed_imports, not blueprint_ok, not config_ok, not db_ok]
    ):
        print("✅ Todos os diagnósticos passaram!")
        print("   O problema pode estar em tempo de execução.")
        print("   Verifique os logs da aplicação para mais detalhes.")


if __name__ == "__main__":
    main()
    print("Script rodou!")
print("TESTE DE SAÍDA")
