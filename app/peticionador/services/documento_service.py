"""
Serviço responsável pela geração de documentos Google Docs.
Extrai toda a lógica complexa de geração de documentos das rotas.
"""

import re
from typing import Dict, Tuple, Optional
from flask import current_app, request
from datetime import datetime
from extensions import db

from .. import google_services
from ..models import PeticaoModelo, PeticaoGerada


class DocumentoService:
    """Service para geração de documentos Google Docs"""
    
    def __init__(self):
        self._google_service = None
    
    @property
    def google_service(self) -> google_services.DocumentGenerationService:
        """Lazy loading do serviço Google com inicialização"""
        if self._google_service is None:
            self._google_service = google_services.DocumentGenerationService()
            self._google_service._initialize_services()
        return self._google_service
    
    def gerar_documento_dinamico(
        self, 
        modelo: PeticaoModelo, 
        form_data: Dict[str, str],
        placeholders: list
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Gera documento dinamicamente a partir dos dados do formulário.
        
        Args:
            modelo: Modelo da petição
            form_data: Dados do formulário (request.form)
            placeholders: Lista de placeholders do modelo
            
        Returns:
            Tuple com (novo_id, link) ou (None, None) em caso de erro
        """
        try:
            current_app.logger.info(f"Iniciando geração de documento para modelo '{modelo.nome}'")
            
            # 1. Montar dicionário de substituições
            replacements = self._build_replacements(form_data, placeholders)
            
            # 2. Gerar nome do arquivo
            nome_arquivo = self._generate_filename(modelo, replacements)
            
            # 3. Verificar se documento já existe e ajustar nome se necessário
            nome_arquivo_final = self._handle_duplicate_check(modelo, nome_arquivo)
            
            # 4. Gerar documento no Google Docs
            novo_id, link = self.google_service.copy_template_and_fill(
                modelo.google_doc_id,
                nome_arquivo_final,
                modelo.pasta_destino_id,
                replacements,
            )
            
            if novo_id:
                # 5. Salvar registro no banco de dados
                self._save_document_record(modelo, novo_id, link)
                current_app.logger.info(f"Documento gerado com sucesso! ID: {novo_id}")
                return novo_id, link
            else:
                raise Exception("A função copy_template_and_fill não retornou um ID de documento.")
                
        except Exception as e:
            current_app.logger.error(f"Erro ao gerar documento: {e}", exc_info=True)
            raise
    
    def _build_replacements(self, form_data: Dict[str, str], placeholders: list) -> Dict[str, str]:
        """Monta o dicionário de substituições a partir dos dados do formulário"""
        replacements = {
            ph.chave: form_data.get(ph.chave, "") for ph in placeholders
        }
        
        # Adicionar data atual formatada
        replacements["data_atual"] = google_services.get_current_date_formatted()
        
        current_app.logger.debug(f"Dados para substituição: {replacements}")
        return replacements
    
    def _generate_filename(self, modelo: PeticaoModelo, replacements: Dict[str, str]) -> str:
        """
        Gera nome do arquivo no formato: dd-mm-aaaa-autor_nome autor_sobrenome-tipo de documento
        """
        data_atual_str = datetime.now().strftime("%d-%m-%Y")
        
        # Buscar nome do autor (primeira tentativa com os campos mais comuns)
        autor_nome = (
            replacements.get("autor_nome") or 
            replacements.get("autor_1_nome") or 
            replacements.get("primeiro_nome") or 
            "Cliente"
        )
        
        # Buscar sobrenome do autor
        autor_sobrenome = (
            replacements.get("autor_sobrenome") or 
            replacements.get("autor_1_sobrenome") or 
            replacements.get("sobrenome") or 
            ""
        )
        
        # Construir nome base
        nome_base = f"{data_atual_str}-{autor_nome} {autor_sobrenome}-{modelo.nome}".strip()
        
        # Limpar caracteres inválidos para nome de arquivo
        nome_base = re.sub(r'[\\/*?:"<>|]', "", nome_base)
        
        current_app.logger.info(f"Nome base gerado: '{nome_base}'")
        return nome_base
    
    def _handle_duplicate_check(self, modelo: PeticaoModelo, nome_base: str) -> str:
        """
        Verifica se documento já existe e adiciona timestamp se necessário
        """
        try:
            existe, _, _ = self.google_service.check_document_exists(
                nome_base, 
                modelo.pasta_destino_id
            )
            
            if existe:
                # Adicionar timestamp para evitar duplicatas
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                nome_arquivo_final = f"{nome_base}-{timestamp}"
                current_app.logger.info(f"Documento já existe. Nome ajustado: '{nome_arquivo_final}'")
            else:
                nome_arquivo_final = nome_base
                current_app.logger.info(f"Documento não existe. Usando nome base: '{nome_arquivo_final}'")
            
            return nome_arquivo_final
            
        except Exception as e:
            current_app.logger.warning(f"Erro ao verificar duplicatas: {e}. Usando timestamp.")
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            return f"{nome_base}-{timestamp}"
    
    def _save_document_record(self, modelo: PeticaoModelo, novo_id: str, link: str) -> None:
        """Salva registro da petição gerada no banco de dados"""
        try:
            peticao = PeticaoGerada(
                cliente_id=None,  # Para formulários dinâmicos cliente_id pode ser None
                modelo=modelo.nome,
                google_id=novo_id,
                link=link
            )
            db.session.add(peticao)
            db.session.commit()
            current_app.logger.info(f"Registro salvo no banco: PeticaoGerada ID {peticao.id}")
            
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar no banco: {e}")
            db.session.rollback()
            # Não re-raise para não quebrar o fluxo principal
            # O documento foi gerado com sucesso, falha é apenas no registro local 