"""
Testes unitários para EnumValidator - Fase 1.5.2
Testes adicionais para atingir meta de cobertura de 80%.
"""

import pytest
from app.models.enums import EnumValidator, FieldType, DocumentStatus, TemplateStatus


@pytest.mark.unit
class TestEnumValidator:
    """
    Suite de testes para classe EnumValidator.
    
    Cobertura de testes:
    - ✅ Validação de tipos de campo
    - ✅ Validação de status de documento  
    - ✅ Validação de status de template
    - ✅ Validação de transições de status
    - ✅ Casos de erro e edge cases
    """
    
    def test_validate_field_type_valid_values(self):
        """Test: EnumValidator aceita tipos de campo válidos."""
        valid_types = ["text", "email", "number", "date", "select", 
                      "multiselect", "textarea", "checkbox", "file"]
        
        for field_type in valid_types:
            assert EnumValidator.validate_field_type(field_type) is True
    
    def test_validate_field_type_invalid_values(self):
        """Test: EnumValidator rejeita tipos de campo inválidos."""
        invalid_types = ["invalid", "unknown", "", "TEXT", "Email"]
        
        for field_type in invalid_types:
            assert EnumValidator.validate_field_type(field_type) is False
    
    def test_validate_document_status_valid_values(self):
        """Test: EnumValidator aceita status de documento válidos."""
        valid_statuses = ["draft", "active", "archived", "deprecated"]
        
        for status in valid_statuses:
            assert EnumValidator.validate_document_status(status) is True
    
    def test_validate_document_status_invalid_values(self):
        """Test: EnumValidator rejeita status de documento inválidos."""
        invalid_statuses = ["invalid", "published", "", "DRAFT"]
        
        for status in invalid_statuses:
            assert EnumValidator.validate_document_status(status) is False
    
    def test_validate_template_status_valid_values(self):
        """Test: EnumValidator aceita status de template válidos."""
        valid_statuses = ["draft", "published", "reviewing", "archived"]
        
        for status in valid_statuses:
            assert EnumValidator.validate_template_status(status) is True
    
    def test_validate_template_status_invalid_values(self):
        """Test: EnumValidator rejeita status de template inválidos."""
        invalid_statuses = ["invalid", "active", "", "PUBLISHED"]
        
        for status in invalid_statuses:
            assert EnumValidator.validate_template_status(status) is False


@pytest.mark.unit
class TestStatusTransitions:
    """
    Testes específicos para validação de transições de status.
    """
    
    def test_validate_document_status_transitions_valid(self):
        """Test: Transições válidas de documento são aceitas."""
        valid_transitions = [
            ("draft", "active"),
            ("draft", "archived"),
            ("active", "archived"),
            ("active", "deprecated"),
            ("archived", "active")
        ]
        
        for current, target in valid_transitions:
            assert EnumValidator.validate_status_transition(
                current, target, "document"
            ) is True
    
    def test_validate_document_status_transitions_invalid(self):
        """Test: Transições inválidas de documento são rejeitadas."""
        invalid_transitions = [
            ("deprecated", "active"),  # Estado final
            ("deprecated", "archived"),
            ("active", "draft"),  # Não pode voltar para draft
            ("archived", "deprecated")  # Não pode ir direto para deprecated
        ]
        
        for current, target in invalid_transitions:
            assert EnumValidator.validate_status_transition(
                current, target, "document"
            ) is False
    
    def test_validate_template_status_transitions_valid(self):
        """Test: Transições válidas de template são aceitas."""
        valid_transitions = [
            ("draft", "reviewing"),
            ("draft", "archived"),
            ("reviewing", "published"),
            ("reviewing", "draft"),
            ("reviewing", "archived"),
            ("published", "archived"),
            ("published", "reviewing"),
            ("archived", "draft")
        ]
        
        for current, target in valid_transitions:
            assert EnumValidator.validate_status_transition(
                current, target, "template"
            ) is True
    
    def test_validate_template_status_transitions_invalid(self):
        """Test: Transições inválidas de template são rejeitadas."""
        invalid_transitions = [
            ("draft", "published"),  # Deve passar por reviewing
            ("published", "draft"),  # Não pode voltar direto para draft
            ("archived", "published"),  # Não pode ir direto para published
            ("archived", "reviewing")  # Não pode ir direto para reviewing
        ]
        
        for current, target in invalid_transitions:
            assert EnumValidator.validate_status_transition(
                current, target, "template"
            ) is False
    
    def test_validate_status_transition_invalid_type(self):
        """Test: Tipo de status inválido é rejeitado."""
        assert EnumValidator.validate_status_transition(
            "draft", "active", "invalid_type"
        ) is False
    
    def test_validate_status_transition_invalid_status_values(self):
        """Test: Valores de status inválidos são rejeitados."""
        # Status inválido para documento
        assert EnumValidator.validate_status_transition(
            "invalid", "active", "document"
        ) is False
        
        # Status inválido para template
        assert EnumValidator.validate_status_transition(
            "draft", "invalid", "template"
        ) is False


