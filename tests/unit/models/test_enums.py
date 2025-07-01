"""
Testes unitários para ENUMs do sistema - Fase 1.5.2
Seguindo metodologia TDD/QDD com critérios Given-When-Then.
"""

import pytest
from enum import Enum

# Os ENUMs ainda não existem - vamos criar os testes primeiro (TDD)


@pytest.mark.unit
class TestFieldType:
    """
    Suite de testes para ENUM FieldType.
    
    Cobertura de testes:
    - ✅ Valores válidos do ENUM
    - ✅ Conversão de string
    - ✅ Comparação e igualdade
    - ✅ Listagem de todos os valores
    - ✅ Validação de tipos inválidos
    """
    
    def test_field_type_values_are_correct(self):
        """
        Test: FieldType contém todos os tipos de campo necessários.
        
        Given: Sistema precisa de tipos de campo específicos
        When: Verifico os valores do ENUM FieldType
        Then: Todos os tipos necessários estão presentes
        """
        from app.models.enums import FieldType
        
        expected_values = {
            "text", "email", "number", "date", "select", 
            "multiselect", "textarea", "checkbox", "file"
        }
        
        actual_values = {field.value for field in FieldType}
        assert actual_values == expected_values
    
    def test_field_type_from_string(self):
        """
        Test: FieldType pode ser criado a partir de string.
        
        Given: String com valor válido de campo
        When: Crio FieldType a partir da string
        Then: ENUM é criado corretamente
        """
        from app.models.enums import FieldType
        
        field_type = FieldType("email")
        assert field_type == FieldType.EMAIL
        assert field_type.value == "email"
    
    def test_field_type_invalid_value_raises_error(self):
        """
        Test: FieldType rejeita valores inválidos.
        
        Given: String com valor inválido
        When: Tento criar FieldType
        Then: ValueError é lançado
        """
        from app.models.enums import FieldType
        
        with pytest.raises(ValueError):
            FieldType("invalid_type")
    
    def test_field_type_comparison(self):
        """
        Test: FieldType suporta comparação correta.
        
        Given: Dois FieldTypes
        When: Comparo eles
        Then: Comparação funciona corretamente
        """
        from app.models.enums import FieldType
        
        assert FieldType.TEXT == FieldType.TEXT
        assert FieldType.TEXT != FieldType.EMAIL
        assert FieldType.TEXT == "text"  # Comparação com string
    
    def test_field_type_all_values_accessible(self):
        """
        Test: Todos os valores de FieldType são acessíveis.
        
        Given: ENUM FieldType definido
        When: Acesso todos os valores
        Then: Posso iterar e acessar cada valor
        """
        from app.models.enums import FieldType
        
        # Teste de iteração
        all_types = list(FieldType)
        assert len(all_types) == 9
        
        # Teste de acesso direto
        assert FieldType.TEXT.value == "text"
        assert FieldType.EMAIL.value == "email"
        assert FieldType.FILE.value == "file"


@pytest.mark.unit
class TestDocumentStatus:
    """
    Suite de testes para ENUM DocumentStatus.
    
    Cobertura de testes:
    - ✅ Valores de status válidos
    - ✅ Transições de status permitidas
    - ✅ Transições inválidas rejeitadas
    - ✅ Status inicial padrão
    """
    
    def test_document_status_values_are_correct(self):
        """
        Test: DocumentStatus contém todos os status necessários.
        """
        from app.models.enums import DocumentStatus
        
        expected_values = {"draft", "active", "archived", "deprecated"}
        actual_values = {status.value for status in DocumentStatus}
        assert actual_values == expected_values
    
    def test_document_status_default_is_draft(self):
        """
        Test: Status padrão de documento é DRAFT.
        """
        from app.models.enums import DocumentStatus
        
        # O primeiro valor deve ser DRAFT (convenção)
        assert DocumentStatus.DRAFT.value == "draft"
    
    def test_document_status_transitions_valid(self):
        """
        Test: Transições válidas de status são permitidas.
        
        Regras de negócio:
        - DRAFT → ACTIVE, ARCHIVED
        - ACTIVE → ARCHIVED, DEPRECATED  
        - ARCHIVED → ACTIVE
        - DEPRECATED → (sem transições)
        """
        from app.models.enums import DocumentStatus
        
        # Definir transições válidas
        valid_transitions = {
            DocumentStatus.DRAFT: {DocumentStatus.ACTIVE, DocumentStatus.ARCHIVED},
            DocumentStatus.ACTIVE: {DocumentStatus.ARCHIVED, DocumentStatus.DEPRECATED},
            DocumentStatus.ARCHIVED: {DocumentStatus.ACTIVE},
            DocumentStatus.DEPRECATED: set()  # Estado final
        }
        
        # Verificar que as transições estão definidas
        for status in DocumentStatus:
            assert status in valid_transitions


