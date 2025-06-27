"""
Modelo de Client para o sistema peticionador.
"""

from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Text, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.models.base import BaseModel
from app.config.constants import MAX_CLIENT_NAME_LENGTH


class TipoPessoaEnum(enum.Enum):
    """Enum para tipo de pessoa."""
    FISICA = "Pessoa Física"
    JURIDICA = "Pessoa Jurídica"


class Client(BaseModel):
    """Modelo para clientes do sistema."""
    
    __tablename__ = "clients"
    
    # Identificação básica
    tipo_pessoa = Column(Enum(TipoPessoaEnum), nullable=False)
    email = Column(String(128), unique=True, nullable=False, index=True)
    
    # Telefones
    telefone_celular = Column(String(32))
    telefone_outro = Column(String(32))
    
    # Pessoa Física
    nome_completo = Column(String(MAX_CLIENT_NAME_LENGTH))
    cpf = Column(String(14), unique=True, index=True)
    rg = Column(String(20))
    data_nascimento = Column(DateTime)
    nacionalidade = Column(String(50))
    estado_civil = Column(String(30))
    profissao = Column(String(100))
    
    # Pessoa Jurídica
    razao_social = Column(String(200))
    nome_fantasia = Column(String(200))
    cnpj = Column(String(18), unique=True, index=True)
    inscricao_estadual = Column(String(20))
    
    # Endereço
    endereco_cep = Column(String(10))
    endereco_logradouro = Column(String(200))
    endereco_numero = Column(String(20))
    endereco_complemento = Column(String(100))
    endereco_bairro = Column(String(100))
    endereco_cidade = Column(String(100))
    endereco_estado = Column(String(2))
    
    # Dados adicionais
    observacoes = Column(Text)
    data_registro = Column(DateTime, default=datetime.utcnow)
    
    # Status
    ativo = Column(Boolean, default=True, nullable=False)
    
    # Relacionamentos
    documents = relationship("Document", back_populates="client", lazy="select")
    
    def to_dict(self, include_documents: bool = False, exclude: list = None) -> Dict[str, Any]:
        """
        Converte cliente para dicionário.
        
        Args:
            include_documents: Se deve incluir documentos
            exclude: Campos para excluir
            
        Returns:
            Dicionário com dados do cliente
        """
        data = super().to_dict(exclude)
        
        # Converte enum para string
        if self.tipo_pessoa:
            data['tipo_pessoa'] = self.tipo_pessoa.value
        
        # Formata datas
        if self.data_nascimento:
            data['data_nascimento'] = self.data_nascimento.strftime('%d/%m/%Y')
        
        if self.data_registro:
            data['data_registro'] = self.data_registro.strftime('%d/%m/%Y %H:%M')
        
        # Adiciona nome de exibição
        data['nome_display'] = self.get_nome_display()
        
        # Adiciona documento principal (CPF ou CNPJ)
        data['documento_principal'] = self.get_documento_principal()
        
        if include_documents:
            data['documents'] = [doc.to_dict() for doc in self.documents]
        else:
            data['documents_count'] = len(self.documents)
        
        return data
    
    def get_nome_display(self) -> str:
        """
        Retorna nome para exibição.
        
        Returns:
            Nome completo para PF ou razão social para PJ
        """
        if self.tipo_pessoa == TipoPessoaEnum.FISICA:
            return self.nome_completo or "Cliente sem nome"
        else:
            return self.razao_social or self.nome_fantasia or "Empresa sem nome"
    
    def get_documento_principal(self) -> Optional[str]:
        """
        Retorna documento principal (CPF ou CNPJ).
        
        Returns:
            CPF para PF ou CNPJ para PJ
        """
        if self.tipo_pessoa == TipoPessoaEnum.FISICA:
            return self.cpf
        else:
            return self.cnpj
    
    def get_endereco_completo(self) -> str:
        """
        Retorna endereço completo formatado.
        
        Returns:
            String com endereço completo
        """
        parts = []
        
        if self.endereco_logradouro:
            logradouro = self.endereco_logradouro
            if self.endereco_numero:
                logradouro += f", {self.endereco_numero}"
            if self.endereco_complemento:
                logradouro += f", {self.endereco_complemento}"
            parts.append(logradouro)
        
        if self.endereco_bairro:
            parts.append(self.endereco_bairro)
        
        if self.endereco_cidade and self.endereco_estado:
            parts.append(f"{self.endereco_cidade}/{self.endereco_estado}")
        
        if self.endereco_cep:
            parts.append(f"CEP: {self.endereco_cep}")
        
        return " - ".join(parts)
    
    def is_pessoa_fisica(self) -> bool:
        """Verifica se é pessoa física."""
        return self.tipo_pessoa == TipoPessoaEnum.FISICA
    
    def is_pessoa_juridica(self) -> bool:
        """Verifica se é pessoa jurídica."""
        return self.tipo_pessoa == TipoPessoaEnum.JURIDICA
    
    def validate_required_fields(self) -> tuple[bool, list]:
        """
        Valida campos obrigatórios baseado no tipo de pessoa.
        
        Returns:
            Tupla (is_valid, error_messages)
        """
        errors = []
        
        # Campos comuns
        if not self.email:
            errors.append("Email é obrigatório")
        
        if not self.tipo_pessoa:
            errors.append("Tipo de pessoa é obrigatório")
        
        # Campos específicos para Pessoa Física
        if self.tipo_pessoa == TipoPessoaEnum.FISICA:
            if not self.nome_completo:
                errors.append("Nome completo é obrigatório para pessoa física")
            if not self.cpf:
                errors.append("CPF é obrigatório para pessoa física")
        
        # Campos específicos para Pessoa Jurídica
        elif self.tipo_pessoa == TipoPessoaEnum.JURIDICA:
            if not self.razao_social:
                errors.append("Razão social é obrigatória para pessoa jurídica")
            if not self.cnpj:
                errors.append("CNPJ é obrigatório para pessoa jurídica")
        
        return len(errors) == 0, errors
    
    def format_cpf(self) -> Optional[str]:
        """
        Formata CPF com máscara.
        
        Returns:
            CPF formatado ou None
        """
        if not self.cpf:
            return None
        
        cpf = self.cpf.replace('.', '').replace('-', '')
        if len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        
        return self.cpf
    
    def format_cnpj(self) -> Optional[str]:
        """
        Formata CNPJ com máscara.
        
        Returns:
            CNPJ formatado ou None
        """
        if not self.cnpj:
            return None
        
        cnpj = self.cnpj.replace('.', '').replace('/', '').replace('-', '')
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        
        return self.cnpj
    
    def deactivate(self) -> None:
        """Desativa cliente (soft delete)."""
        self.ativo = False
        self.save()
    
    def activate(self) -> None:
        """Ativa cliente."""
        self.ativo = True
        self.save()
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional['Client']:
        """
        Busca cliente por email.
        
        Args:
            email: Email do cliente
            
        Returns:
            Cliente ou None
        """
        return cls.query.filter_by(email=email, ativo=True).first()
    
    @classmethod
    def find_by_cpf(cls, cpf: str) -> Optional['Client']:
        """
        Busca cliente por CPF.
        
        Args:
            cpf: CPF do cliente
            
        Returns:
            Cliente ou None
        """
        # Remove formatação
        cpf_clean = cpf.replace('.', '').replace('-', '')
        return cls.query.filter_by(cpf=cpf_clean, ativo=True).first()
    
    @classmethod
    def find_by_cnpj(cls, cnpj: str) -> Optional['Client']:
        """
        Busca cliente por CNPJ.
        
        Args:
            cnpj: CNPJ do cliente
            
        Returns:
            Cliente ou None
        """
        # Remove formatação
        cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '')
        return cls.query.filter_by(cnpj=cnpj_clean, ativo=True).first()
    
    @classmethod
    def find_active(cls) -> list:
        """
        Retorna todos os clientes ativos.
        
        Returns:
            Lista de clientes ativos
        """
        return cls.query.filter_by(ativo=True).order_by(cls.nome_completo, cls.razao_social).all()
    
    @classmethod
    def search_by_name(cls, search_term: str) -> list:
        """
        Busca clientes por nome.
        
        Args:
            search_term: Termo de busca
            
        Returns:
            Lista de clientes que coincidem
        """
        search_pattern = f"%{search_term}%"
        return cls.query.filter(
            cls.ativo == True,
            (cls.nome_completo.ilike(search_pattern) | 
             cls.razao_social.ilike(search_pattern) |
             cls.nome_fantasia.ilike(search_pattern))
        ).order_by(cls.nome_completo, cls.razao_social).all()
    
    def __repr__(self) -> str:
        """Representação string do cliente."""
        name = self.get_nome_display()
        return f"<Client(id={self.id}, name='{name}', type='{self.tipo_pessoa.value if self.tipo_pessoa else 'N/A'}')>"