"""
Repository para Documents.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, desc
from app.models.document import Document
from app.repositories.base import BaseRepository
from app.utils.exceptions import DocumentNotFoundException
from app.config.constants import DOCUMENT_STATUSES


class DocumentRepository(BaseRepository[Document]):
    """Repository específico para Documents."""
    
    def __init__(self):
        super().__init__(Document)
    
    def find_by_slug(self, slug: str) -> Optional[Document]:
        """
        Busca documento por slug.
        
        Args:
            slug: Slug único do documento
            
        Returns:
            Document ou None se não encontrado
        """
        return self.session.query(Document).filter_by(slug=slug).first()
    
    def find_by_status(self, status: str) -> List[Document]:
        """
        Busca documentos por status.
        
        Args:
            status: Status dos documentos
            
        Returns:
            Lista de documentos com o status ordenados por data
        """
        return self.session.query(Document).filter_by(
            status=status
        ).order_by(desc(Document.created_at)).all()
    
    def find_by_template(self, template_id: int) -> List[Document]:
        """
        Busca documentos por template.
        
        Args:
            template_id: ID do template
            
        Returns:
            Lista de documentos do template
        """
        return self.session.query(Document).filter_by(
            template_id=template_id
        ).order_by(desc(Document.created_at)).all()
    
    def find_by_client(self, client_id: int) -> List[Document]:
        """
        Busca documentos por cliente.
        
        Args:
            client_id: ID do cliente
            
        Returns:
            Lista de documentos do cliente
        """
        return self.session.query(Document).filter_by(
            client_id=client_id
        ).order_by(desc(Document.created_at)).all()
    
    def find_by_google_drive_id(self, google_drive_id: str) -> Optional[Document]:
        """
        Busca documento por ID do Google Drive.
        
        Args:
            google_drive_id: ID do arquivo no Google Drive
            
        Returns:
            Document ou None se não encontrado
        """
        return self.session.query(Document).filter_by(
            google_drive_id=google_drive_id
        ).first()
    
    def find_pending_processing(self) -> List[Document]:
        """
        Busca documentos pendentes de processamento.
        
        Returns:
            Lista de documentos em status draft ou error (que podem ser reprocessados)
        """
        return self.session.query(Document).filter(
            Document.status.in_(['draft', 'error'])
        ).order_by(Document.created_at).all()
    
    def find_processing(self) -> List[Document]:
        """
        Busca documentos atualmente em processamento.
        
        Returns:
            Lista de documentos em processamento
        """
        return self.session.query(Document).filter_by(
            status='processing'
        ).order_by(Document.generation_started_at).all()
    
    def find_completed_recent(self, days: int = 7) -> List[Document]:
        """
        Busca documentos completados recentemente.
        
        Args:
            days: Número de dias para considerar como recente
            
        Returns:
            Lista de documentos completados nos últimos dias
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(Document).filter(
            and_(
                Document.status == 'completed',
                Document.generation_completed_at >= since_date
            )
        ).order_by(desc(Document.generation_completed_at)).all()
    
    def find_with_errors(self, max_retries: int = 3) -> List[Document]:
        """
        Busca documentos com erro que podem ser reprocessados.
        
        Args:
            max_retries: Número máximo de tentativas
            
        Returns:
            Lista de documentos com erro que ainda podem ser retentados
        """
        return self.session.query(Document).filter(
            and_(
                Document.status == 'error',
                Document.retry_count < max_retries
            )
        ).order_by(Document.updated_at).all()
    
    def find_stuck_processing(self, hours: int = 2) -> List[Document]:
        """
        Busca documentos "presos" em processamento.
        
        Args:
            hours: Número de horas para considerar como preso
            
        Returns:
            Lista de documentos em processamento há muito tempo
        """
        stuck_since = datetime.utcnow() - timedelta(hours=hours)
        return self.session.query(Document).filter(
            and_(
                Document.status == 'processing',
                Document.generation_started_at <= stuck_since
            )
        ).order_by(Document.generation_started_at).all()
    
    def search_by_title(self, search_term: str) -> List[Document]:
        """
        Busca documentos por título.
        
        Args:
            search_term: Termo de busca
            
        Returns:
            Lista de documentos que coincidem com a busca
        """
        search_pattern = f"%{search_term}%"
        return self.session.query(Document).filter(
            Document.title.ilike(search_pattern)
        ).order_by(desc(Document.created_at)).all()
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Document]:
        """
        Busca documentos por intervalo de datas.
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Lista de documentos criados no período
        """
        return self.session.query(Document).filter(
            and_(
                Document.created_at >= start_date,
                Document.created_at <= end_date
            )
        ).order_by(desc(Document.created_at)).all()
    
    def count_by_status(self) -> Dict[str, int]:
        """
        Conta documentos por status.
        
        Returns:
            Dicionário com contagem por status
        """
        results = self.session.query(
            Document.status,
            func.count(Document.id)
        ).group_by(Document.status).all()
        
        status_counts = {status: count for status, count in results}
        
        # Garante que todos os status apareçam no resultado
        for status in DOCUMENT_STATUSES:
            if status not in status_counts:
                status_counts[status] = 0
        
        return status_counts
    
    def count_by_template(self, template_id: int) -> int:
        """
        Conta documentos de um template específico.
        
        Args:
            template_id: ID do template
            
        Returns:
            Número de documentos do template
        """
        return self.session.query(Document).filter_by(
            template_id=template_id
        ).count()
    
    def get_generation_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Retorna estatísticas de geração de documentos.
        
        Args:
            days: Período em dias para análise
            
        Returns:
            Dicionário com estatísticas
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        # Documentos gerados no período
        period_docs = self.session.query(Document).filter(
            Document.created_at >= since_date
        )
        
        total_period = period_docs.count()
        completed_period = period_docs.filter_by(status='completed').count()
        failed_period = period_docs.filter_by(status='error').count()
        
        # Tempo médio de geração
        completed_docs = self.session.query(Document).filter(
            and_(
                Document.status == 'completed',
                Document.generation_started_at.isnot(None),
                Document.generation_completed_at.isnot(None),
                Document.created_at >= since_date
            )
        ).all()
        
        if completed_docs:
            total_seconds = sum([
                (doc.generation_completed_at - doc.generation_started_at).total_seconds()
                for doc in completed_docs
            ])
            avg_generation_time = total_seconds / len(completed_docs)
        else:
            avg_generation_time = 0
        
        # Taxa de sucesso
        success_rate = (completed_period / total_period * 100) if total_period > 0 else 0
        
        return {
            'period_days': days,
            'total_documents': total_period,
            'completed_documents': completed_period,
            'failed_documents': failed_period,
            'success_rate_percentage': round(success_rate, 2),
            'average_generation_time_seconds': round(avg_generation_time, 2),
            'processing_documents': self.count(status='processing'),
            'pending_documents': self.count(status='draft')
        }
    
    def get_daily_statistics(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Retorna estatísticas diárias de documentos.
        
        Args:
            days: Número de dias para analisar
            
        Returns:
            Lista com estatísticas por dia
        """
        from sqlalchemy import DATE
        
        since_date = datetime.utcnow() - timedelta(days=days)
        
        results = self.session.query(
            func.DATE(Document.created_at).label('date'),
            func.count(Document.id).label('total'),
            func.sum(func.case([(Document.status == 'completed', 1)], else_=0)).label('completed'),
            func.sum(func.case([(Document.status == 'error', 1)], else_=0)).label('failed')
        ).filter(
            Document.created_at >= since_date
        ).group_by(
            func.DATE(Document.created_at)
        ).order_by(
            func.DATE(Document.created_at)
        ).all()
        
        return [
            {
                'date': result.date.strftime('%Y-%m-%d'),
                'total': result.total,
                'completed': result.completed or 0,
                'failed': result.failed or 0,
                'success_rate': round((result.completed or 0) / result.total * 100, 2) if result.total > 0 else 0
            }
            for result in results
        ]
    
    def cleanup_old_errors(self, days: int = 30) -> int:
        """
        Remove documentos com erro antigos.
        
        Args:
            days: Idade em dias para considerar antigo
            
        Returns:
            Número de documentos removidos
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        old_error_docs = self.session.query(Document).filter(
            and_(
                Document.status == 'error',
                Document.updated_at <= cutoff_date
            )
        ).all()
        
        count = len(old_error_docs)
        for doc in old_error_docs:
            self.session.delete(doc)
        
        self.session.commit()
        return count