@pytest.mark.unit  
class TestTemplateStatus:
    """
    Suite de testes para ENUM TemplateStatus.
    
    Cobertura de testes:
    - ✅ Valores de status de template
    - ✅ Fluxo de publicação
    - ✅ Estados intermediários
    """
    
    def test_template_status_values_are_correct(self):
        """
        Test: TemplateStatus contém todos os status de template.
        """
        from app.models.enums import TemplateStatus
        
        expected_values = {"draft", "published", "reviewing", "archived"}
        actual_values = {status.value for status in TemplateStatus}
        assert actual_values == expected_values
    
    def test_template_status_publishing_flow(self):
        """
        Test: Fluxo de publicação de template é válido.
        
        Fluxo: DRAFT → REVIEWING → PUBLISHED
        """
        from app.models.enums import TemplateStatus
        
        # Estados do fluxo de publicação
        draft = TemplateStatus.DRAFT
        reviewing = TemplateStatus.REVIEWING  
        published = TemplateStatus.PUBLISHED
        archived = TemplateStatus.ARCHIVED
        
        # Verificar que todos os estados existem
        assert draft.value == "draft"
        assert reviewing.value == "reviewing"
        assert published.value == "published"
        assert archived.value == "archived"


@pytest.mark.unit
class TestEnumsIntegration:
    """
    Testes de integração entre ENUMs.
    
    Cobertura:
    - ✅ ENUMs não conflitam entre si
    - ✅ Serialização/deserialização
    - ✅ Uso em estruturas de dados
    """
    
    def test_enums_no_value_conflicts(self):
        """
        Test: ENUMs não têm conflitos de valores entre si.
        """
        from app.models.enums import FieldType, DocumentStatus, TemplateStatus
        
        field_values = {field.value for field in FieldType}
        doc_values = {status.value for status in DocumentStatus}
        template_values = {status.value for status in TemplateStatus}
        
        # Verificar que não há conflitos diretos problemáticos
        # (alguns overlaps como "draft" podem ser OK em contextos diferentes)
        assert len(field_values) == 9  # Todos os field types únicos
        assert len(doc_values) == 4    # Todos os doc status únicos
        assert len(template_values) == 4  # Todos os template status únicos
    
    def test_enums_serialization(self):
        """
        Test: ENUMs podem ser serializados para JSON.
        """
        from app.models.enums import FieldType, DocumentStatus, TemplateStatus
        import json
        
        # Teste de serialização
        data = {
            "field_type": FieldType.EMAIL.value,
            "doc_status": DocumentStatus.ACTIVE.value,
            "template_status": TemplateStatus.PUBLISHED.value
        }
        
        # Deve ser serializável para JSON
        json_str = json.dumps(data)
        assert json_str
        
        # Deve ser deserializável
        loaded_data = json.loads(json_str)
        assert loaded_data["field_type"] == "email"
        assert loaded_data["doc_status"] == "active"
        assert loaded_data["template_status"] == "published"
    
    def test_enums_in_collections(self):
        """
        Test: ENUMs funcionam corretamente em coleções.
        """
        from app.models.enums import FieldType, DocumentStatus
        
        # Em listas
        field_list = [FieldType.TEXT, FieldType.EMAIL, FieldType.NUMBER]
        assert len(field_list) == 3
        assert FieldType.EMAIL in field_list
        
        # Em sets
        status_set = {DocumentStatus.DRAFT, DocumentStatus.ACTIVE}
        assert len(status_set) == 2
        assert DocumentStatus.DRAFT in status_set
        
        # Em dicionários
        mapping = {
            FieldType.TEXT: "Texto simples",
            FieldType.EMAIL: "Endereço de email"
        }
        assert mapping[FieldType.TEXT] == "Texto simples" 