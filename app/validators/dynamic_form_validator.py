"""
Validador específico para o formulário dinâmico
Integração entre validações client-side e server-side
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from flask import current_app
from wtforms import ValidationError
from wtforms.validators import DataRequired, Email, Length, Regexp

from .form_validator import FormValidator, validate_cpf, validate_cnpj

logger = logging.getLogger(__name__)


class DynamicFormValidator:
    """
    Validador específico para formulários dinâmicos
    Fornece validação robusta server-side e integração com validações client-side
    """

    def __init__(self):
        self.errors: Dict[str, List[str]] = {}
        self.warnings: Dict[str, List[str]] = {}
        self.base_validator = FormValidator()

    def add_error(self, field_name: str, message: str):
        """Adiciona um erro de validação para um campo específico"""
        if field_name not in self.errors:
            self.errors[field_name] = []
        self.errors[field_name].append(message)

    def add_warning(self, field_name: str, message: str):
        """Adiciona um aviso para um campo específico"""
        if field_name not in self.warnings:
            self.warnings[field_name] = []
        self.warnings[field_name].append(message)

    def clear_errors(self):
        """Limpa todos os erros"""
        self.errors = {}

    def clear_warnings(self):
        """Limpa todos os avisos"""
        self.warnings = {}

    def has_errors(self) -> bool:
        """Verifica se há erros de validação"""
        return len(self.errors) > 0

    def get_all_errors(self) -> List[str]:
        """Retorna uma lista de todos os erros"""
        all_errors = []
        for field_errors in self.errors.values():
            all_errors.extend(field_errors)
        return all_errors

    def validate_required_field(self, field_name: str, value: Any, field_label: str = None) -> bool:
        """Valida se um campo obrigatório foi preenchido"""
        if not value or (isinstance(value, str) and not value.strip()):
            label = field_label or field_name.replace('_', ' ').title()
            self.add_error(field_name, f"{label} é obrigatório")
            return False
        return True

    def validate_cpf_field(self, field_name: str, value: str) -> bool:
        """Valida campo CPF"""
        if not value:
            return True  # CPF pode ser opcional dependendo do contexto

        is_valid, error_message = validate_cpf(value)
        if not is_valid:
            self.add_error(field_name, error_message)
            return False
        return True

    def validate_cnpj_field(self, field_name: str, value: str) -> bool:
        """Valida campo CNPJ"""
        if not value:
            return True  # CNPJ pode ser opcional dependendo do contexto

        is_valid, error_message = validate_cnpj(value)
        if not is_valid:
            self.add_error(field_name, error_message)
            return False
        return True

    def validate_email_field(self, field_name: str, value: str) -> bool:
        """Valida campo de email"""
        if not value:
            return True  # Email pode ser opcional

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            self.add_error(field_name, "Formato de email inválido")
            return False
        return True

    def validate_phone_field(self, field_name: str, value: str) -> bool:
        """Valida campo de telefone"""
        if not value:
            return True  # Telefone pode ser opcional

        # Remove tudo que não é dígito
        phone_digits = re.sub(r'\D', '', value)
        
        if len(phone_digits) not in [10, 11]:
            self.add_error(field_name, "Telefone deve ter 10 ou 11 dígitos")
            return False
        return True

    def validate_cep_field(self, field_name: str, value: str) -> bool:
        """Valida campo CEP"""
        if not value:
            return True  # CEP pode ser opcional

        cep_digits = re.sub(r'\D', '', value)
        if len(cep_digits) != 8:
            self.add_error(field_name, "CEP deve ter 8 dígitos")
            return False
        return True

    def validate_cnh_field(self, field_name: str, value: str) -> bool:
        """Valida campo CNH"""
        if not value:
            return True  # CNH pode ser opcional

        cnh_digits = re.sub(r'\D', '', value)
        if len(cnh_digits) != 11:
            self.add_error(field_name, "CNH deve ter 11 dígitos")
            return False
        return True

    def validate_rg_field(self, field_name: str, value: str) -> bool:
        """Valida campo RG"""
        if not value:
            return True  # RG pode ser opcional

        # RG tem formatos variados, validação básica
        rg_clean = re.sub(r'[^\w]', '', value)
        if len(rg_clean) < 7 or len(rg_clean) > 12:
            self.add_error(field_name, "RG deve ter entre 7 e 12 caracteres")
            return False
        return True

    def validate_date_field(self, field_name: str, value: str) -> bool:
        """Valida campo de data"""
        if not value:
            return True  # Data pode ser opcional

        # Validar formato de data (YYYY-MM-DD)
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, value):
            self.add_error(field_name, "Data deve estar no formato AAAA-MM-DD")
            return False

        # Validar se é uma data válida
        try:
            from datetime import datetime
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            self.add_error(field_name, "Data inválida")
            return False

        return True

    def validate_text_length(self, field_name: str, value: str, min_length: int = None, max_length: int = None) -> bool:
        """Valida comprimento de texto"""
        if not value:
            return True  # Campo vazio pode ser válido dependendo do contexto

        length = len(value.strip())
        
        if min_length and length < min_length:
            self.add_error(field_name, f"Deve ter pelo menos {min_length} caracteres")
            return False
            
        if max_length and length > max_length:
            self.add_error(field_name, f"Deve ter no máximo {max_length} caracteres")
            return False
            
        return True

    def detect_field_type(self, field_name: str) -> str:
        """Detecta o tipo de campo baseado no nome"""
        field_lower = field_name.lower()
        
        if 'cpf' in field_lower:
            return 'cpf'
        elif 'cnpj' in field_lower:
            return 'cnpj'
        elif 'email' in field_lower:
            return 'email'
        elif 'telefone' in field_lower or 'celular' in field_lower:
            return 'phone'
        elif 'cep' in field_lower:
            return 'cep'
        elif 'cnh' in field_lower:
            return 'cnh'
        elif 'rg' in field_lower and 'cargo' not in field_lower:
            return 'rg'
        elif 'data' in field_lower or 'nascimento' in field_lower:
            return 'date'
        elif 'nome' in field_lower:
            return 'name'
        else:
            return 'text'

    def validate_field(self, field_name: str, value: Any, is_required: bool = False, field_type: str = None) -> bool:
        """Valida um campo específico"""
        # Converter para string se necessário
        if value is not None and not isinstance(value, str):
            value = str(value)

        # Verificar se é obrigatório
        if is_required and not self.validate_required_field(field_name, value):
            return False

        # Se não há valor, não precisa validar formato
        if not value:
            return True

        # Detectar tipo se não foi fornecido
        if not field_type:
            field_type = self.detect_field_type(field_name)

        # Aplicar validação específica do tipo
        validation_methods = {
            'cpf': self.validate_cpf_field,
            'cnpj': self.validate_cnpj_field,
            'email': self.validate_email_field,
            'phone': self.validate_phone_field,
            'cep': self.validate_cep_field,
            'cnh': self.validate_cnh_field,
            'rg': self.validate_rg_field,
            'date': self.validate_date_field,
        }

        validator_method = validation_methods.get(field_type)
        if validator_method:
            return validator_method(field_name, value)

        # Validação padrão para texto
        if field_type == 'name':
            return self.validate_text_length(field_name, value, min_length=2, max_length=100)
        elif field_type == 'text':
            return self.validate_text_length(field_name, value, max_length=255)

        return True

    def validate_form_data(self, form_data: Dict[str, Any], required_fields: List[str] = None) -> Tuple[bool, Dict[str, List[str]], Dict[str, List[str]]]:
        """
        Valida todos os dados do formulário
        
        Args:
            form_data: Dicionário com os dados do formulário
            required_fields: Lista de campos obrigatórios
            
        Returns:
            Tuple: (é_válido, erros, avisos)
        """
        self.clear_errors()
        self.clear_warnings()
        
        required_fields = required_fields or []
        
        # Validar cada campo
        for field_name, value in form_data.items():
            # Pular campos especiais
            if field_name in ['csrf_token', 'submit']:
                continue
                
            is_required = field_name in required_fields
            self.validate_field(field_name, value, is_required)

        # Validações de negócio específicas
        self._validate_business_rules(form_data)

        return not self.has_errors(), dict(self.errors), dict(self.warnings)

    def _validate_business_rules(self, form_data: Dict[str, Any]):
        """Aplica regras de negócio específicas"""
        # Verificar se pelo menos um autor foi preenchido
        author_fields = [k for k in form_data.keys() if k.startswith('autor_')]
        if author_fields:
            # Verificar se há pelo menos um nome de autor preenchido
            author_names = [k for k in author_fields if 'nome' in k and form_data.get(k)]
            if not author_names:
                self.add_error('autor_1_nome', 'Pelo menos um autor deve ser informado')

        # Verificar consistência entre dados de cliente
        cliente_id = form_data.get('cliente_id')
        if cliente_id:
            # Se há cliente_id, verificar se dados básicos estão preenchidos
            if not form_data.get('autor_1_nome') and not form_data.get('autor_1_nome_completo'):
                self.add_warning('autor_1_nome', 'Nome do autor principal não foi preenchido automaticamente')

    def get_validation_summary(self) -> Dict[str, Any]:
        """Retorna um resumo da validação"""
        return {
            'valid': not self.has_errors(),
            'total_errors': len(self.get_all_errors()),
            'total_warnings': sum(len(warnings) for warnings in self.warnings.values()),
            'errors': dict(self.errors),
            'warnings': dict(self.warnings),
            'fields_with_errors': list(self.errors.keys()),
            'fields_with_warnings': list(self.warnings.keys())
        }

    def create_wtforms_validators(self, field_name: str, field_type: str = None) -> List:
        """Cria validadores WTForms para um campo específico"""
        validators = []
        
        # Detectar tipo se não foi fornecido
        if not field_type:
            field_type = self.detect_field_type(field_name)

        # Adicionar validadores específicos
        if field_type == 'email':
            validators.append(Email(message="Email inválido"))
        elif field_type == 'cpf':
            validators.append(Regexp(
                r'^\d{3}\.\d{3}\.\d{3}-\d{2}$',
                message="CPF deve estar no formato XXX.XXX.XXX-XX"
            ))
        elif field_type == 'cnpj':
            validators.append(Regexp(
                r'^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$',
                message="CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX"
            ))
        elif field_type == 'cep':
            validators.append(Regexp(
                r'^\d{5}-\d{3}$',
                message="CEP deve estar no formato XXXXX-XXX"
            ))
        elif field_type == 'phone':
            validators.append(Regexp(
                r'^(\(\d{2}\)\s?)?\d{4,5}-\d{4}$',
                message="Telefone inválido"
            ))

        # Adicionar validadores de comprimento
        if field_type == 'name':
            validators.extend([
                Length(min=2, max=100, message="Nome deve ter entre 2 e 100 caracteres")
            ])
        elif field_type == 'text':
            validators.append(Length(max=255, message="Máximo de 255 caracteres"))

        return validators


# Instância global do validador
dynamic_form_validator = DynamicFormValidator()


def validate_dynamic_form_field(field_name: str, value: Any, is_required: bool = False) -> Tuple[bool, List[str]]:
    """
    Função auxiliar para validar um campo específico
    
    Returns:
        Tuple: (é_válido, lista_de_erros)
    """
    validator = DynamicFormValidator()
    is_valid = validator.validate_field(field_name, value, is_required)
    
    field_errors = validator.errors.get(field_name, [])
    return is_valid, field_errors


def validate_dynamic_form_data(form_data: Dict[str, Any], required_fields: List[str] = None) -> Dict[str, Any]:
    """
    Função auxiliar para validar dados completos do formulário
    
    Returns:
        Dict: Resumo completo da validação
    """
    validator = DynamicFormValidator()
    is_valid, errors, warnings = validator.validate_form_data(form_data, required_fields)
    
    return {
        'valid': is_valid,
        'errors': errors,
        'warnings': warnings,
        'summary': validator.get_validation_summary()
    }


# Custom WTForms Validator Classes
class CPFValidator:
    """Validador personalizado de CPF para WTForms"""
    
    def __init__(self, message=None):
        self.message = message or "CPF inválido"
    
    def __call__(self, form, field):
        if field.data:
            is_valid, error_msg = validate_cpf(field.data)
            if not is_valid:
                raise ValidationError(self.message)


class CNPJValidator:
    """Validador personalizado de CNPJ para WTForms"""
    
    def __init__(self, message=None):
        self.message = message or "CNPJ inválido"
    
    def __call__(self, form, field):
        if field.data:
            is_valid, error_msg = validate_cnpj(field.data)
            if not is_valid:
                raise ValidationError(self.message)


class PhoneValidator:
    """Validador personalizado de telefone para WTForms"""
    
    def __init__(self, message=None):
        self.message = message or "Telefone inválido"
    
    def __call__(self, form, field):
        if field.data:
            phone_digits = re.sub(r'\D', '', field.data)
            if len(phone_digits) not in [10, 11]:
                raise ValidationError(self.message)


class CEPValidator:
    """Validador personalizado de CEP para WTForms"""
    
    def __init__(self, message=None):
        self.message = message or "CEP inválido"
    
    def __call__(self, form, field):
        if field.data:
            cep_digits = re.sub(r'\D', '', field.data)
            if len(cep_digits) != 8:
                raise ValidationError(self.message) 