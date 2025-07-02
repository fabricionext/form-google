"""
Serviço para geração de documentos usando templates configurados.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.config.constants import GOOGLE_DRIVE_CONFIG
from app.adapters.enhanced_google_drive import EnhancedGoogleDriveAdapter

logger = logging.getLogger(__name__)


class DocumentGenerationService:
    """Serviço responsável pela geração de documentos a partir de templates."""
    
    def __init__(self):
        self.google_adapter = EnhancedGoogleDriveAdapter()
    
    def generate_document(self, cliente_data: Dict[str, Any], document_type: str) -> Dict[str, Any]:
        """
        Gera um documento a partir dos dados do cliente e tipo de documento.
        
        Args:
            cliente_data: Dados do cliente
            document_type: Tipo de documento (ex: 'FICHA_CADASTRAL', 'CONTRATO_HONORARIOS')
            
        Returns:
            Informações do documento gerado
        """
        try:
            # Determinar se é PF ou PJ
            tipo_pessoa = cliente_data.get('tipo_pessoa', 'FISICA')
            # Lidar com enum e strings
            tipo_str = str(tipo_pessoa).upper()
            if 'FISICA' in tipo_str or 'FÍSICA' in tipo_str:
                pessoa_type = 'PF'
            elif 'JURIDICA' in tipo_str or 'JURÍDICA' in tipo_str:
                pessoa_type = 'PJ'
            else:
                pessoa_type = 'PF'  # default para PF
            
            # Obter template ID
            template_id = self._get_template_id(pessoa_type, document_type)
            if not template_id:
                raise ValueError(f"Template não encontrado para {pessoa_type} - {document_type}")
            
            # Gerar nome do cliente
            if pessoa_type == 'PF':
                client_name = f"{cliente_data.get('primeiro_nome', '')} {cliente_data.get('sobrenome', '')}".strip()
            else:
                client_name = cliente_data.get('razao_social', cliente_data.get('primeiro_nome', ''))
            
            # Organizar pasta do cliente
            client_folder_id = self.google_adapter.organize_by_client(client_name)
            
            # Gerar nome do documento
            document_name = self._generate_document_name(cliente_data, document_type, pessoa_type)
            
            # Copiar template e preencher dados
            document_id = self.google_adapter.copy_document(
                template_id=template_id,
                new_name=document_name,
                target_folder=client_folder_id
            )
            
            # Preencher placeholders
            placeholders_data = self._prepare_placeholders_data(cliente_data, pessoa_type)
            self.google_adapter.fill_placeholders(document_id, placeholders_data)
            
            logger.info(f"Documento gerado com sucesso: {document_name} (ID: {document_id})")
            
            return {
                'success': True,
                'document_id': document_id,
                'document_name': document_name,
                'client_folder_id': client_folder_id,
                'template_used': template_id,
                'type': document_type,
                'pessoa_type': pessoa_type
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar documento: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_template_id(self, pessoa_type: str, document_type: str) -> Optional[str]:
        """Obtém o ID do template baseado no tipo de pessoa e documento."""
        templates = GOOGLE_DRIVE_CONFIG.get('TEMPLATES', {})
        return templates.get(pessoa_type, {}).get(document_type)
    
    def _generate_document_name(self, cliente_data: Dict[str, Any], document_type: str, pessoa_type: str) -> str:
        """
        Gera nome do documento no formato:
        dd-mm-aaaa-Nome Sobrenome-Tipo de Documento-Timestamp
        ou
        dd-mm-aaaa-Razão Social-Tipo de Documento-Timestamp
        """
        # Data atual
        now = datetime.now()
        date_str = now.strftime("%d-%m-%Y")
        timestamp = now.strftime("%H%M%S")
        
        # Nome do cliente
        if pessoa_type == 'PF':
            client_name = f"{cliente_data.get('primeiro_nome', '')} {cliente_data.get('sobrenome', '')}".strip()
        else:
            client_name = cliente_data.get('razao_social', cliente_data.get('primeiro_nome', ''))
        
        # Tipo de documento legível
        document_types_map = {
            'FICHA_CADASTRAL': 'Ficha Cadastral',
            'CONTRATO_HONORARIOS': 'Contrato de Honorários',
            'PROCURACAO_JUDICIAL': 'Procuração Judicial',
            'PROCURACAO_ADMINISTRATIVA': 'Procuração Administrativa',
            'CONTRATO_ADMINISTRATIVO': 'Contrato Administrativo',
            'DECLARACAO_POBREZA': 'Declaração de Pobreza'
        }
        
        doc_type_name = document_types_map.get(document_type, document_type)
        
        # Sanitizar nome
        safe_client_name = self._sanitize_filename(client_name)
        safe_doc_type = self._sanitize_filename(doc_type_name)
        
        return f"{date_str}-{safe_client_name}-{safe_doc_type}-{timestamp}"
    
    def _sanitize_filename(self, filename: str) -> str:
        """Remove caracteres inválidos do nome do arquivo."""
        import re
        # Remove caracteres especiais
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        # Remove espaços extras
        filename = re.sub(r'\s+', ' ', filename).strip()
        return filename[:100]  # Limita tamanho
    
    def _prepare_placeholders_data(self, cliente_data: Dict[str, Any], pessoa_type: str) -> Dict[str, Any]:
        """Prepara dados para substituição de placeholders."""
        now = datetime.now()
        
        # Dados básicos sempre presentes
        placeholders = {
            'data_atual': now.strftime("%d/%m/%Y"),
            'data_atual_extenso': self._format_date_extenso(now),
            'ano_atual': now.strftime("%Y"),
            'mes_atual': now.strftime("%m"),
            'dia_atual': now.strftime("%d")
        }
        
        # Dados específicos por tipo de pessoa
        if pessoa_type == 'PF':
            placeholders.update({
                'cliente_nome': f"{cliente_data.get('primeiro_nome', '')} {cliente_data.get('sobrenome', '')}".strip(),
                'cliente_primeiro_nome': cliente_data.get('primeiro_nome', ''),
                'cliente_sobrenome': cliente_data.get('sobrenome', ''),
                'cliente_cpf': cliente_data.get('cpf', ''),
                'cliente_rg': cliente_data.get('rg', ''),
                'cliente_estado_civil': cliente_data.get('estado_civil', ''),
                'cliente_profissao': cliente_data.get('profissao', ''),
                'cliente_nacionalidade': cliente_data.get('nacionalidade', 'Brasileira')
            })
        else:
            placeholders.update({
                'empresa_razao_social': cliente_data.get('razao_social', ''),
                'empresa_cnpj': cliente_data.get('cnpj', ''),
                'empresa_inscricao_estadual': cliente_data.get('inscricao_estadual', ''),
                'empresa_representante': cliente_data.get('representante_legal', ''),
                'empresa_representante_cpf': cliente_data.get('representante_cpf', '')
            })
        
        # Dados de contato
        placeholders.update({
            'cliente_email': cliente_data.get('email', ''),
            'cliente_telefone': cliente_data.get('telefone_celular', ''),
            'cliente_telefone_fixo': cliente_data.get('telefone_fixo', '')
        })
        
        # Dados de endereço
        endereco_completo = self._format_endereco_completo(cliente_data)
        placeholders.update({
            'cliente_endereco_completo': endereco_completo,
            'cliente_endereco_logradouro': cliente_data.get('endereco_logradouro', ''),
            'cliente_endereco_numero': cliente_data.get('endereco_numero', ''),
            'cliente_endereco_complemento': cliente_data.get('endereco_complemento', ''),
            'cliente_endereco_bairro': cliente_data.get('endereco_bairro', ''),
            'cliente_endereco_cidade': cliente_data.get('endereco_cidade', ''),
            'cliente_endereco_estado': cliente_data.get('endereco_estado', ''),
            'cliente_endereco_cep': cliente_data.get('endereco_cep', '')
        })
        
        return placeholders
    
    def _format_date_extenso(self, date: datetime) -> str:
        """Formata data por extenso."""
        meses = [
            'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
            'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'
        ]
        
        dia = date.day
        mes = meses[date.month - 1]
        ano = date.year
        
        return f"{dia} de {mes} de {ano}"
    
    def _format_endereco_completo(self, cliente_data: Dict[str, Any]) -> str:
        """Formata endereço completo."""
        partes = []
        
        logradouro = cliente_data.get('endereco_logradouro', '')
        numero = cliente_data.get('endereco_numero', '')
        complemento = cliente_data.get('endereco_complemento', '')
        bairro = cliente_data.get('endereco_bairro', '')
        cidade = cliente_data.get('endereco_cidade', '')
        estado = cliente_data.get('endereco_estado', '')
        cep = cliente_data.get('endereco_cep', '')
        
        if logradouro:
            endereco_base = logradouro
            if numero:
                endereco_base += f", {numero}"
            if complemento:
                endereco_base += f", {complemento}"
            partes.append(endereco_base)
        
        if bairro:
            partes.append(bairro)
        
        if cidade and estado:
            partes.append(f"{cidade}/{estado}")
        elif cidade:
            partes.append(cidade)
        
        if cep:
            partes.append(f"CEP: {cep}")
        
        return " - ".join(partes)