@pytest.mark.unit
class TestEnumMethods:
    """
    Testes para métodos específicos dos ENUMs.
    """
    
    def test_field_type_from_string_method(self):
        """Test: Método from_string do FieldType."""
        field_type = FieldType.from_string("email")
        assert field_type == FieldType.EMAIL
        
        with pytest.raises(ValueError):
            FieldType.from_string("invalid")
    
    def test_field_type_get_all_values(self):
        """Test: Método get_all_values do FieldType."""
        all_values = FieldType.get_all_values()
        expected = {"text", "email", "number", "date", "select", 
                   "multiselect", "textarea", "checkbox", "file"}
        assert all_values == expected
    
    def test_document_status_get_default_status(self):
        """Test: Status padrão de DocumentStatus."""
        default = DocumentStatus.get_default_status()
        assert default == DocumentStatus.DRAFT
    
    def test_document_status_can_transition_to(self):
        """Test: Método can_transition_to de DocumentStatus."""
        draft = DocumentStatus.DRAFT
        active = DocumentStatus.ACTIVE
        deprecated = DocumentStatus.DEPRECATED
        
        assert draft.can_transition_to(active) is True
        assert deprecated.can_transition_to(active) is False
    
    def test_template_status_get_default_status(self):
        """Test: Status padrão de TemplateStatus."""
        default = TemplateStatus.get_default_status()
        assert default == TemplateStatus.DRAFT
    
    def test_template_status_is_public(self):
        """Test: Método is_public de TemplateStatus."""
        assert TemplateStatus.PUBLISHED.is_public() is True
        assert TemplateStatus.DRAFT.is_public() is False
        assert TemplateStatus.REVIEWING.is_public() is False
        assert TemplateStatus.ARCHIVED.is_public() is False
    
    def test_template_status_can_transition_to(self):
        """Test: Método can_transition_to de TemplateStatus."""
        draft = TemplateStatus.DRAFT
        reviewing = TemplateStatus.REVIEWING
        archived = TemplateStatus.ARCHIVED
        
        assert draft.can_transition_to(reviewing) is True
        assert archived.can_transition_to(reviewing) is False


@pytest.mark.unit
class TestEnumConstants:
    """
    Testes para constantes exportadas pelos ENUMs.
    """
    
    def test_field_type_choices_format(self):
        """Test: FIELD_TYPE_CHOICES tem formato correto para forms."""
        from app.models.enums import FIELD_TYPE_CHOICES
        
        # Deve ser lista de tuplas (value, label)
        assert isinstance(FIELD_TYPE_CHOICES, list)
        assert len(FIELD_TYPE_CHOICES) == 9
        
        for choice in FIELD_TYPE_CHOICES:
            assert isinstance(choice, tuple)
            assert len(choice) == 2
            value, label = choice
            assert isinstance(value, str)
            assert isinstance(label, str)
            assert label == value.title()  # Label deve ser title case
    
    def test_document_status_choices_format(self):
        """Test: DOCUMENT_STATUS_CHOICES tem formato correto."""
        from app.models.enums import DOCUMENT_STATUS_CHOICES
        
        assert isinstance(DOCUMENT_STATUS_CHOICES, list)
        assert len(DOCUMENT_STATUS_CHOICES) == 4
        
        expected_values = {"draft", "active", "archived", "deprecated"}
        actual_values = {choice[0] for choice in DOCUMENT_STATUS_CHOICES}
        assert actual_values == expected_values
    
    def test_template_status_choices_format(self):
        """Test: TEMPLATE_STATUS_CHOICES tem formato correto."""
        from app.models.enums import TEMPLATE_STATUS_CHOICES
        
        assert isinstance(TEMPLATE_STATUS_CHOICES, list)
        assert len(TEMPLATE_STATUS_CHOICES) == 4
        
        expected_values = {"draft", "published", "reviewing", "archived"}
        actual_values = {choice[0] for choice in TEMPLATE_STATUS_CHOICES}
        assert actual_values == expected_values 