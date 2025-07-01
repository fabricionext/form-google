"""
Repository para Placeholders.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_, func
from app.models.template_placeholder import TemplatePlaceholder as Placeholder
from app.repositories.base import BaseRepository
from app.config.constants import PLACEHOLDER_CATEGORIES


class PlaceholderRepository(BaseRepository[Placeholder]):
    """Repository específico para Placeholders."""
    
    def __init__(self):
        super().__init__(Placeholder)
    
    def find_by_template(self, template_id: int) -> List[Placeholder]:
        """
        Busca placeholders por template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Lista de placeholders do template ordenados por order_index
        """
        return self.session.query(Placeholder).filter_by(
            template_id=template_id
        ).order_by(Placeholder.order_index, Placeholder.name).all()
    
    def find_by_category(self, template_id: int, category: str) -> List[Placeholder]:
        """
        Busca placeholders por template e categoria.
        
        Args:
            template_id: ID do template
            category: Categoria dos placeholders
            
        Returns:
            Lista de placeholders da categoria
        """
        return self.session.query(Placeholder).filter_by(
            template_id=template_id,
            category=category
        ).order_by(Placeholder.order_index, Placeholder.name).all()
    
    def find_by_name(self, template_id: int, name: str) -> Optional[Placeholder]:
        """
        Busca placeholder por nome dentro de um template.
        
        Args:
            template_id: ID do template
            name: Nome do placeholder
            
        Returns:
            Placeholder ou None se não encontrado
        """
        return self.session.query(Placeholder).filter_by(
            template_id=template_id,
            name=name
        ).first()
    
    def find_required(self, template_id: int) -> List[Placeholder]:
        """
        Busca placeholders obrigatórios de um template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Lista de placeholders obrigatórios
        """
        return self.session.query(Placeholder).filter_by(
            template_id=template_id,
            required=True
        ).order_by(Placeholder.order_index, Placeholder.name).all()
    
    def find_by_type(self, template_id: int, placeholder_type: str) -> List[Placeholder]:
        """
        Busca placeholders por tipo.
        
        Args:
            template_id: ID do template
            placeholder_type: Tipo do placeholder
            
        Returns:
            Lista de placeholders do tipo especificado
        """
        return self.session.query(Placeholder).filter_by(
            template_id=template_id,
            type=placeholder_type
        ).order_by(Placeholder.order_index, Placeholder.name).all()
    
    def find_by_group(self, template_id: int, group_name: str) -> List[Placeholder]:
        """
        Busca placeholders por grupo.
        
        Args:
            template_id: ID do template
            group_name: Nome do grupo
            
        Returns:
            Lista de placeholders do grupo
        """
        return self.session.query(Placeholder).filter_by(
            template_id=template_id,
            group_name=group_name
        ).order_by(Placeholder.order_index, Placeholder.name).all()
    
    def search_by_label(self, template_id: int, search_term: str) -> List[Placeholder]:
        """
        Busca placeholders por label ou description.
        
        Args:
            template_id: ID do template
            search_term: Termo de busca
            
        Returns:
            Lista de placeholders que coincidem
        """
        search_pattern = f"%{search_term}%"
        return self.session.query(Placeholder).filter(
            and_(
                Placeholder.template_id == template_id,
                or_(
                    Placeholder.label.ilike(search_pattern),
                    Placeholder.description.ilike(search_pattern),
                    Placeholder.name.ilike(search_pattern)
                )
            )
        ).order_by(Placeholder.order_index, Placeholder.name).all()
    
    def get_categories_for_template(self, template_id: int) -> List[str]:
        """
        Retorna categorias únicas de placeholders em um template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Lista de categorias únicas
        """
        results = self.session.query(Placeholder.category).filter(
            and_(
                Placeholder.template_id == template_id,
                Placeholder.category.isnot(None)
            )
        ).distinct().all()
        
        return [category[0] for category in results]
    
    def get_groups_for_template(self, template_id: int) -> List[str]:
        """
        Retorna grupos únicos de placeholders em um template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Lista de grupos únicos
        """
        results = self.session.query(Placeholder.group_name).filter(
            and_(
                Placeholder.template_id == template_id,
                Placeholder.group_name.isnot(None)
            )
        ).distinct().all()
        
        return [group[0] for group in results]
    
    def get_next_order_index(self, template_id: int) -> int:
        """
        Retorna próximo índice de ordenação para um template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Próximo índice disponível
        """
        max_index = self.session.query(
            func.max(Placeholder.order_index)
        ).filter_by(template_id=template_id).scalar()
        
        return (max_index or 0) + 1
    
    def reorder_placeholders(self, template_id: int, placeholder_orders: List[Dict[str, int]]) -> bool:
        """
        Reordena placeholders de um template.
        
        Args:
            template_id: ID do template
            placeholder_orders: Lista de {'placeholder_id': id, 'order_index': index}
            
        Returns:
            True se reordenação foi bem-sucedida
        """
        try:
            for item in placeholder_orders:
                placeholder = self.session.query(Placeholder).filter_by(
                    id=item['placeholder_id'],
                    template_id=template_id
                ).first()
                
                if placeholder:
                    placeholder.order_index = item['order_index']
            
            self.session.commit()
            return True
        except Exception:
            self.session.rollback()
            return False
    
    def duplicate_from_template(self, source_template_id: int, target_template_id: int) -> List[Placeholder]:
        """
        Duplica placeholders de um template para outro.
        
        Args:
            source_template_id: ID do template origem
            target_template_id: ID do template destino
            
        Returns:
            Lista de novos placeholders criados
        """
        source_placeholders = self.find_by_template(source_template_id)
        new_placeholders = []
        
        for source_ph in source_placeholders:
            new_data = source_ph.to_dict(exclude=['id', 'created_at', 'updated_at'])
            new_data['template_id'] = target_template_id
            
            new_placeholder = Placeholder(**new_data)
            self.session.add(new_placeholder)
            new_placeholders.append(new_placeholder)
        
        self.session.commit()
        return new_placeholders
    
    def get_statistics_by_template(self, template_id: int) -> Dict[str, Any]:
        """
        Retorna estatísticas de placeholders de um template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Dicionário com estatísticas
        """
        placeholders = self.find_by_template(template_id)
        
        # Contagem por categoria
        category_counts = {}
        for ph in placeholders:
            category = ph.category or 'sem_categoria'
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Contagem por tipo
        type_counts = {}
        for ph in placeholders:
            type_counts[ph.type] = type_counts.get(ph.type, 0) + 1
        
        # Outros contadores
        required_count = sum(1 for ph in placeholders if ph.required)
        with_default_count = sum(1 for ph in placeholders if ph.default_value)
        with_validation_count = sum(1 for ph in placeholders if ph.validation_rules)
        
        return {
            'total_placeholders': len(placeholders),
            'required_placeholders': required_count,
            'optional_placeholders': len(placeholders) - required_count,
            'with_default_value': with_default_count,
            'with_validation_rules': with_validation_count,
            'category_distribution': category_counts,
            'type_distribution': type_counts,
            'categories': list(category_counts.keys()),
            'types': list(type_counts.keys())
        }
    
    def validate_placeholder_names(self, template_id: int, names: List[str]) -> Dict[str, bool]:
        """
        Valida se nomes de placeholders existem no template.
        
        Args:
            template_id: ID do template
            names: Lista de nomes para validar
            
        Returns:
            Dicionário com nome -> exists
        """
        existing_names = set([
            ph.name for ph in self.find_by_template(template_id)
        ])
        
        return {name: name in existing_names for name in names}
    
    def bulk_update_category(self, placeholder_ids: List[int], new_category: str) -> int:
        """
        Atualiza categoria de múltiplos placeholders.
        
        Args:
            placeholder_ids: Lista de IDs dos placeholders
            new_category: Nova categoria
            
        Returns:
            Número de placeholders atualizados
        """
        updated_count = self.session.query(Placeholder).filter(
            Placeholder.id.in_(placeholder_ids)
        ).update(
            {'category': new_category},
            synchronize_session=False
        )
        
        self.session.commit()
        return updated_count
    
    def find_orphaned(self) -> List[Placeholder]:
        """
        Busca placeholders órfãos (sem template).
        
        Returns:
            Lista de placeholders sem template associado
        """
        from app.models.document_template import DocumentTemplate as Template
        
        return self.session.query(Placeholder).outerjoin(Template).filter(
            Template.id.is_(None)
        ).all()