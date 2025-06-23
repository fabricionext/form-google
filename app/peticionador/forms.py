from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    HiddenField,
    IntegerField,
    PasswordField,
    RadioField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    Regexp,
)
from wtforms_sqlalchemy.fields import QuerySelectField

from .models import (  # Importa AutoridadeTransito do peticionador.models
    AutoridadeTransito,
    Cliente,
)


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(message="Endereço de email inválido.")],
    )
    password = PasswordField(
        "Senha", validators=[DataRequired(message="Senha é obrigatória.")]
    )
    remember_me = BooleanField("Lembrar-me")
    submit = SubmitField("Login")


class AutoridadeTransitoForm(FlaskForm):
    nome = StringField(
        "Nome da Autoridade",
        validators=[DataRequired(message="Nome é obrigatório."), Length(max=255)],
    )
    cnpj = StringField(
        "CNPJ",
        validators=[Length(max=18, message="CNPJ deve ter no máximo 18 caracteres.")],
    )
    logradouro = StringField("Logradouro", validators=[Length(max=255)])
    numero = StringField("Número", validators=[Length(max=50)])
    complemento = StringField("Complemento", validators=[Length(max=100)])
    cidade = StringField("Cidade", validators=[Length(max=100)])
    estado = StringField(
        "Estado (UF)",
        validators=[
            Length(min=2, max=2, message="Estado deve ser a sigla UF com 2 caracteres.")
        ],
    )
    cep = StringField(
        "CEP",
        validators=[Length(max=9, message="CEP deve ter no máximo 9 caracteres.")],
    )
    submit = SubmitField("Salvar Autoridade")


