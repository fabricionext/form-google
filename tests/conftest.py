"""
Configuração global de testes para Framework TDD/QDD.

Este arquivo contém fixtures compartilhadas, configurações de banco de dados
de teste e utilities comuns para todos os testes.
"""

import os
import pytest
import tempfile
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import Flask

# Configurar variáveis de ambiente para testes
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import create_app
from app.extensions import db
from app.models import *


@pytest.fixture(scope='session')
def app():
    """
    Fixture de aplicação Flask para testes.
    Scope: session (uma instância para toda a sessão de testes)
    """
    # Configurações específicas para teste
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'GOOGLE_CLIENT_ID': 'test-client-id',
        'GOOGLE_CLIENT_SECRET': 'test-client-secret',
    }
    
    app = create_app()
    app.config.update(test_config)
    
    # Criar contexto de aplicação
    app_context = app.app_context()
    app_context.push()
    
    yield app
    
    app_context.pop()


@pytest.fixture(scope='session')
def client(app):
    """
    Fixture de cliente de teste Flask.
    """
    return app.test_client()


@pytest.fixture(scope='session')
def runner(app):
    """
    Fixture de runner CLI para testes.
    """
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """
    Fixture de sessão de banco de dados.
    Scope: function (nova sessão para cada teste)
    """
    # Criar todas as tabelas
    db.create_all()
    
    # Iniciar transação
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Configurar sessão de teste
    session = sessionmaker(bind=connection)()
    db.session = session
    
    yield db.session
    
    # Cleanup
    transaction.rollback()
    connection.close()
    db.session.remove()
    db.drop_all()


@pytest.fixture
def auth_headers():
    """
    Headers de autenticação para testes de API.
    """
    return {
        'Authorization': 'Bearer test-token',
        'Content-Type': 'application/json'
    }


@pytest.fixture
def mock_google_drive():
    """
    Mock do Google Drive para testes.
    """
    with patch('app.adapters.google_drive.GoogleDriveAdapter') as mock:
        # Configurar comportamentos padrão
        mock.return_value.copy_document.return_value = {
            'id': 'test-doc-id',
            'name': 'Test Document',
            'webViewLink': 'https://docs.google.com/document/d/test-doc-id'
        }
        mock.return_value.update_document_content.return_value = True
        mock.return_value.create_folder.return_value = 'test-folder-id'
        
        yield mock


@pytest.fixture
def sample_template_data():
    """
    Dados de exemplo para template.
    """
    return {
        'name': 'Template Teste',
        'description': 'Template para testes unitários',
        'category': 'testes',
        'google_doc_id': 'test-google-doc-id',
        'status': 'draft'
    }


@pytest.fixture
def sample_category_data():
    """
    Dados de exemplo para categoria de template.
    """
    return {
        'name': 'Categoria Teste',
        'slug': 'categoria-teste',
        'description': 'Categoria para testes',
        'icon': 'test-icon'
    }


@pytest.fixture
def sample_placeholder_data():
    """
    Dados de exemplo para placeholder.
    """
    return {
        'key': 'cliente_nome',
        'label': 'Nome do Cliente',
        'type': 'text',
        'required': True,
        'validation_rules': {
            'min_length': 2,
            'max_length': 100
        }
    }


# Fixtures para dados de integração
@pytest.fixture
def template_with_placeholders(db_session, sample_template_data):
    """
    Cria um template com placeholders para testes de integração.
    """
    from app.models.document_template import DocumentTemplate
    from app.models.template_placeholder import TemplatePlaceholder
    
    # Criar template
    template = DocumentTemplate(**sample_template_data)
    db_session.add(template)
    db_session.flush()  # Para obter o ID
    
    # Criar placeholders
    placeholders_data = [
        {
            'template_id': template.id,
            'key': 'cliente_nome',
            'label': 'Nome do Cliente',
            'type': 'text',
            'required': True
        },
        {
            'template_id': template.id,
            'key': 'cliente_email',
            'label': 'Email do Cliente',
            'type': 'email',
            'required': True
        },
        {
            'template_id': template.id,
            'key': 'observacoes',
            'label': 'Observações',
            'type': 'textarea',
            'required': False
        }
    ]
    
    for placeholder_data in placeholders_data:
        placeholder = TemplatePlaceholder(**placeholder_data)
        db_session.add(placeholder)
    
    db_session.commit()
    return template


# Utilities para testes
class TestUtils:
    """
    Classe utilitária para testes.
    """
    
    @staticmethod
    def assert_model_fields(obj, expected_data, exclude_fields=None):
        """
        Verifica se os campos do modelo correspondem aos dados esperados.
        """
        exclude_fields = exclude_fields or ['id', 'created_at', 'updated_at']
        
        for key, expected_value in expected_data.items():
            if key not in exclude_fields:
                actual_value = getattr(obj, key, None)
                assert actual_value == expected_value, f"Campo {key}: esperado {expected_value}, obtido {actual_value}"
    
    @staticmethod
    def create_test_user(db_session, email="test@example.com"):
        """
        Cria um usuário de teste.
        """
        from app.models.user import User
        
        user = User(
            email=email,
            username=email.split('@')[0],
            password_hash='test-hash'
        )
        db_session.add(user)
        db_session.commit()
        return user


@pytest.fixture
def test_utils():
    """
    Fixture para utilities de teste.
    """
    return TestUtils


# Marcadores personalizados para performance
def pytest_configure(config):
    """
    Configuração adicional do pytest.
    """
    # Registrar marcadores personalizados
    config.addinivalue_line(
        "markers", "unit: Testes unitários rápidos"
    )
    config.addinivalue_line(
        "markers", "integration: Testes de integração"
    )
    config.addinivalue_line(
        "markers", "e2e: Testes end-to-end"
    )


# Hook para medir performance dos testes
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """
    Hook executado antes de cada teste para configuração.
    """
    # Marcar testes lentos automaticamente
    if hasattr(item, 'get_closest_marker'):
        if item.get_closest_marker('integration') or item.get_closest_marker('e2e'):
            if not item.get_closest_marker('slow'):
                item.add_marker(pytest.mark.slow) 