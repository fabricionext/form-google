"""
Modelo base para todos os modelos do sistema.
"""

from datetime import datetime
from typing import Dict, Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declared_attr, declarative_base

# Criar a base declarativa para SQLAlchemy
Base = declarative_base()

db = SQLAlchemy()


class BaseModel(db.Model):
    """Modelo base com campos comuns."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @declared_attr
    def __tablename__(cls):
        """Gera nome da tabela automaticamente."""
        return cls.__name__.lower()
    
    def to_dict(self, exclude: list = None) -> Dict[str, Any]:
        """
        Converte modelo para dicionário.
        
        Args:
            exclude: Lista de campos para excluir
            
        Returns:
            Dicionário com dados do modelo
        """
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: list = None) -> None:
        """
        Atualiza modelo a partir de dicionário.
        
        Args:
            data: Dicionário com dados
            exclude: Lista de campos para excluir
        """
        exclude = exclude or ['id', 'created_at']
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.utcnow()
    
    def save(self) -> 'BaseModel':
        """Salva modelo no banco de dados."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self) -> None:
        """Remove modelo do banco de dados."""
        db.session.delete(self)
        db.session.commit()
    
    @classmethod
    def find_by_id(cls, id: int) -> 'BaseModel':
        """
        Busca modelo por ID.
        
        Args:
            id: ID do modelo
            
        Returns:
            Instância do modelo ou None
        """
        return cls.query.filter_by(id=id).first()
    
    @classmethod
    def find_all(cls, **filters) -> list:
        """
        Busca todos os modelos com filtros opcionais.
        
        Args:
            **filters: Filtros para aplicar
            
        Returns:
            Lista de modelos
        """
        query = cls.query
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.filter(getattr(cls, key) == value)
        return query.all()
    
    @classmethod
    def count(cls, **filters) -> int:
        """
        Conta modelos com filtros opcionais.
        
        Args:
            **filters: Filtros para aplicar
            
        Returns:
            Número de registros
        """
        query = cls.query
        for key, value in filters.items():
            if hasattr(cls, key):
                query = query.filter(getattr(cls, key) == value)
        return query.count()
    
    def __repr__(self) -> str:
        """Representação string do modelo."""
        return f"<{self.__class__.__name__}(id={self.id})>"