class ClienteForm(FlaskForm):
    tipo_pessoa = RadioField(
        "Tipo de Pessoa",
        choices=[("FISICA", "Pessoa Física"), ("JURIDICA", "Pessoa Jurídica")],
        validators=[DataRequired(message="Selecione o tipo de pessoa.")],
    )

    # Campos Comuns
    email = StringField(
        "E-mail",
        validators=[Optional(), Email(message="E-mail inválido."), Length(max=128)],
    )
    telefone_celular = StringField(
        "Telefone Celular", validators=[Optional(), Length(max=32)]
    )
    telefone_outro = StringField(
        "Outro Telefone", validators=[Optional(), Length(max=32)]
    )

    endereco_logradouro = StringField(
        "Logradouro", validators=[Optional(), Length(max=128)]
    )
    endereco_numero = StringField("Número", validators=[Optional(), Length(max=16)])
    endereco_complemento = StringField(
        "Complemento", validators=[Optional(), Length(max=64)]
    )
    endereco_bairro = StringField("Bairro", validators=[Optional(), Length(max=64)])
    endereco_cidade = StringField("Cidade", validators=[Optional(), Length(max=64)])
    endereco_estado = SelectField(
        "UF",
        choices=[
            ("", "Selecione..."),
            ("AC", "AC"),
            ("AL", "AL"),
            ("AP", "AP"),
            ("AM", "AM"),
            ("BA", "BA"),
            ("CE", "CE"),
            ("DF", "DF"),
            ("ES", "ES"),
            ("GO", "GO"),
            ("MA", "MA"),
            ("MT", "MT"),
            ("MS", "MS"),
            ("MG", "MG"),
            ("PA", "PA"),
            ("PB", "PB"),
            ("PR", "PR"),
            ("PE", "PE"),
            ("PI", "PI"),
            ("RJ", "RJ"),
            ("RN", "RN"),
            ("RS", "RS"),
            ("RO", "RO"),
            ("RR", "RR"),
            ("SC", "SC"),
            ("SP", "SP"),
            ("SE", "SE"),
            ("TO", "TO"),
        ],
        validators=[Optional()],
    )
    endereco_cep = StringField("CEP", validators=[Optional(), Length(max=16)])

    # Campos Pessoa Física
    primeiro_nome = StringField(
        "Primeiro Nome", validators=[Optional(), Length(max=64)]
    )
    sobrenome = StringField("Sobrenome", validators=[Optional(), Length(max=128)])
    nacionalidade = StringField(
        "Nacionalidade", validators=[Optional(), Length(max=32)]
    )
    rg_numero = StringField("RG", validators=[Optional(), Length(max=32)])
    rg_orgao_emissor = StringField(
        "Órgão Emissor do RG", validators=[Optional(), Length(max=32)]
    )
    rg_uf_emissor = SelectField(
        "UF Emissor do RG",
        choices=[
            ("", "Selecione..."),
            ("AC", "AC"),
            ("AL", "AL"),
            ("AP", "AP"),
            ("AM", "AM"),
            ("BA", "BA"),
            ("CE", "CE"),
            ("DF", "DF"),
            ("ES", "ES"),
            ("GO", "GO"),
            ("MA", "MA"),
            ("MT", "MT"),
            ("MS", "MS"),
            ("MG", "MG"),
            ("PA", "PA"),
            ("PB", "PB"),
            ("PR", "PR"),
            ("PE", "PE"),
            ("PI", "PI"),
            ("RJ", "RJ"),
            ("RN", "RN"),
            ("RS", "RS"),
            ("RO", "RO"),
            ("RR", "RR"),
            ("SC", "SC"),
            ("SP", "SP"),
            ("SE", "SE"),
            ("TO", "TO"),
        ],
        validators=[Optional()],
    )
    estado_civil = SelectField(
        "Estado Civil",
        choices=[
            ("", "Selecione..."),
            ("SOLTEIRO", "Solteiro(a)"),
            ("CASADO", "Casado(a)"),
            ("DIVORCIADO", "Divorciado(a)"),
            ("VIUVO", "Viúvo(a)"),
            ("UNIAO_ESTAVEL", "União Estável"),
            ("OUTRO", "Outro"),
        ],
        validators=[Optional()],
    )
    cpf = StringField(
        "CPF",
        validators=[
            Optional(),
            Regexp(
                r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
                message="CPF inválido. Use o formato XXX.XXX.XXX-XX.",
            ),
        ],
    )
    profissao = StringField("Profissão", validators=[Optional(), Length(max=64)])
    cnh_numero = StringField("CNH", validators=[Optional(), Length(max=32)])
    data_nascimento = DateField(
        "Data de Nascimento", format="%Y-%m-%d", validators=[Optional()]
    )

    # Campos Pessoa Jurídica
    razao_social = StringField("Razão Social", validators=[Optional(), Length(max=128)])
    cnpj = StringField(
        "CNPJ",
        validators=[
            Optional(),
            Regexp(
                r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$",
                message="CNPJ inválido. Use o formato XX.XXX.XXX/XXXX-XX.",
            ),
        ],
    )

    # Representante Legal (da PJ)
    representante_nome = StringField(
        "Nome do Representante Legal", validators=[Optional(), Length(max=128)]
    )
    representante_cpf = StringField(
        "CPF do Representante",
        validators=[
            Optional(),
            Regexp(
                r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
                message="CPF do representante inválido. Use o formato XXX.XXX.XXX-XX.",
            ),
        ],
    )
    representante_rg_numero = StringField(
        "RG do Representante", validators=[Optional(), Length(max=32)]
    )
    representante_rg_orgao_emissor = StringField(
        "Órgão Emissor do RG do Representante", validators=[Optional(), Length(max=32)]
    )
    representante_rg_uf_emissor = SelectField(
        "UF Emissor do RG do Representante",
        choices=[
            ("", "Selecione..."),
            ("AC", "AC"),
            ("AL", "AL"),
            ("AP", "AP"),
            ("AM", "AM"),
            ("BA", "BA"),
            ("CE", "CE"),
            ("DF", "DF"),
            ("ES", "ES"),
            ("GO", "GO"),
            ("MA", "MA"),
            ("MT", "MT"),
            ("MS", "MS"),
            ("MG", "MG"),
            ("PA", "PA"),
            ("PB", "PB"),
            ("PR", "PR"),
            ("PE", "PE"),
            ("PI", "PI"),
            ("RJ", "RJ"),
            ("RN", "RN"),
            ("RS", "RS"),
            ("RO", "RO"),
            ("RR", "RR"),
            ("SC", "SC"),
            ("SP", "SP"),
            ("SE", "SE"),
            ("TO", "TO"),
        ],
        validators=[Optional()],
    )
    representante_cargo = StringField(
        "Cargo do Representante", validators=[Optional(), Length(max=64)]
    )

    submit = SubmitField("Salvar Cliente")


def cliente_query():
    # Retorna todos os clientes ordenados pelo nome completo ou razão social
    return Cliente.query.order_by(Cliente.primeiro_nome, Cliente.razao_social).all()


def autoridade_transito_query():
    return AutoridadeTransito.query.order_by(AutoridadeTransito.nome).all()


class PeticaoModeloForm(FlaskForm):
    nome = StringField("Nome do Modelo", validators=[DataRequired(), Length(max=150)])
    doc_template_id = StringField(
        "ID do Documento Google", validators=[DataRequired(), Length(max=64)]
    )
    pasta_destino_id = StringField(
        "ID da Pasta de Destino", validators=[DataRequired(), Length(max=64)]
    )
    descricao = TextAreaField("Descrição", validators=[Optional(), Length(max=1000)])
    ativo = BooleanField("Ativo", default=True)
    submit = SubmitField("Salvar Modelo")


