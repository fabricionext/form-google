# Standard library imports

# Third party imports
from marshmallow import Schema, fields, validate


class PeticaoModeloSchema(Schema):
    """Schema para validação de dados do PeticaoModelo."""

    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True, validate=validate.Length(min=3, max=150))
    slug = fields.Str(required=True, validate=validate.Length(min=3, max=150))
    google_doc_id = fields.Str(required=True, validate=validate.Length(max=64))
    doc_template_id = fields.Str(validate=validate.Length(max=64))
    pasta_destino_id = fields.Str(required=True, validate=validate.Length(max=64))
    descricao = fields.Str()
    ativo = fields.Bool(load_default=True)
    criado_em = fields.DateTime(dump_only=True)
    atualizado_em = fields.DateTime(dump_only=True)
    total_placeholders = fields.Int(load_default=0)
    total_personas = fields.Int(load_default=0)
    ultima_sincronizacao = fields.DateTime()


class FormularioPlaceholderSchema(Schema):
    """Schema para validação de FormularioPlaceholder."""

    id = fields.Int(dump_only=True)
    modelo_id = fields.Int(required=True)
    chave = fields.Str(required=True, validate=validate.Length(max=128))
    categoria = fields.Str(
        validate=validate.OneOf(
            [
                "cliente",
                "endereco",
                "processo",
                "polo_ativo",
                "polo_passivo",
                "terceiros",
                "autoridade",
                "outros",
            ]
        ),
        load_default="outros",
    )
    tipo_campo = fields.Str(
        validate=validate.OneOf(["text", "email", "tel", "date", "textarea", "select"]),
        load_default="text",
    )
    label = fields.Str(required=True, validate=validate.Length(max=150))
    placeholder_text = fields.Str(validate=validate.Length(max=200))
    obrigatorio = fields.Bool(load_default=False)
    opcoes_json = fields.Str()  # JSON string for select/radio options
    ordem = fields.Int(load_default=0)
    ativo = fields.Bool(load_default=True)
    criado_em = fields.DateTime(dump_only=True)


class FormularioGeradoSchema(Schema):
    """Schema para validação de FormularioGerado."""

    id = fields.Int(dump_only=True)
    modelo_id = fields.Int(required=True)
    nome = fields.Str(required=True, validate=validate.Length(max=150))
    slug = fields.Str(required=True, validate=validate.Length(max=150))
    criado_em = fields.DateTime(dump_only=True)

    # Relacionamento
    modelo = fields.Nested(PeticaoModeloSchema, dump_only=True)


class FormularioSchema(Schema):
    """Schema principal para validação de formulários dinâmicos."""

    modelo_slug = fields.Str(required=True)
    dados_formulario = fields.Dict(required=True)

    # Campos específicos do formulário
    nome_documento = fields.Str(validate=validate.Length(min=3, max=150))
    observacoes = fields.Str()


class FormularioSubmissionSchema(Schema):
    """Schema para submissão de formulário preenchido."""

    modelo_id = fields.Int(required=True)
    dados_cliente = fields.Dict(required=True)
    dados_formulario = fields.Dict(required=True)
    tipo_pessoa = fields.Str(required=True, validate=validate.OneOf(["pf", "pj"]))
    documentos_requeridos = fields.List(fields.Str())


class PeticaoModeloListSchema(Schema):
    """Schema simplificado para listagem de modelos."""

    id = fields.Int()
    nome = fields.Str()
    slug = fields.Str()
    descricao = fields.Str()
    ativo = fields.Bool()
    total_placeholders = fields.Int()
    total_personas = fields.Int()
    criado_em = fields.DateTime()


class FormularioValidationErrorSchema(Schema):
    """Schema para retorno de erros de validação."""

    field = fields.Str(required=True)
    message = fields.Str(required=True)
    invalid_value = fields.Raw()


class FormularioResponseSchema(Schema):
    """Schema para resposta de processamento de formulário."""

    success = fields.Bool(required=True)
    message = fields.Str(required=True)
    data = fields.Dict()
    errors = fields.List(fields.Nested(FormularioValidationErrorSchema))
    document_url = fields.Str()
    redirect_url = fields.Str()
