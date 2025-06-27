"""
Repository base para acesso a dados.
"""

from typing import TypeVar, Generic, List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.base import BaseModel, db
from app.utils.exceptions import PeticionadorException

ModelType = TypeVar('ModelType', bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Repository base com operações CRUD genéricas."""
    
    def __init__(self, model_class: type[ModelType], session: Session = None):
        """
        Inicializa repository.
        
        Args:
            model_class: Classe do modelo
            session: Sessão do SQLAlchemy (opcional)
        """
        self.model_class = model_class
        self.session = session or db.session
    
    def find_by_id(self, id: int) -> Optional[ModelType]:
        """
        Busca modelo por ID.
        
        Args:
            id: ID do modelo
            
        Returns:
            Instância do modelo ou None
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            return self.session.query(self.model_class).filter_by(id=id).first()
        except SQLAlchemyError as e:
            raise PeticionadorException(f"Erro ao buscar {self.model_class.__name__} por ID: {str(e)}")
    
    def find_all(self, **filters) -> List[ModelType]:
        """
        Busca todos os modelos com filtros opcionais.
        
        Args:
            **filters: Filtros para aplicar
            
        Returns:
            Lista de modelos
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            query = self.session.query(self.model_class)
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.all()
        except SQLAlchemyError as e:
            raise PeticionadorException(f"Erro ao buscar {self.model_class.__name__}: {str(e)}")
    
    def create(self, data: Dict[str, Any]) -> ModelType:
        """
        Cria novo modelo.
        
        Args:
            data: Dados para criar o modelo
            
        Returns:
            Instância criada
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            instance = self.model_class(**data)
            self.session.add(instance)
            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PeticionadorException(f"Erro ao criar {self.model_class.__name__}: {str(e)}")
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[ModelType]:
        """
        Atualiza modelo existente.
        
        Args:
            id: ID do modelo
            data: Dados para atualizar
            
        Returns:
            Instância atualizada ou None se não encontrada
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            instance = self.find_by_id(id)
            if not instance:
                return None
            
            instance.update_from_dict(data)
            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PeticionadorException(f"Erro ao atualizar {self.model_class.__name__}: {str(e)}")
    
    def delete(self, id: int) -> bool:
        """
        Remove modelo.
        
        Args:
            id: ID do modelo
            
        Returns:
            True se removido, False se não encontrado
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            instance = self.find_by_id(id)
            if not instance:
                return False
            
            self.session.delete(instance)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PeticionadorException(f"Erro ao deletar {self.model_class.__name__}: {str(e)}")
    
    def count(self, **filters) -> int:
        """
        Conta modelos com filtros opcionais.
        
        Args:
            **filters: Filtros para aplicar
            
        Returns:
            Número de registros
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            query = self.session.query(self.model_class)
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            return query.count()
        except SQLAlchemyError as e:
            raise PeticionadorException(f"Erro ao contar {self.model_class.__name__}: {str(e)}")
    
    def exists(self, **filters) -> bool:
        """
        Verifica se existe modelo com filtros.
        
        Args:
            **filters: Filtros para aplicar
            
        Returns:
            True se existe pelo menos um registro
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        return self.count(**filters) > 0
    
    def find_by_criteria(self, criteria: Dict[str, Any], 
                        order_by: str = None, 
                        limit: int = None, 
                        offset: int = None) -> List[ModelType]:
        """
        Busca modelos com critérios avançados.
        
        Args:
            criteria: Critérios de busca
            order_by: Campo para ordenação
            limit: Limite de registros
            offset: Offset para paginação
            
        Returns:
            Lista de modelos
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            query = self.session.query(self.model_class)
            
            # Aplica filtros
            for key, value in criteria.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            # Ordenação
            if order_by and hasattr(self.model_class, order_by):
                query = query.order_by(getattr(self.model_class, order_by))
            
            # Paginação
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            raise PeticionadorException(f"Erro ao buscar {self.model_class.__name__} com critérios: {str(e)}")
    
    def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[ModelType]:
        """
        Cria múltiplos modelos em lote.
        
        Args:
            data_list: Lista de dados para criar modelos
            
        Returns:
            Lista de instâncias criadas
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            instances = []
            for data in data_list:
                instance = self.model_class(**data)
                instances.append(instance)
                self.session.add(instance)
            
            self.session.commit()
            return instances
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PeticionadorException(f"Erro ao criar {self.model_class.__name__} em lote: {str(e)}")
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Atualiza múltiplos modelos em lote.
        
        Args:
            updates: Lista de atualizações (deve conter 'id' e dados)
            
        Returns:
            Número de registros atualizados
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            updated_count = 0
            for update_data in updates:
                if 'id' not in update_data:
                    continue
                
                instance_id = update_data.pop('id')
                instance = self.find_by_id(instance_id)
                if instance:
                    instance.update_from_dict(update_data)
                    updated_count += 1
            
            self.session.commit()
            return updated_count
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PeticionadorException(f"Erro ao atualizar {self.model_class.__name__} em lote: {str(e)}")
    
    def paginate(self, page: int = 1, per_page: int = 20, **filters) -> Dict[str, Any]:
        """
        Busca modelos com paginação.
        
        Args:
            page: Página atual (começa em 1)
            per_page: Registros por página
            **filters: Filtros para aplicar
            
        Returns:
            Dicionário com dados paginados
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            query = self.session.query(self.model_class)
            
            # Aplica filtros
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.filter(getattr(self.model_class, key) == value)
            
            # Conta total
            total = query.count()
            
            # Calcula offset
            offset = (page - 1) * per_page
            
            # Busca dados da página
            items = query.offset(offset).limit(per_page).all()
            
            # Calcula informações de paginação
            total_pages = (total + per_page - 1) // per_page
            has_prev = page > 1
            has_next = page < total_pages
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next,
                'prev_page': page - 1 if has_prev else None,
                'next_page': page + 1 if has_next else None
            }
        except SQLAlchemyError as e:
            raise PeticionadorException(f"Erro ao paginar {self.model_class.__name__}: {str(e)}")
    
    def save(self, instance: ModelType) -> ModelType:
        """
        Salva instância no banco.
        
        Args:
            instance: Instância para salvar
            
        Returns:
            Instância salva
            
        Raises:
            PeticionadorException: Erro no banco de dados
        """
        try:
            self.session.add(instance)
            self.session.commit()
            return instance
        except SQLAlchemyError as e:
            self.session.rollback()
            raise PeticionadorException(f"Erro ao salvar {self.model_class.__name__}: {str(e)}")
    
    def refresh(self, instance: ModelType) -> ModelType:
        """
        Atualiza instância com dados do banco.
        
        Args:
            instance: Instância para atualizar
            
        Returns:
            Instância atualizada
        """
        self.session.refresh(instance)
        return instance