class DocumentTemplateForm(FlaskForm):
    """Formulário para edição de IDs de templates."""

    tipo_pessoa = SelectField(
        "Tipo de Pessoa",
        choices=[("pf", "PF"), ("pj", "PJ"), ("pet", "PET")],
        validators=[DataRequired()],
    )
    nome = StringField(
        "Nome do Documento", validators=[DataRequired(), Length(max=150)]
    )
    template_id = StringField(
        "ID do Template", validators=[DataRequired(), Length(max=64)]
    )
    submit = SubmitField("Salvar")


class GerarDocumentoSuspensaoForm(FlaskForm):
    # Campo para busca de CPF
    cpf_busca = StringField(
        "CPF do Cliente para Busca",
        validators=[
            Optional(),
            Regexp(
                r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
                message="CPF inválido. Use o formato XXX.XXX.XXX-XX.",
            ),
        ],
    )

    # Campos do Cliente (para exibir/editar após busca)
    cliente_id = HiddenField()
    cliente_primeiro_nome = StringField(
        "Primeiro Nome", validators=[Optional(), Length(max=64)]
    )
    cliente_sobrenome = StringField(
        "Sobrenome", validators=[Optional(), Length(max=128)]
    )
    cliente_email = StringField(
        "E-mail",
        validators=[Optional(), Email(message="E-mail inválido."), Length(max=128)],
    )
    cliente_telefone_celular = StringField(
        "Telefone Celular", validators=[Optional(), Length(max=32)]
    )
    cliente_endereco_logradouro = StringField(
        "Logradouro", validators=[Optional(), Length(max=128)]
    )
    cliente_endereco_numero = StringField(
        "Número", validators=[Optional(), Length(max=16)]
    )
    cliente_endereco_complemento = StringField(
        "Complemento", validators=[Optional(), Length(max=64)]
    )
    cliente_endereco_bairro = StringField(
        "Bairro", validators=[Optional(), Length(max=64)]
    )
    cliente_endereco_cidade = StringField(
        "Cidade", validators=[Optional(), Length(max=64)]
    )
    cliente_endereco_estado = SelectField(
        "UF",
        choices=[
            ("", "Selecione..."),
            ("AC", "AC"),
            ("AL", "AL"),
            ("AP", "AP"),
            ("AM", "AM"),
            ("BA", "BA"),
            ("CE", "CE"),
            ("DF", "DF"),
            ("ES", "ES"),
            ("GO", "GO"),
            ("MA", "MA"),
            ("MT", "MT"),
            ("MS", "MS"),
            ("MG", "MG"),
            ("PA", "PA"),
            ("PB", "PB"),
            ("PR", "PR"),
            ("PE", "PE"),
            ("PI", "PI"),
            ("RJ", "RJ"),
            ("RN", "RN"),
            ("RS", "RS"),
            ("RO", "RO"),
            ("RR", "RR"),
            ("SC", "SC"),
            ("SP", "SP"),
            ("SE", "SE"),
            ("TO", "TO"),
        ],
        validators=[Optional()],
    )
    cliente_endereco_cep = StringField("CEP", validators=[Optional(), Length(max=16)])
    cliente_cpf = StringField(
        "CPF Cliente (para confirmação/edição)",
        validators=[
            Optional(),
            Regexp(
                r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
                message="CPF inválido. Use o formato XXX.XXX.XXX-XX.",
            ),
        ],
    )  # Para exibir/editar o CPF que foi buscado
    cliente_rg_numero = StringField("RG", validators=[Optional(), Length(max=32)])
    cliente_cnh_numero = StringField("CNH", validators=[Optional(), Length(max=32)])

    # Campos específicos da Petição de Suspensão
    numero_processo_adm = StringField(
        "Número do Processo Administrativo",
        validators=[
            DataRequired(message="Número do processo é obrigatório."),
            Length(max=50),
        ],
    )
    auto_infracao = StringField(
        "Auto de Infração (Opcional)", validators=[Optional(), Length(max=50)]
    )
    autoridade_transito = QuerySelectField(
        "Autoridade de Trânsito Notificadora",
        query_factory=autoridade_transito_query,
        get_label="nome",
        allow_blank=False,
        validators=[DataRequired(message="Selecione a autoridade de trânsito.")],
    )
    data_notificacao = DateField(
        "Data da Notificação da Penalidade",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Data da notificação é obrigatória.")],
    )
    pontos_cnh = IntegerField(
        "Quantidade de Pontos na CNH (se aplicável)",
        validators=[
            Optional(),
            NumberRange(min=0, message="Pontos devem ser um número positivo."),
        ],
    )
    observacoes_adicionais = TextAreaField(
        "Observações Adicionais (Opcional)", validators=[Optional(), Length(max=1000)]
    )

    # submit = SubmitField('Gerar Documento de Suspensão') # O botão será definido no template com name='action'
