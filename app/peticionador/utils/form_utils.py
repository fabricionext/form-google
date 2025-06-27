"""
Form Utilities
==============

Funções utilitárias para construção e manipulação de formulários.
Migradas do routes.py para melhor organização.
"""

import re
from typing import Dict, List, Optional
from flask_wtf import FlaskForm
from wtforms import DateField, EmailField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email

from .placeholder_utils import (
    categorize_placeholder_key,
    determine_field_type_from_key,
    format_label_from_key,
    is_required_field_key,
    generate_placeholder_text_from_key
)


def build_dynamic_form(placeholders) -> type:
    """
    Gera dinamicamente uma classe WTForm melhorada com campos conforme placeholders.
    Versão atualizada com suporte a categorização e tipos avançados de campo.
    
    Migrado do routes.py com melhorias.
    """
    attrs = {"csrf_enabled": True}

    # Métodos auxiliares para o formulário
    def get_fields_by_category(self, categoria):
        """Retorna campos de uma categoria específica."""
        return [
            field
            for field_name, field in self._fields.items()
            if hasattr(field, "_categoria") and field._categoria == categoria
        ]

    def get_categories(self):
        """Retorna todas as categorias disponíveis."""
        categories = set()
        for field_name, field in self._fields.items():
            if hasattr(field, "_categoria"):
                categories.add(field._categoria)
        return sorted(categories)

    attrs["get_fields_by_category"] = get_fields_by_category
    attrs["get_categories"] = get_categories

    for ph in placeholders:
        validators = []

        # Adicionar validação se obrigatório
        if getattr(ph, "obrigatorio", False):
            validators.append(DataRequired(message="Campo obrigatório"))

        # Configurações básicas do campo
        label_value = (
            getattr(ph, "label_form", None) or 
            getattr(ph, "label", None) or 
            format_label_from_key(ph.chave)
        )

        field_kwargs = {
            "label": label_value,
            "validators": validators,
        }

        # Texto placeholder
        placeholder_text = (
            getattr(ph, "placeholder_text", None) or
            getattr(ph, "placeholder_texto", None) or
            generate_placeholder_text_from_key(ph.chave)
        )
        render_kw = {"placeholder": placeholder_text, "class": "form-control"}
        
        # Adicionar mapeamento dinâmico com data-map-key
        map_key = determine_client_map_key(ph.chave)
        if map_key:
            render_kw["data-map-key"] = map_key

        # Determinar tipo de campo
        tipo_campo = getattr(ph, "tipo_campo", "string")
        
        # Criar campo baseado no tipo
        if tipo_campo == "email":
            validators.append(Email(message="Email inválido"))
            field = EmailField(**field_kwargs, render_kw=render_kw)
        elif tipo_campo == "date":
            field = DateField(**field_kwargs, render_kw=render_kw)
        elif tipo_campo == "textarea":
            render_kw["rows"] = 4
            field = TextAreaField(**field_kwargs, render_kw=render_kw)
        elif tipo_campo == "select":
            choices = get_choices_for_field_key(ph.chave)
            field = SelectField(**field_kwargs, choices=choices, render_kw=render_kw)
        else:
            # Campo de texto padrão
            if tipo_campo == "tel":
                render_kw["type"] = "tel"
            field = StringField(**field_kwargs, render_kw=render_kw)

        # Adicionar categoria ao campo para organização
        field._categoria = categorize_placeholder_key(ph.chave)
        
        # Adicionar campo à classe
        attrs[ph.chave] = field

    # Criar e retornar classe do formulário
    return type("DynamicForm", (FlaskForm,), attrs)


