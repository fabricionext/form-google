import datetime
import enum

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db  # Importa diretamente da raiz do projeto

# Ajuste o import de 'db' conforme a estrutura do seu projeto.
# Exemplo: from app import db
# Se o seu db estiver em app.extensions, por exemplo:


class User(UserMixin, db.Model):
    __tablename__ = "users_peticionador"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class TipoPessoaEnum(enum.Enum):
    FISICA = "Pessoa Física"
    JURIDICA = "Pessoa Jurídica"


class Cliente(db.Model):
    __tablename__ = "clientes_peticionador"

    id = db.Column(db.Integer, primary_key=True)
    tipo_pessoa = db.Column(db.Enum(TipoPessoaEnum), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    telefone_celular = db.Column(db.String(32))
    # Pessoa Física
    nome_completo = db.Column(db.String(128))
    cpf = db.Column(db.String(14), unique=True)
    # Pessoa Jurídica
    razao_social = db.Column(db.String(128))
    cnpj = db.Column(db.String(18), unique=True)
    representante_nome = db.Column(db.String(128))

    def __repr__(self):
        return f"<Cliente {self.nome_completo or self.razao_social}>"


class AutoridadeTransito(db.Model):
    __tablename__ = "autoridades_transito"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)
    cnpj = db.Column(db.String(18), nullable=True)
    logradouro = db.Column(db.String(255), nullable=True)
    numero = db.Column(db.String(50), nullable=True)
    complemento = db.Column(db.String(100), nullable=True)
    cidade = db.Column(db.String(100), nullable=True)
    estado = db.Column(db.String(2), nullable=True)
    cep = db.Column(db.String(9), nullable=True)

    def __repr__(self):
        return f"<AutoridadeTransito {self.nome}>"


# --- Novos Modelos para gerenciamento de templates de petição ---
class PeticaoModelo(db.Model):
    __tablename__ = "peticao_modelos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    doc_template_id = db.Column(db.String(64), nullable=False)  # ID do Google Docs
    pasta_destino_id = db.Column(db.String(64), nullable=False)  # ID da pasta no Drive
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<PeticaoModelo {self.nome}>"


class PeticaoPlaceholder(db.Model):
    __tablename__ = "peticao_placeholders"

    id = db.Column(db.Integer, primary_key=True)
    modelo_id = db.Column(
        db.Integer, db.ForeignKey("peticao_modelos.id"), nullable=False
    )
    chave = db.Column(db.String(64), nullable=False)  # ex.: {{processo_numero}}
    tipo_campo = db.Column(db.String(20), nullable=False, default="string")
    label_form = db.Column(db.String(120))
    opcoes_json = db.Column(db.Text)  # Para campos select/radio
    ordem = db.Column(db.Integer, default=0)
    obrigatorio = db.Column(db.Boolean, default=True)

    modelo = db.relationship(
        "PeticaoModelo",
        backref=db.backref("placeholders", lazy=True, cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<Placeholder {self.chave} ({self.modelo_id})>"


class PeticaoGerada(db.Model):
    """Histórico de documentos gerados pelo Peticionador."""

    __tablename__ = "peticoes_geradas"

    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(
        db.Integer, db.ForeignKey("clientes_peticionador.id"), nullable=True
    )  # Tornado opcional
    modelo = db.Column(db.String(120), nullable=False)
    google_id = db.Column(db.String(64), nullable=False)
    link = db.Column(db.String(255))
    criado_em = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationship (opcional, lazy='joined' para facilitar queries)
    cliente = db.relationship("Cliente", backref=db.backref("peticoes", lazy=True))

    def __repr__(self):
        return f"<PeticaoGerada {self.modelo} - {self.cliente_id}>"
