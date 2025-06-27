"""
Modelo de Placeholder para o sistema peticionador.
"""

import re
from typing import Dict, Any, Optional, Union
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.config.constants import (
    MAX_PLACEHOLDER_NAME_LENGTH,
    PLACEHOLDER_TYPES,
    PLACEHOLDER_CATEGORIES,
    PLACEHOLDER_TYPE_TEXT,
    PLACEHOLDER_CATEGORY_OUTROS,
    REGEX_CPF,
    REGEX_CNPJ,
    REGEX_PHONE,
    REGEX_EMAIL
)


class Placeholder(BaseModel):
    """Modelo para placeholders de templates."""
    
    __tablename__ = "placeholders"
    
    # Identificação
    name = Column(String(MAX_PLACEHOLDER_NAME_LENGTH), nullable=False, index=True)
    label = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Configuração
    type = Column(String(50), nullable=False, default=PLACEHOLDER_TYPE_TEXT)
    category = Column(String(50), nullable=False, default=PLACEHOLDER_CATEGORY_OUTROS, index=True)
    required = Column(Boolean, default=False, nullable=False)
    
    # Validação
    validation_rules = Column(JSON)  # Regras de validação específicas
    default_value = Column(Text)
    placeholder_text = Column(String(200))  # Texto de exemplo
    
    # Relacionamento com template
    template_id = Column(Integer, ForeignKey('templates.id'), nullable=False)
    template = relationship("Template", back_populates="placeholders")
    
    # Metadados de posicionamento
    order_index = Column(Integer, default=0)
    group_name = Column(String(100))  # Para agrupar campos relacionados
    
    def to_dict(self, exclude: list = None) -> Dict[str, Any]:
        """
        Converte placeholder para dicionário.
        
        Args:
            exclude: Campos para excluir
            
        Returns:
            Dicionário com dados do placeholder
        """
        data = super().to_dict(exclude)
        
        # Garante que validation_rules seja dict
        if self.validation_rules is None:
            data['validation_rules'] = {}
        
        return data
    
    def validate_value(self, value: Any) -> bool:
        """
        Valida valor contra regras do placeholder.
        
        Args:
            value: Valor para validar
            
        Returns:
            True se válido, False caso contrário
        """
        # Valor vazio em campo obrigatório
        if self.required and (value is None or str(value).strip() == ""):
            return False
        
        # Se não é obrigatório e está vazio, é válido
        if not self.required and (value is None or str(value).strip() == ""):
            return True
        
        # Converte para string para validação
        str_value = str(value).strip()
        
        # Validação por tipo
        return self._validate_by_type(str_value)
    
    def _validate_by_type(self, value: str) -> bool:
        """
        Valida valor baseado no tipo do placeholder.
        
        Args:
            value: Valor string para validar
            
        Returns:
            True se válido
        """
        if self.type == "text":
            return self._validate_text(value)
        elif self.type == "number":
            return self._validate_number(value)
        elif self.type == "email":
            return self._validate_email(value)
        elif self.type == "cpf":
            return self._validate_cpf(value)
        elif self.type == "cnpj":
            return self._validate_cnpj(value)
        elif self.type == "phone":
            return self._validate_phone(value)
        elif self.type == "date":
            return self._validate_date(value)
        elif self.type == "currency":
            return self._validate_currency(value)
        elif self.type == "select":
            return self._validate_select(value)
        else:
            return True  # Tipo desconhecido, permite
    
    def _validate_text(self, value: str) -> bool:
        """Valida campo de texto."""
        rules = self.validation_rules or {}
        
        # Comprimento mínimo
        if 'min_length' in rules and len(value) < rules['min_length']:
            return False
        
        # Comprimento máximo
        if 'max_length' in rules and len(value) > rules['max_length']:
            return False
        
        # Regex personalizado
        if 'pattern' in rules:
            if not re.match(rules['pattern'], value):
                return False
        
        return True
    
    def _validate_number(self, value: str) -> bool:
        """Valida campo numérico."""
        try:
            num_value = float(value.replace(',', '.'))
            rules = self.validation_rules or {}
            
            # Valor mínimo
            if 'min_value' in rules and num_value < rules['min_value']:
                return False
            
            # Valor máximo
            if 'max_value' in rules and num_value > rules['max_value']:
                return False
            
            return True
        except ValueError:
            return False
    
    def _validate_email(self, value: str) -> bool:
        """Valida email."""
        return bool(re.match(REGEX_EMAIL, value))
    
    def _validate_cpf(self, value: str) -> bool:
        """Valida CPF."""
        # Remove formatação
        cpf = re.sub(r'[^0-9]', '', value)
        
        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False
        
        # Verifica se não são todos iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Validação dos dígitos verificadores
        def calculate_digit(cpf_partial):
            sum_val = sum(int(cpf_partial[i]) * (len(cpf_partial) + 1 - i) for i in range(len(cpf_partial)))
            remainder = sum_val % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Primeiro dígito
        if int(cpf[9]) != calculate_digit(cpf[:9]):
            return False
        
        # Segundo dígito
        if int(cpf[10]) != calculate_digit(cpf[:10]):
            return False
        
        return True
    
    def _validate_cnpj(self, value: str) -> bool:
        """Valida CNPJ."""
        # Remove formatação
        cnpj = re.sub(r'[^0-9]', '', value)
        
        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            return False
        
        # Verifica se não são todos iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Validação dos dígitos verificadores
        def calculate_cnpj_digit(cnpj_partial, weights):
            sum_val = sum(int(cnpj_partial[i]) * weights[i] for i in range(len(cnpj_partial)))
            remainder = sum_val % 11
            return 0 if remainder < 2 else 11 - remainder
        
        # Primeiro dígito
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        if int(cnpj[12]) != calculate_cnpj_digit(cnpj[:12], weights1):
            return False
        
        # Segundo dígito
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        if int(cnpj[13]) != calculate_cnpj_digit(cnpj[:13], weights2):
            return False
        
        return True
    
    def _validate_phone(self, value: str) -> bool:
        """Valida telefone."""
        return bool(re.match(REGEX_PHONE, value))
    
    def _validate_date(self, value: str) -> bool:
        """Valida data."""
        from datetime import datetime
        try:
            # Tenta formatos comuns
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                try:
                    datetime.strptime(value, fmt)
                    return True
                except ValueError:
                    continue
            return False
        except Exception:
            return False
    
    def _validate_currency(self, value: str) -> bool:
        """Valida valor monetário."""
        # Remove formatação comum de moeda
        clean_value = re.sub(r'[R$\s.,]', '', value).replace(',', '.')
        try:
            float(clean_value)
            return True
        except ValueError:
            return False
    
    def _validate_select(self, value: str) -> bool:
        """Valida campo select."""
        rules = self.validation_rules or {}
        options = rules.get('options', [])
        
        if not options:
            return True  # Se não há opções definidas, aceita qualquer valor
        
        return value in options
    
    def get_form_field_config(self) -> Dict[str, Any]:
        """
        Retorna configuração para campo de formulário.
        
        Returns:
            Dicionário com configuração do campo
        """
        config = {
            'name': self.name,
            'label': self.label,
            'type': self.type,
            'required': self.required,
            'placeholder': self.placeholder_text,
            'default_value': self.default_value,
            'description': self.description
        }
        
        # Adiciona regras de validação específicas
        if self.validation_rules:
            config['validation'] = self.validation_rules
        
        return config
    
    @classmethod
    def find_by_template(cls, template_id: int) -> list:
        """
        Busca placeholders por template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Lista de placeholders do template
        """
        return cls.query.filter_by(template_id=template_id).order_by(cls.order_index, cls.name).all()
    
    @classmethod
    def find_by_category(cls, template_id: int, category: str) -> list:
        """
        Busca placeholders por template e categoria.
        
        Args:
            template_id: ID do template
            category: Categoria dos placeholders
            
        Returns:
            Lista de placeholders da categoria
        """
        return cls.query.filter_by(
            template_id=template_id, 
            category=category
        ).order_by(cls.order_index, cls.name).all()
    
    def __repr__(self) -> str:
        """Representação string do placeholder."""
        return f"<Placeholder(id={self.id}, name='{self.name}', type='{self.type}')>"