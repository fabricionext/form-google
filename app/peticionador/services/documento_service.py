"""
Serviço responsável pela geração de documentos Google Docs.
Extrai toda a lógica complexa de geração de documentos das rotas.
"""

import logging
from typing import Dict, Tuple, Optional
from flask import current_app
from datetime import datetime
from app.extensions import db

from ..models import PeticaoModelo, PeticaoGerada
from .google_drive_service import GoogleDriveService
from .document_naming_service import DocumentNamingService
from ..utils.document_utils import replace_placeholders_in_doc

logger = logging.getLogger(__name__)


class DocumentoService:
    """Service para geração de documentos Google Docs"""
    
    def __init__(self, drive_service: GoogleDriveService = None, naming_service: DocumentNamingService = None):
        self.drive_service = drive_service or GoogleDriveService()
        self.naming_service = naming_service or DocumentNamingService()
    
    def gerar_documento_dinamico(
        self, 
        modelo: PeticaoModelo, 
        form_data: Dict[str, str],
        placeholders: list
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Orquestra a geração de um documento dinâmico.
        """
        logger.info(f"Iniciando geração de documento para o modelo: {modelo.nome}")
        
        # Implementação básica para satisfazer a interface
        # A lógica completa será implementada nas próximas fases
        try:
            # 1. Construir substituições
            replacements = self._build_replacements(form_data, placeholders)
            
            # 2. Gerar nome do arquivo
            nome_arquivo = self._generate_filename(modelo, replacements)
            
            # 3. Simular geração do documento (placeholder)
            # Em uma implementação real, aqui chamaríamos:
            # novo_id, link = self.drive_service.copy_file(...)
            
            # 4. Salvar registro no banco
            self._save_document_record(modelo, "mock_doc_id", "mock_link")
            
            logger.info(f"Documento gerado com sucesso (simulado)")
            return "mock_doc_id", "mock_link"
            
        except Exception as e:
            logger.error(f"Erro ao gerar documento: {e}", exc_info=True)
            return None, None
    
    def _build_replacements(self, form_data: Dict[str, str], placeholders: list) -> Dict[str, str]:
        """Monta o dicionário de substituições a partir dos dados do formulário"""
        replacements = {
            ph.chave: form_data.get(ph.chave, "") for ph in placeholders
        }
        
        # Adicionar data atual formatada
        replacements["data_atual"] = datetime.now().strftime("%d/%m/%Y")
        
        logger.debug(f"Dados para substituição: {replacements}")
        return replacements
    
    def _generate_filename(self, modelo: PeticaoModelo, replacements: Dict[str, str]) -> str:
        """Gera nome do arquivo baseado no modelo e dados do formulário"""
        data_atual_str = datetime.now().strftime("%d-%m-%Y")
        
        # Buscar nome do autor
        autor_nome = (
            replacements.get("autor_nome") or 
            replacements.get("primeiro_nome") or 
            "Cliente"
        )
        
        # Construir nome base
        nome_base = f"{data_atual_str}-{autor_nome}-{modelo.nome}".strip()
        
        logger.info(f"Nome base gerado: '{nome_base}'")
        return nome_base
    
    def _save_document_record(self, modelo: PeticaoModelo, novo_id: str, link: str) -> None:
        """Salva registro da petição gerada no banco de dados"""
        try:
            peticao = PeticaoGerada(
                cliente_id=None,
                modelo=modelo.nome,
                google_id=novo_id,
                link=link
            )
            db.session.add(peticao)
            db.session.commit()
            logger.info(f"Registro salvo no banco: PeticaoGerada ID {peticao.id}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar no banco: {e}")
            db.session.rollback() 