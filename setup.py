from setuptools import find_packages, setup

setup(
    name="form_google",
    version="1.0.0",
    description="Sistema de cadastro e automação de documentos Google Docs para ADV.",
    author="Fabricio Almeida",
    author_email="fabricionext@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # Dependências principais
        "Flask",
        "gunicorn",
        "google-api-python-client",
        "oauth2client",
        "sqlalchemy",
        # Bibliotecas usadas nos testes e em módulos importados
        "psycopg2-binary",
        "python-dotenv",
        "requests",
        "python-dateutil",
        "flask_sqlalchemy",
        "flask_login",
        "flask_limiter",
        "flask_talisman",
        "flask_wtf",
        "flask_migrate",
    ],
    python_requires=">=3.8",
    entry_points={"console_scripts": ["form-google=app:main"]},
)
