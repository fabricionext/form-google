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
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

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
    telefone_outro = db.Column(db.String(32))
    
    # Pessoa Física - Campos expandidos
    primeiro_nome = db.Column(db.String(64))
    sobrenome = db.Column(db.String(128))
    nome_completo = db.Column(db.String(192))
    cpf = db.Column(db.String(14), unique=True)
    rg_numero = db.Column(db.String(32))
    rg_orgao_emissor = db.Column(db.String(32))
    rg_uf_emissor = db.Column(db.String(2))
    data_nascimento = db.Column(db.Date)
    nacionalidade = db.Column(db.String(32))
    estado_civil = db.Column(db.String(20))  # NOVO CAMPO
    profissao = db.Column(db.String(64))  # NOVO CAMPO
    cnh_numero = db.Column(db.String(32))  # NOVO CAMPO
    
    # Endereço
    endereco_logradouro = db.Column(db.String(128))
    endereco_numero = db.Column(db.String(16))
    endereco_complemento = db.Column(db.String(64))
    endereco_bairro = db.Column(db.String(64))
    endereco_cidade = db.Column(db.String(64))
    endereco_estado = db.Column(db.String(2))
    endereco_cep = db.Column(db.String(16))
    
    # Pessoa Jurídica
    razao_social = db.Column(db.String(128))
    cnpj = db.Column(db.String(18), unique=True)
    representante_nome = db.Column(db.String(128))
    representante_cpf = db.Column(db.String(14))
    representante_rg_numero = db.Column(db.String(32))
    representante_rg_orgao_emissor = db.Column(db.String(32))
    representante_rg_uf_emissor = db.Column(db.String(2))
    representante_cargo = db.Column(db.String(64))

    @property
    def nome_completo_formatado(self):
        """Retorna nome completo formatado baseado no tipo de pessoa"""
        if self.tipo_pessoa == TipoPessoaEnum.JURIDICA:
            return self.razao_social or ""
        return f"{self.primeiro_nome or ''} {self.sobrenome or ''}".strip()
    
    @property
    def endereco_formatado(self):
        """Retorna endereço completo formatado"""
        parts = [
            self.endereco_logradouro,
            self.endereco_numero,
            self.endereco_complemento,
            self.endereco_bairro,
        ]
        endereco_base = ", ".join(filter(None, parts))
        
        if self.endereco_cidade and self.endereco_estado:
            cidade_uf = f"{self.endereco_cidade}/{self.endereco_estado}"
            if endereco_base:
                endereco_base += f" - {cidade_uf}"
            else:
                endereco_base = cidade_uf
        
        if self.endereco_cep:
            if endereco_base:
                endereco_base += f" - CEP: {self.endereco_cep}"
            else:
                endereco_base = f"CEP: {self.endereco_cep}"
        
        return endereco_base.strip(" ,-")
    
    @property
    def documento_principal(self):
        """Retorna CPF ou CNPJ baseado no tipo de pessoa"""
        if self.tipo_pessoa == TipoPessoaEnum.JURIDICA:
            return self.cnpj or ""
        return self.cpf or ""
    
    @property
    def telefone_principal(self):
        """Retorna telefone principal ou alternativo"""
        return self.telefone_celular or self.telefone_outro or ""

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
    slug = db.Column(db.String(150), unique=True, nullable=False)
    google_doc_id = db.Column(db.String(64), nullable=False)  # ID do Google Docs (renomeado para consistência)
    doc_template_id = db.Column(db.String(64), nullable=True)  # Mantido para compatibilidade
    pasta_destino_id = db.Column(db.String(64), nullable=False)  # ID da pasta no Drive
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Campos para análise de personas
    total_placeholders = db.Column(db.Integer, default=0)
    total_personas = db.Column(db.Integer, default=0)
    ultima_sincronizacao = db.Column(db.DateTime)

    def to_dict(self):
        """Converte o objeto em um dicionário serializável."""
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "total_placeholders": self.total_placeholders,
            "total_personas": self.total_personas,
            "ultima_sincronizacao": self.ultima_sincronizacao.isoformat() if self.ultima_sincronizacao else None,
        }
    
    def __json__(self):
        """Método para serialização JSON automática."""
        return self.to_dict()
    
    def to_json_safe(self):
        """Versão mais robusta para serialização JSON."""
        try:
            return {
                "id": self.id or 0,
                "nome": self.nome or "",
                "descricao": self.descricao or "",
                "total_placeholders": self.total_placeholders or 0,
                "total_personas": self.total_personas or 0,
                "ultima_sincronizacao": self.ultima_sincronizacao.isoformat() if self.ultima_sincronizacao else None,
                "ativo": self.ativo if hasattr(self, 'ativo') else True
            }
        except Exception:
            return {"id": 0, "nome": "Modelo Indisponível", "descricao": "", "total_placeholders": 0, "total_personas": 0, "ultima_sincronizacao": None, "ativo": True}

    def __repr__(self):
        return f"<PeticaoModelo {self.nome}>"


