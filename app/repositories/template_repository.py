"""
Repository para Templates.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_
from app.models.document_template import DocumentTemplate as Template
from app.repositories.base import BaseRepository
from app.utils.exceptions import TemplateNotFoundException


class TemplateRepository(BaseRepository[Template]):
    """Repository específico para Templates."""
    
    def __init__(self):
        super().__init__(Template)
    
    def find_by_slug(self, slug: str) -> Optional[Template]:
        """
        Busca template por slug.
        
        Args:
            slug: Slug único do template
            
        Returns:
            Template ou None se não encontrado
        """
        return self.session.query(Template).filter_by(slug=slug).first()
    
    def find_active(self) -> List[Template]:
        """
        Busca todos os templates ativos.
        
        Returns:
            Lista de templates ativos ordenados por nome
        """
        return self.session.query(Template).filter_by(
            is_active=True
        ).order_by(Template.name).all()
    
    def find_by_category(self, category: str) -> List[Template]:
        """
        Busca templates por categoria.
        
        Args:
            category: Categoria dos templates
            
        Returns:
            Lista de templates da categoria
        """
        return self.session.query(Template).filter_by(
            category=category,
            is_active=True
        ).order_by(Template.name).all()
    
    def find_by_google_drive_id(self, google_drive_id: str) -> Optional[Template]:
        """
        Busca template por ID do Google Drive.
        
        Args:
            google_drive_id: ID do arquivo no Google Drive
            
        Returns:
            Template ou None se não encontrado
        """
        return self.session.query(Template).filter_by(
            google_drive_id=google_drive_id
        ).first()
    
    def search_by_name(self, search_term: str) -> List[Template]:
        """
        Busca templates por nome (busca parcial).
        
        Args:
            search_term: Termo de busca
            
        Returns:
            Lista de templates que coincidem com a busca
        """
        search_pattern = f"%{search_term}%"
        return self.session.query(Template).filter(
            and_(
                Template.is_active == True,
                or_(
                    Template.name.ilike(search_pattern),
                    Template.description.ilike(search_pattern)
                )
            )
        ).order_by(Template.name).all()
    
    def find_with_placeholders(self, template_id: int) -> Optional[Template]:
        """
        Busca template com placeholders carregados.
        
        Args:
            template_id: ID do template
            
        Returns:
            Template com placeholders ou None
        """
        from sqlalchemy.orm import joinedload
        
        return self.session.query(Template).options(
            joinedload(Template.placeholders)
        ).filter_by(id=template_id).first()
    
    def find_by_tags(self, tags: List[str]) -> List[Template]:
        """
        Busca templates que contêm alguma das tags.
        
        Args:
            tags: Lista de tags para buscar
            
        Returns:
            Lista de templates que contêm as tags
        """
        conditions = []
        for tag in tags:
            conditions.append(Template.tags.contains(f'"{tag}"'))
        
        return self.session.query(Template).filter(
            and_(
                Template.is_active == True,
                or_(*conditions)
            )
        ).order_by(Template.name).all()
    
    def get_most_used(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna templates mais utilizados.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de dicionários com template e contagem de uso
        """
        from sqlalchemy import func
        from app.models.form import FormSubmission as Document
        
        results = self.session.query(
            Template,
            func.count(Document.id).label('usage_count')
        ).outerjoin(Document).filter(
            Template.is_active == True
        ).group_by(Template.id).order_by(
            func.count(Document.id).desc()
        ).limit(limit).all()
        
        return [
            {
                'template': template,
                'usage_count': usage_count
            }
            for template, usage_count in results
        ]
    
    def get_categories(self) -> List[str]:
        """
        Retorna todas as categorias de templates ativos.
        
        Returns:
            Lista de categorias únicas
        """
        results = self.session.query(Template.category).filter(
            and_(
                Template.is_active == True,
                Template.category.isnot(None)
            )
        ).distinct().all()
        
        return [category[0] for category in results]
    
    def deactivate(self, template_id: int) -> bool:
        """
        Desativa template (soft delete).
        
        Args:
            template_id: ID do template
            
        Returns:
            True se desativado com sucesso
            
        Raises:
            TemplateNotFoundException: Se template não existe
        """
        template = self.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundException(template_id)
        
        template.is_active = False
        self.save(template)
        return True
    
    def activate(self, template_id: int) -> bool:
        """
        Ativa template.
        
        Args:
            template_id: ID do template
            
        Returns:
            True se ativado com sucesso
            
        Raises:
            TemplateNotFoundException: Se template não existe
        """
        template = self.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundException(template_id)
        
        template.is_active = True
        self.save(template)
        return True
    
    def increment_version(self, template_id: int) -> Template:
        """
        Incrementa versão do template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Template com versão incrementada
            
        Raises:
            TemplateNotFoundException: Se template não existe
        """
        template = self.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundException(template_id)
        
        template.version += 1
        return self.save(template)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas dos templates.
        
        Returns:
            Dicionário com estatísticas
        """
        from sqlalchemy import func
        from app.models.form import FormSubmission as Document
        
        total_templates = self.count()
        active_templates = self.count(is_active=True)
        
        # Templates com documentos gerados
        templates_with_docs = self.session.query(Template.id).join(Document).distinct().count()
        
        # Template mais usado
        most_used = self.session.query(
            Template.name,
            func.count(Document.id).label('count')
        ).outerjoin(Document).filter(
            Template.is_active == True
        ).group_by(Template.id, Template.name).order_by(
            func.count(Document.id).desc()
        ).first()
        
        return {
            'total_templates': total_templates,
            'active_templates': active_templates,
            'inactive_templates': total_templates - active_templates,
            'templates_with_documents': templates_with_docs,
            'most_used_template': {
                'name': most_used[0] if most_used else None,
                'usage_count': most_used[1] if most_used else 0
            }
        }