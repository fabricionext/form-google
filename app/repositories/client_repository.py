"""
Repository para Clients.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func, desc
from app.models.client import Client, TipoPessoaEnum
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    """Repository específico para Clients."""
    
    def __init__(self):
        super().__init__(Client)
    
    def find_by_email(self, email: str) -> Optional[Client]:
        """
        Busca cliente por email.
        
        Args:
            email: Email do cliente
            
        Returns:
            Client ou None se não encontrado
        """
        return self.session.query(Client).filter_by(
            email=email,
            ativo=True
        ).first()
    
    def find_by_cpf(self, cpf: str) -> Optional[Client]:
        """
        Busca cliente por CPF.
        
        Args:
            cpf: CPF do cliente (com ou sem formatação)
            
        Returns:
            Client ou None se não encontrado
        """
        # Remove formatação do CPF
        cpf_clean = cpf.replace('.', '').replace('-', '').replace(' ', '')
        
        return self.session.query(Client).filter_by(
            cpf=cpf_clean,
            ativo=True
        ).first()
    
    def find_by_cnpj(self, cnpj: str) -> Optional[Client]:
        """
        Busca cliente por CNPJ.
        
        Args:
            cnpj: CNPJ do cliente (com ou sem formatação)
            
        Returns:
            Client ou None se não encontrado
        """
        # Remove formatação do CNPJ
        cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '').replace(' ', '')
        
        return self.session.query(Client).filter_by(
            cnpj=cnpj_clean,
            ativo=True
        ).first()
    
    def find_active(self) -> List[Client]:
        """
        Busca todos os clientes ativos.
        
        Returns:
            Lista de clientes ativos ordenados por nome
        """
        return self.session.query(Client).filter_by(
            ativo=True
        ).order_by(Client.nome_completo, Client.razao_social).all()
    
    def find_by_tipo_pessoa(self, tipo_pessoa: TipoPessoaEnum) -> List[Client]:
        """
        Busca clientes por tipo de pessoa.
        
        Args:
            tipo_pessoa: Tipo de pessoa (FISICA ou JURIDICA)
            
        Returns:
            Lista de clientes do tipo especificado
        """
        return self.session.query(Client).filter_by(
            tipo_pessoa=tipo_pessoa,
            ativo=True
        ).order_by(Client.nome_completo, Client.razao_social).all()
    
    def search_by_name(self, search_term: str) -> List[Client]:
        """
        Busca clientes por nome (nome completo, razão social ou nome fantasia).
        
        Args:
            search_term: Termo de busca
            
        Returns:
            Lista de clientes que coincidem com a busca
        """
        search_pattern = f"%{search_term}%"
        return self.session.query(Client).filter(
            and_(
                Client.ativo == True,
                or_(
                    Client.nome_completo.ilike(search_pattern),
                    Client.razao_social.ilike(search_pattern),
                    Client.nome_fantasia.ilike(search_pattern)
                )
            )
        ).order_by(Client.nome_completo, Client.razao_social).all()
    
    def search_by_document(self, document: str) -> List[Client]:
        """
        Busca clientes por documento (CPF ou CNPJ).
        
        Args:
            document: Documento para buscar (com ou sem formatação)
            
        Returns:
            Lista de clientes que coincidem
        """
        # Remove formatação
        doc_clean = document.replace('.', '').replace('/', '').replace('-', '').replace(' ', '')
        
        return self.session.query(Client).filter(
            and_(
                Client.ativo == True,
                or_(
                    Client.cpf.like(f"%{doc_clean}%"),
                    Client.cnpj.like(f"%{doc_clean}%")
                )
            )
        ).order_by(Client.nome_completo, Client.razao_social).all()
    
    def find_by_city(self, city: str) -> List[Client]:
        """
        Busca clientes por cidade.
        
        Args:
            city: Nome da cidade
            
        Returns:
            Lista de clientes da cidade
        """
        return self.session.query(Client).filter(
            and_(
                Client.ativo == True,
                Client.endereco_cidade.ilike(f"%{city}%")
            )
        ).order_by(Client.nome_completo, Client.razao_social).all()
    
    def find_by_state(self, state: str) -> List[Client]:
        """
        Busca clientes por estado.
        
        Args:
            state: Sigla do estado (ex: SP, RJ)
            
        Returns:
            Lista de clientes do estado
        """
        return self.session.query(Client).filter_by(
            endereco_estado=state.upper(),
            ativo=True
        ).order_by(Client.nome_completo, Client.razao_social).all()
    
    def find_recent(self, days: int = 30) -> List[Client]:
        """
        Busca clientes registrados recentemente.
        
        Args:
            days: Número de dias para considerar como recente
            
        Returns:
            Lista de clientes registrados nos últimos dias
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(Client).filter(
            and_(
                Client.ativo == True,
                Client.data_registro >= since_date
            )
        ).order_by(desc(Client.data_registro)).all()
    
    def find_with_documents(self) -> List[Client]:
        """
        Busca clientes que possuem documentos gerados.
        
        Returns:
            Lista de clientes com documentos
        """
        from app.models.document import Document
        
        return self.session.query(Client).join(Document).filter(
            Client.ativo == True
        ).distinct().order_by(Client.nome_completo, Client.razao_social).all()
    
    def find_without_documents(self) -> List[Client]:
        """
        Busca clientes que não possuem documentos gerados.
        
        Returns:
            Lista de clientes sem documentos
        """
        from app.models.document import Document
        
        return self.session.query(Client).outerjoin(Document).filter(
            and_(
                Client.ativo == True,
                Document.id.is_(None)
            )
        ).order_by(Client.nome_completo, Client.razao_social).all()
    
    def check_email_exists(self, email: str, exclude_id: int = None) -> bool:
        """
        Verifica se email já existe.
        
        Args:
            email: Email para verificar
            exclude_id: ID do cliente para excluir da verificação
            
        Returns:
            True se email já existe
        """
        query = self.session.query(Client).filter_by(email=email)
        
        if exclude_id:
            query = query.filter(Client.id != exclude_id)
        
        return query.first() is not None
    
    def check_cpf_exists(self, cpf: str, exclude_id: int = None) -> bool:
        """
        Verifica se CPF já existe.
        
        Args:
            cpf: CPF para verificar (com ou sem formatação)
            exclude_id: ID do cliente para excluir da verificação
            
        Returns:
            True se CPF já existe
        """
        cpf_clean = cpf.replace('.', '').replace('-', '').replace(' ', '')
        query = self.session.query(Client).filter_by(cpf=cpf_clean)
        
        if exclude_id:
            query = query.filter(Client.id != exclude_id)
        
        return query.first() is not None
    
    def check_cnpj_exists(self, cnpj: str, exclude_id: int = None) -> bool:
        """
        Verifica se CNPJ já existe.
        
        Args:
            cnpj: CNPJ para verificar (com ou sem formatação)
            exclude_id: ID do cliente para excluir da verificação
            
        Returns:
            True se CNPJ já existe
        """
        cnpj_clean = cnpj.replace('.', '').replace('/', '').replace('-', '').replace(' ', '')
        query = self.session.query(Client).filter_by(cnpj=cnpj_clean)
        
        if exclude_id:
            query = query.filter(Client.id != exclude_id)
        
        return query.first() is not None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas dos clientes.
        
        Returns:
            Dicionário com estatísticas
        """
        total_clients = self.count(ativo=True)
        pf_count = self.count(tipo_pessoa=TipoPessoaEnum.FISICA, ativo=True)
        pj_count = self.count(tipo_pessoa=TipoPessoaEnum.JURIDICA, ativo=True)
        
        # Clientes por estado
        state_results = self.session.query(
            Client.endereco_estado,
            func.count(Client.id)
        ).filter_by(ativo=True).group_by(Client.endereco_estado).all()
        
        state_distribution = {state: count for state, count in state_results if state}
        
        # Clientes registrados nos últimos 30 dias
        recent_count = len(self.find_recent(30))
        
        # Clientes com/sem documentos
        with_docs = len(self.find_with_documents())
        without_docs = len(self.find_without_documents())
        
        return {
            'total_clients': total_clients,
            'pessoa_fisica_count': pf_count,
            'pessoa_juridica_count': pj_count,
            'recent_registrations_30d': recent_count,
            'clients_with_documents': with_docs,
            'clients_without_documents': without_docs,
            'state_distribution': state_distribution,
            'most_common_state': max(state_distribution.items(), key=lambda x: x[1])[0] if state_distribution else None
        }
    
    def get_registration_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Retorna estatísticas de registros por dia.
        
        Args:
            days: Número de dias para analisar
            
        Returns:
            Lista com estatísticas por dia
        """
        since_date = datetime.utcnow() - timedelta(days=days)
        
        results = self.session.query(
            func.DATE(Client.data_registro).label('date'),
            func.count(Client.id).label('registrations'),
            func.sum(func.case([(Client.tipo_pessoa == TipoPessoaEnum.FISICA, 1)], else_=0)).label('pf'),
            func.sum(func.case([(Client.tipo_pessoa == TipoPessoaEnum.JURIDICA, 1)], else_=0)).label('pj')
        ).filter(
            Client.data_registro >= since_date
        ).group_by(
            func.DATE(Client.data_registro)
        ).order_by(
            func.DATE(Client.data_registro)
        ).all()
        
        return [
            {
                'date': result.date.strftime('%Y-%m-%d'),
                'total_registrations': result.registrations,
                'pessoa_fisica': result.pf or 0,
                'pessoa_juridica': result.pj or 0
            }
            for result in results
        ]
    
    def deactivate_client(self, client_id: int) -> bool:
        """
        Desativa cliente (soft delete).
        
        Args:
            client_id: ID do cliente
            
        Returns:
            True se desativado com sucesso
        """
        client = self.find_by_id(client_id)
        if not client:
            return False
        
        client.ativo = False
        self.save(client)
        return True
    
    def activate_client(self, client_id: int) -> bool:
        """
        Ativa cliente.
        
        Args:
            client_id: ID do cliente
            
        Returns:
            True se ativado com sucesso
        """
        client = self.find_by_id(client_id)
        if not client:
            return False
        
        client.ativo = True
        self.save(client)
        return True