# Placeholder para formulários dinâmicos (novo sistema)
class FormularioPlaceholder(db.Model):
    __tablename__ = "formulario_placeholders"

    id = db.Column(db.Integer, primary_key=True)
    modelo_id = db.Column(db.Integer, db.ForeignKey("peticao_modelos.id"), nullable=False)
    chave = db.Column(db.String(128), nullable=False)  # ex.: autor_1_nome, reu_2_cpf
    categoria = db.Column(db.String(32), nullable=False, default="outros")  # cliente, endereco, processo, polo_ativo, polo_passivo, terceiros, autoridade
    tipo_campo = db.Column(db.String(20), nullable=False, default="text")  # text, email, tel, date, textarea, select
    label = db.Column(db.String(150), nullable=False)
    placeholder_text = db.Column(db.String(200))
    obrigatorio = db.Column(db.Boolean, default=False)
    opcoes_json = db.Column(db.Text)  # Para campos select/radio (JSON)
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    modelo = db.relationship(
        "PeticaoModelo",
        backref=db.backref("formulario_placeholders", lazy=True, cascade="all, delete-orphan"),
    )

    def __repr__(self):
        return f"<FormularioPlaceholder {self.chave} ({self.categoria})>"


# Placeholder legado (mantido para compatibilidade)
class PeticaoPlaceholder(db.Model):
    __tablename__ = "peticao_placeholders"

    id = db.Column(db.Integer, primary_key=True)
    modelo_id = db.Column(
        db.Integer, db.ForeignKey("peticao_modelos.id"), nullable=False
    )
    chave = db.Column(db.String(64), nullable=False)  # ex.: {{processo_numero}}
    categoria = db.Column(db.String(32), nullable=False, default="outros")  # Nova categoria
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
        return f"<Placeholder {self.chave} ({self.categoria})>"


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


class DocumentTemplate(db.Model):
    """Armazena os IDs de templates de documentos Google."""

    __tablename__ = "document_templates"

    id = db.Column(db.Integer, primary_key=True)
    tipo_pessoa = db.Column(db.String(10), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    template_id = db.Column(db.String(64), nullable=False)

    def __repr__(self):
        return f"<DocumentTemplate {self.tipo_pessoa}:{self.nome}>"


class FormularioGerado(db.Model):
    """Modelo para formulários gerados dinamicamente."""
    
    __tablename__ = "formularios_gerados"
    
    id = db.Column(db.Integer, primary_key=True)
    modelo_id = db.Column(db.Integer, db.ForeignKey("peticao_modelos.id"), nullable=False)
    nome = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    modelo = db.relationship(
        "PeticaoModelo", 
        backref=db.backref("formularios_gerados", lazy=True)
    )

    def to_dict(self):
        return {
            'id': self.id,
            'modelo_id': self.modelo_id,
            'nome': self.nome,
            'slug': self.slug,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'modelo': self.modelo.to_dict() if self.modelo else None
        }

    def __repr__(self):
        return f"<FormularioGerado {self.nome} ({self.modelo_id})>"


class PersonaAnalise(db.Model):
    """Modelo para armazenar análises de personas de documentos."""
    
    __tablename__ = "persona_analises"
    
    id = db.Column(db.Integer, primary_key=True)
    modelo_id = db.Column(db.Integer, db.ForeignKey("peticao_modelos.id"), nullable=False)
    documento_id = db.Column(db.String(64), nullable=False)  # ID do Google Docs
    personas_detectadas = db.Column(db.JSON)  # Dict com contagem de cada tipo de persona
    patterns_detectados = db.Column(db.JSON)  # Padrões encontrados
    total_placeholders = db.Column(db.Integer, default=0)
    total_personas = db.Column(db.Integer, default=0)
    sugestoes = db.Column(db.JSON)  # Sugestões geradas pelo sistema
    criado_em = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    modelo = db.relationship(
        "PeticaoModelo", 
        backref=db.backref("persona_analises", lazy=True, cascade="all, delete-orphan")
    )

    def __repr__(self):
        return f"<PersonaAnalise {self.modelo_id} - {self.total_personas} personas>"