def determine_client_map_key(field_name: str) -> Optional[str]:
    """
    Determina a chave de mapeamento de cliente baseada no nome do campo.
    
    Migrado do routes.py com melhorias.
    """
    field_lower = field_name.lower()
    
    # Mapeamento de campos do cliente
    mapping_rules = {
        # Dados pessoais básicos
        'primeiro_nome': 'primeiro_nome',
        'nome': 'primeiro_nome',
        'sobrenome': 'sobrenome',
        'ultimo_nome': 'sobrenome',
        'cpf': 'cpf',
        'rg_numero': 'rg_numero',
        'rg': 'rg_numero',
        'cnh_numero': 'cnh_numero',
        'cnh': 'cnh_numero',
        'email': 'email',
        'telefone_celular': 'telefone_celular',
        'telefone': 'telefone_celular',
        'celular': 'telefone_celular',
        'data_nascimento': 'data_nascimento',
        'nascimento': 'data_nascimento',
        'nacionalidade': 'nacionalidade',
        'estado_civil': 'estado_civil',
        'profissao': 'profissao',
        'profissão': 'profissao',
        
        # Endereço
        'logradouro': 'endereco_logradouro',
        'endereço_logradouro': 'endereco_logradouro',
        'endereco_logradouro': 'endereco_logradouro',
        'numero': 'endereco_numero',
        'endereço_numero': 'endereco_numero', 
        'endereco_numero': 'endereco_numero',
        'complemento': 'endereco_complemento',
        'endereço_complemento': 'endereco_complemento',
        'endereco_complemento': 'endereco_complemento',
        'bairro': 'endereco_bairro',
        'endereço_bairro': 'endereco_bairro',
        'endereco_bairro': 'endereco_bairro',
        'cidade': 'endereco_cidade',
        'endereço_cidade': 'endereco_cidade',
        'endereco_cidade': 'endereco_cidade',
        'estado': 'endereco_estado',
        'endereço_uf': 'endereco_estado',
        'endereco_uf': 'endereco_estado',
        'uf': 'endereco_estado',
        'cep': 'endereco_cep',
        'endereço_cep': 'endereco_cep',
        'endereco_cep': 'endereco_cep',
    }
    
    # Detectar padrões do tipo 'autor_1_nome', 'autor_2_cpf', etc.
    autor_match = re.match(r'autor_\d+_(.+)', field_lower)
    if autor_match:
        base_field = autor_match.group(1)
        return mapping_rules.get(base_field)
    
    # Padrão para campos de autor sem numeração
    autor_simple_match = re.match(r'autor_(.+)', field_lower)
    if autor_simple_match:
        base_field = autor_simple_match.group(1)
        return mapping_rules.get(base_field)
    
    # Campos diretos sem prefixo
    return mapping_rules.get(field_lower)


def get_choices_for_field_key(chave: str) -> List[tuple]:
    """
    Retorna opções para campos select baseado na chave.
    
    Migrado do routes.py.
    """
    chave_lower = chave.lower()
    
    if 'estado_civil' in chave_lower:
        return [
            ('', 'Selecione...'),
            ('solteiro', 'Solteiro(a)'),
            ('casado', 'Casado(a)'),
            ('divorciado', 'Divorciado(a)'),
            ('viuvo', 'Viúvo(a)'),
            ('separado', 'Separado(a)'),
            ('uniao_estavel', 'União Estável')
        ]
    elif 'tipo_pessoa' in chave_lower:
        return [
            ('', 'Selecione...'),
            ('fisica', 'Pessoa Física'),
            ('juridica', 'Pessoa Jurídica')
        ]
    elif 'sexo' in chave_lower:
        return [
            ('', 'Selecione...'),
            ('masculino', 'Masculino'),
            ('feminino', 'Feminino'),
            ('outro', 'Outro')
        ]
    elif 'estado' in chave_lower or 'uf' in chave_lower:
        return [
            ('', 'Selecione...'),
            ('AC', 'Acre'),
            ('AL', 'Alagoas'),
            ('AP', 'Amapá'),
            ('AM', 'Amazonas'),
            ('BA', 'Bahia'),
            ('CE', 'Ceará'),
            ('DF', 'Distrito Federal'),
            ('ES', 'Espírito Santo'),
            ('GO', 'Goiás'),
            ('MA', 'Maranhão'),
            ('MT', 'Mato Grosso'),
            ('MS', 'Mato Grosso do Sul'),
            ('MG', 'Minas Gerais'),
            ('PA', 'Pará'),
            ('PB', 'Paraíba'),
            ('PR', 'Paraná'),
            ('PE', 'Pernambuco'),
            ('PI', 'Piauí'),
            ('RJ', 'Rio de Janeiro'),
            ('RN', 'Rio Grande do Norte'),
            ('RS', 'Rio Grande do Sul'),
            ('RO', 'Rondônia'),
            ('RR', 'Roraima'),
            ('SC', 'Santa Catarina'),
            ('SP', 'São Paulo'),
            ('SE', 'Sergipe'),
            ('TO', 'Tocantins')
        ]
    else:
        # Campo select genérico
        return [('', 'Selecione...')]