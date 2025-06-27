# Standard library imports
import re

# Third party imports
from marshmallow import Schema, ValidationError, fields, validate, validates


class ClienteSchema(Schema):
    """Schema para validação de dados do cliente."""

    # Campos comuns
    id = fields.Int(dump_only=True)
    tipo_pessoa = fields.Str(
        required=True, validate=validate.OneOf(["FISICA", "JURIDICA"])
    )
    email = fields.Email(required=True)
    telefone_celular = fields.Str(validate=validate.Length(max=32))
    telefone_outro = fields.Str(validate=validate.Length(max=32))

    # Pessoa Física
    primeiro_nome = fields.Str(validate=validate.Length(min=2, max=64))
    sobrenome = fields.Str(validate=validate.Length(max=128))
    nome_completo = fields.Str(validate=validate.Length(max=192))
    cpf = fields.Str(validate=validate.Length(max=14))
    rg_numero = fields.Str(validate=validate.Length(max=32))
    rg_orgao_emissor = fields.Str(validate=validate.Length(max=32))
    rg_uf_emissor = fields.Str(validate=validate.Length(max=2))
    data_nascimento = fields.Date()
    nacionalidade = fields.Str(validate=validate.Length(max=32))
    estado_civil = fields.Str(validate=validate.Length(max=20))
    profissao = fields.Str(validate=validate.Length(max=64))
    cnh_numero = fields.Str(validate=validate.Length(max=32))

    # Endereço
    endereco_logradouro = fields.Str(validate=validate.Length(max=128))
    endereco_numero = fields.Str(validate=validate.Length(max=16))
    endereco_complemento = fields.Str(validate=validate.Length(max=64))
    endereco_bairro = fields.Str(validate=validate.Length(max=64))
    endereco_cidade = fields.Str(validate=validate.Length(max=64))
    endereco_estado = fields.Str(validate=validate.Length(max=2))
    endereco_cep = fields.Str(validate=validate.Length(max=16))

    # Pessoa Jurídica
    razao_social = fields.Str(validate=validate.Length(max=128))
    cnpj = fields.Str(validate=validate.Length(max=18))
    representante_nome = fields.Str(validate=validate.Length(max=128))
    representante_cpf = fields.Str(validate=validate.Length(max=14))
    representante_rg_numero = fields.Str(validate=validate.Length(max=32))
    representante_rg_orgao_emissor = fields.Str(validate=validate.Length(max=32))
    representante_rg_uf_emissor = fields.Str(validate=validate.Length(max=2))
    representante_cargo = fields.Str(validate=validate.Length(max=64))

    @validates("cpf")
    def validate_cpf(self, value):
        """Validação básica de CPF."""
        if value and not self._is_valid_cpf(value):
            raise ValidationError("CPF inválido.")
        return value

    @validates("cnpj")
    def validate_cnpj(self, value):
        """Validação básica de CNPJ."""
        if value and not self._is_valid_cnpj(value):
            raise ValidationError("CNPJ inválido.")
        return value

    @validates("endereco_cep")
    def validate_cep(self, value):
        """Validação de CEP."""
        if value:
            # Remove tudo que não é dígito
            clean_cep = re.sub(r"\D", "", value)
            if len(clean_cep) != 8:
                raise ValidationError("CEP deve ter 8 dígitos.")
        return value

    def _is_valid_cpf(self, cpf):
        """Validação simplificada de CPF."""
        # Remove caracteres não numéricos
        cpf = re.sub(r"\D", "", cpf)

        # Verifica se tem 11 dígitos
        if len(cpf) != 11:
            return False

        # Verifica se não são todos números iguais
        if cpf == cpf[0] * 11:
            return False

        # Aqui poderia implementar o algoritmo completo de validação
        return True

    def _is_valid_cnpj(self, cnpj):
        """Validação simplificada de CNPJ."""
        # Remove caracteres não numéricos
        cnpj = re.sub(r"\D", "", cnpj)

        # Verifica se tem 14 dígitos
        if len(cnpj) != 14:
            return False

        # Verifica se não são todos números iguais
        if cnpj == cnpj[0] * 14:
            return False

        # Aqui poderia implementar o algoritmo completo de validação
        return True


class ClienteCreateSchema(ClienteSchema):
    """Schema para criação de cliente - campos obrigatórios."""

    email = fields.Email(required=True)
    tipo_pessoa = fields.Str(
        required=True, validate=validate.OneOf(["FISICA", "JURIDICA"])
    )


class ClienteUpdateSchema(ClienteSchema):
    """Schema para atualização de cliente - todos os campos opcionais."""

    email = fields.Email()
    tipo_pessoa = fields.Str(validate=validate.OneOf(["FISICA", "JURIDICA"]))


class ClienteListSchema(Schema):
    """Schema simplificado para listagem de clientes."""

    id = fields.Int()
    tipo_pessoa = fields.Str()
    email = fields.Email()
    nome_completo_formatado = fields.Str()
    telefone_celular = fields.Str()
    endereco_formatado = fields.Str()
