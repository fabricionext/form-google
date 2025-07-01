"""
Testes unitários para TemplateCategory - Fase 1.5.1
Seguindo metodologia TDD/QDD com critérios Given-When-Then.
"""

import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

import unittest.mock as mock


@pytest.mark.unit
class TestTemplateCategory:
    """
    Suite de testes para modelo TemplateCategory.
    
    Cobertura de testes:
    - ✅ Criação com dados válidos
    - ✅ Validação de campos obrigatórios
    - ✅ Unicidade de slug
    - ✅ Geração automática de slug
    - ✅ Campos com valores padrão
    - ✅ Timestamps automáticos
    """
    
    def test_create_category_with_valid_data(self, db_session, sample_category_data):
        """
        Test: Categoria criada com dados válidos.
        
        Given: Dados válidos de categoria
        When: Criar nova categoria
        Then: Categoria deve ser salva com todos os campos corretos
        """
        # Given
        from app.models.template_category import TemplateCategory
        
        # When
        category = TemplateCategory(**sample_category_data)
        db_session.add(category)
        db_session.commit()
        
        # Then
        assert category.id is not None
        assert category.name == sample_category_data['name']
        assert category.slug == sample_category_data['slug']
        assert category.description == sample_category_data['description']
        assert category.icon == sample_category_data['icon']
        assert category.is_active is True  # Default value
        assert category.order_index == 0   # Default value
        assert isinstance(category.created_at, datetime)
        assert isinstance(category.updated_at, datetime)
    
    def test_create_category_name_required(self, db_session):
        """
        Test: Nome é obrigatório.
        
        Given: Dados sem nome
        When: Tentar criar categoria
        Then: Deve gerar erro de validação
        """
        # Given
        from app.models.template_category import TemplateCategory
        
        # When/Then
        with pytest.raises(Exception):  # SQLAlchemy irá gerar erro
            category = TemplateCategory(slug='test-slug')
            db_session.add(category)
            db_session.commit()
    
    def test_slug_must_be_unique(self, db_session):
        """
        Test: Slug deve ser único.
        
        Given: Categoria existente com slug
        When: Criar nova categoria com mesmo slug
        Then: Deve gerar erro de integridade
        """
        # Given
        from app.models.template_category import TemplateCategory
        
        category1 = TemplateCategory(name='Cat 1', slug='test-slug')
        db_session.add(category1)
        db_session.commit()
        
        # When/Then
        with pytest.raises(IntegrityError):
            category2 = TemplateCategory(name='Cat 2', slug='test-slug')
            db_session.add(category2)
            db_session.commit()
    
    def test_auto_generate_slug_from_name(self, db_session):
        """
        Test: Gerar slug automaticamente do nome.
        
        Given: Categoria sem slug especificado
        When: Salvar categoria
        Then: Slug deve ser gerado automaticamente baseado no nome
        """
        # Given
        from app.models.template_category import TemplateCategory
        
        # When
        category = TemplateCategory(name='Ações Anulatórias de Multas')
        category.generate_slug()  # Método que será implementado
        db_session.add(category)
        db_session.commit()
        
        # Then
        assert category.slug == 'acoes-anulatorias-de-multas'
    
    def test_category_is_active_by_default(self, db_session):
        """
        Test: Categoria é ativa por padrão.
        
        Given: Nova categoria sem especificar is_active
        When: Criar categoria
        Then: is_active deve ser True por padrão
        """
        # Given
        from app.models.template_category import TemplateCategory
        
        # When
        category = TemplateCategory(name='Test Category', slug='test-category')
        db_session.add(category)
        db_session.commit()
        
        # Then
        assert category.is_active is True
    
    def test_order_index_default_zero(self, db_session):
        """
        Test: order_index é 0 por padrão.
        
        Given: Nova categoria sem especificar order_index
        When: Criar categoria
        Then: order_index deve ser 0 por padrão
        """
        # Given
        from app.models.template_category import TemplateCategory
        
        # When
        category = TemplateCategory(name='Test Category', slug='test-category')
        db_session.add(category)
        db_session.commit()
        
        # Then
        assert category.order_index == 0
    
    def test_timestamps_auto_generated(self, db_session):
        """
        Test: Timestamps são gerados automaticamente.
        
        Given: Nova categoria
        When: Salvar categoria
        Then: created_at e updated_at devem ser preenchidos automaticamente
        """
        # Given
        from app.models.template_category import TemplateCategory
        
        # When
        before_creation = datetime.utcnow()
        category = TemplateCategory(name='Test Category', slug='test-category')
        db_session.add(category)
        db_session.commit()
        after_creation = datetime.utcnow()
        
        # Then
        assert category.created_at is not None
        assert category.updated_at is not None
        assert before_creation <= category.created_at <= after_creation
        assert before_creation <= category.updated_at <= after_creation
    
    def test_str_representation(self, db_session, sample_category_data):
        """
        Test: Representação string da categoria.
        
        Given: Categoria criada
        When: Converter para string
        Then: Deve retornar representação legível
        """
        # Given
        from app.models.template_category import TemplateCategory
        
        category = TemplateCategory(**sample_category_data)
        db_session.add(category)
        db_session.commit()
        
        # When
        str_repr = str(category)
        
        # Then
        assert sample_category_data['name'] in str_repr
        assert 'TemplateCategory' in str_repr
    
    @pytest.mark.slow
    def test_bulk_creation_performance(self, db_session):
        """
        Test: Performance na criação em massa de categorias.
        
        Given: Múltiplas categorias para criar
        When: Criar 100 categorias
        Then: Operação deve ser concluída em tempo razoável
        """
        # Given
        from app.models.template_category import TemplateCategory
        import time
        
        # When
        start_time = time.time()
        categories = []
        for i in range(100):
            category = TemplateCategory(
                name=f'Category {i}',
                slug=f'category-{i}',
                description=f'Description for category {i}'
            )
            categories.append(category)
        
        db_session.add_all(categories)
        db_session.commit()
        end_time = time.time()
        
        # Then
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Deve executar em menos de 1 segundo
        assert db_session.query(TemplateCategory).count() == 100


@pytest.mark.integration
class TestTemplateCategoryIntegration:
    """
    Testes de integração para TemplateCategory.
    """
    
    def test_category_templates_relationship(self, db_session):
        """
        Test: Relacionamento categoria -> templates.
        
        Given: Categoria e templates associados
        When: Acessar templates da categoria
        Then: Deve retornar templates corretos
        """
        # Este teste será implementado quando tivermos o relacionamento
        pass


# Fixtures específicas para este modelo
@pytest.fixture
def category_with_templates(db_session, sample_category_data):
    """
    Fixture que cria categoria com templates associados.
    """
    from app.models.template_category import TemplateCategory
    
    category = TemplateCategory(**sample_category_data)
    db_session.add(category)
    db_session.commit()
    
    # TODO: Adicionar templates quando modelo estiver pronto
    
    return category 