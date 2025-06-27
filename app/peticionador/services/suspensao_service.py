"""
Serviço para geração de documentos de Suspensão do Direito de Dirigir.
Refatora a lógica complexa da rota gerar_suspensao_peticao_dados_form.
"""

from typing import Optional, Dict, Any, Tuple
from flask import current_app, flash, url_for, redirect
from datetime import datetime

from extensions import db
from .. import google_services
from ..models import PeticaoModelo, Cliente, PeticaoGerada
from models import RespostaForm


class SuspensaoService:
    """Service para gerenciar operações de Suspensão do Direito de Dirigir"""
    
    def __init__(self):
        self._modelo = None
    
    @property
    def modelo(self) -> Optional[PeticaoModelo]:
        """Lazy loading do modelo de Suspensão"""
        if self._modelo is None:
            self._modelo = PeticaoModelo.query.filter_by(
                nome="Suspensão do Direito de Dirigir"
            ).first()
        return self._modelo
    
    def buscar_cliente_por_cpf(self, cpf: str) -> Optional[RespostaForm]:
        """
        Busca cliente por CPF de forma segura.
        
        Args:
            cpf: CPF para buscar
            
        Returns:
            Cliente encontrado ou None
        """
        if not cpf:
            return None
        
        # Validação de segurança
        from app.validators.cliente_validator import ClienteValidator
        
        valido, cpf_limpo, erro = ClienteValidator.validar_cpf(cpf)
        if not valido:
            current_app.logger.warning(f"Busca com CPF inválido: {erro}")
            return None
        
        current_app.logger.info(f"Buscando cliente com CPF: {cpf_limpo}")
        
        # Buscar com CPF limpo
        cliente = RespostaForm.query.filter_by(cpf=cpf_limpo).first()
        
        # Se não encontrou, tentar com formatação
        if not cliente and len(cpf_limpo) == 11:
            cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}"
            cliente = RespostaForm.query.filter_by(cpf=cpf_formatado).first()
            current_app.logger.info(f"Tentativa com CPF formatado: {cpf_formatado}")
        
        if cliente:
            current_app.logger.info(f"Cliente encontrado: {cliente.primeiro_nome} {cliente.sobrenome}")
        else:
            current_app.logger.info(f"Nenhum cliente encontrado para CPF: {cpf_limpo}")
        
        return cliente
    
    def preencher_formulario_com_cliente(self, form, cliente: RespostaForm) -> None:
        """
        Preenche formulário com dados do cliente encontrado.
        
        Args:
            form: Formulário a ser preenchido
            cliente: Cliente com dados para preenchimento
        """
        form.cliente_id.data = cliente.id
        form.cliente_primeiro_nome.data = cliente.primeiro_nome
        form.cliente_sobrenome.data = cliente.sobrenome
        form.cliente_email.data = cliente.email
        form.cliente_telefone_celular.data = cliente.telefone_celular
        
        # Dados de endereço
        form.cliente_endereco_logradouro.data = getattr(cliente, 'logradouro', '') or getattr(cliente, 'endereco_logradouro', '')
        form.cliente_endereco_numero.data = getattr(cliente, 'numero', '') or getattr(cliente, 'endereco_numero', '')
        form.cliente_endereco_complemento.data = getattr(cliente, 'complemento', '') or getattr(cliente, 'endereco_complemento', '')
        form.cliente_endereco_bairro.data = getattr(cliente, 'bairro', '') or getattr(cliente, 'endereco_bairro', '')
        form.cliente_endereco_cidade.data = getattr(cliente, 'cidade', '') or getattr(cliente, 'endereco_cidade', '')
        form.cliente_endereco_estado.data = getattr(cliente, 'uf_endereco', '') or getattr(cliente, 'endereco_estado', '')
        form.cliente_endereco_cep.data = getattr(cliente, 'cep', '') or getattr(cliente, 'endereco_cep', '')
        
        # Documentos
        form.cliente_cpf.data = cliente.cpf
        form.cliente_rg_numero.data = getattr(cliente, 'rg', '') or getattr(cliente, 'rg_numero', '')
        form.cliente_cnh_numero.data = getattr(cliente, 'cnh', '') or getattr(cliente, 'cnh_numero', '')
        
        current_app.logger.info(f"Formulário preenchido com dados do cliente {cliente.primeiro_nome}")
    
    def atualizar_cliente_do_formulario(self, cliente: Cliente, form) -> None:
        """
        Atualiza dados do cliente com informações do formulário.
        
        Args:
            cliente: Cliente a ser atualizado
            form: Formulário com novos dados
        """
        cliente.primeiro_nome = form.cliente_primeiro_nome.data
        cliente.sobrenome = form.cliente_sobrenome.data
        cliente.email = form.cliente_email.data
        cliente.telefone_celular = form.cliente_telefone_celular.data
        cliente.endereco_logradouro = form.cliente_endereco_logradouro.data
        cliente.endereco_numero = form.cliente_endereco_numero.data
        cliente.endereco_complemento = form.cliente_endereco_complemento.data
        cliente.endereco_bairro = form.cliente_endereco_bairro.data
        cliente.endereco_cidade = form.cliente_endereco_cidade.data
        cliente.endereco_estado = form.cliente_endereco_estado.data
        cliente.endereco_cep = form.cliente_endereco_cep.data
        cliente.cpf = form.cliente_cpf.data
        cliente.rg_numero = form.cliente_rg_numero.data
        cliente.cnh_numero = form.cliente_cnh_numero.data
        
        current_app.logger.info(f"Cliente {cliente.id} atualizado com dados do formulário")
    
    def preparar_dados_documento(self, cliente: Cliente, dados_peticao: Dict[str, str]) -> Dict[str, str]:
        """
        Prepara dicionário de dados para geração do documento.
        
        Args:
            cliente: Cliente com dados pessoais
            dados_peticao: Dados específicos da petição
            
        Returns:
            Dicionário completo para substituição no documento
        """
        # Usar as properties do modelo para formatação
        return {
            "nome_completo": cliente.nome_completo_formatado,
            "razao_social": cliente.razao_social or "",
            "cpf": cliente.cpf or "",
            "cnpj": cliente.cnpj or "",
            "rg_numero": cliente.rg_numero or "",
            "cnh_numero": cliente.cnh_numero or "",
            "endereco_completo": cliente.endereco_formatado,
            "email": cliente.email or "",
            "telefone_celular": cliente.telefone_principal,
            "data_atual": datetime.now().strftime("%d de %B de %Y"),
            **dados_peticao,  # Adiciona os dados específicos da petição
        }
    
    def gerar_documento_google(
        self, 
        cliente_data: Dict[str, str], 
        cliente: Cliente
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Gera documento no Google Docs.
        
        Args:
            cliente_data: Dados formatados para substituição
            cliente: Cliente para nomear pasta/arquivo
            
        Returns:
            Tuple com (document_id, link) ou (None, None) em caso de erro
        """
        try:
            # Configurações do Google Drive/Docs
            template_id = current_app.config.get("TEMPLATE_PET_SUSPENSAO_DIREITO_DIRIGIR")
            parent_folder_id = current_app.config.get("PETICIONADOR_PARENT_FOLDER_ID")
            
            if not template_id or not parent_folder_id:
                raise ValueError("IDs de template ou pasta pai não configurados")
            
            # Nome da pasta do cliente
            cliente_folder_name = (
                cliente.nome_completo_formatado or "Cliente Desconhecido"
            )
            
            # Nome do arquivo
            year = datetime.now().year
            numero_processo = cliente_data.get('numero_processo_adm', 'sem-processo')
            file_name = f"{year}-{cliente_folder_name}-Suspensão Direito Dirigir-{numero_processo}"
            
            # Criar serviços Google
            drive_service = google_services.create_drive_service()
            docs_service = google_services.create_docs_service()
            
            # Criar pasta do cliente se não existir
            target_folder_id = google_services.create_folder_if_not_exists(
                drive_service, parent_folder_id, cliente_folder_name
            )
            
            if not target_folder_id:
                raise ValueError("Erro ao criar ou encontrar a pasta do cliente no Google Drive")
            
            # Gerar documento
            document_id, link = google_services.generate_google_docs_from_template_peticionador(
                docs_service,
                drive_service,
                template_id,
                target_folder_id,
                file_name,
                cliente_data,
            )
            
            if document_id:
                # Salvar no banco de dados
                self._salvar_peticao_gerada(cliente, document_id, link)
                current_app.logger.info(f"Documento gerado com sucesso: {document_id}")
                return document_id, link
            else:
                raise ValueError("Falha na geração do documento Google")
                
        except Exception as e:
            current_app.logger.error(f"Erro na geração do documento: {e}", exc_info=True)
            raise
    
    def _salvar_peticao_gerada(self, cliente: Cliente, document_id: str, link: str) -> None:
        """
        Salva registro da petição gerada no banco de dados.
        
        Args:
            cliente: Cliente que gerou a petição
            document_id: ID do documento no Google
            link: Link para o documento
        """
        try:
            peticao = PeticaoGerada(
                cliente_id=cliente.id,
                modelo="Suspensão do Direito de Dirigir",
                google_id=document_id,
                link=link
            )
            db.session.add(peticao)
            db.session.commit()
            current_app.logger.info(f"Petição salva no banco: ID {peticao.id}")
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar petição no banco: {e}")
            db.session.rollback()
            # Não re-raise para não quebrar o fluxo principal 