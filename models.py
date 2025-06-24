from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

# Importa a instância única definida em extensions.py
from extensions import db


class RespostaForm(db.Model):
    __tablename__ = "respostas_form"
    id = Column(Integer, primary_key=True)
    timestamp_processamento = Column(DateTime, default=datetime.utcnow)
    submission_id = Column(String(64), unique=True, nullable=False)
    tipo_pessoa = Column(String(16))
    primeiro_nome = Column(String(64))
    sobrenome = Column(String(64))
    cpf = Column(String(32))
    data_nascimento = Column(String(16))
    rg = Column(String(32))
    estado_emissor_rg = Column(String(32))
    nacionalidade = Column(String(32))
    estado_civil = Column(String(32))
    profissao = Column(String(64))
    cnh = Column(String(32))
    razao_social = Column(String(128))
    cnpj = Column(String(32))
    nome_representante_legal = Column(String(128))
    cpf_representante_legal = Column(String(32))
    cargo_representante_legal = Column(String(64))
    cep = Column(String(16))
    # Campo legado: endereço completo em uma string
    endereco = Column(String(128))
    # Novos campos estruturados para endereço
    logradouro = Column(String(128))
    numero = Column(String(16))
    complemento = Column(String(64))
    bairro = Column(String(64))  # Bairro do endereço
    cidade = Column(String(64))
    uf_endereco = Column(String(32))
    telefone_celular = Column(String(32))
    outro_telefone = Column(String(32))
    email = Column(String(128))
    nome_cliente_pasta = Column(String(128))
    ids_arquivos_anexados = Column(String(256))
    link_pasta_cliente = Column(String(256))
    status_processamento = Column(String(64))
    observacoes_processamento = Column(Text)
