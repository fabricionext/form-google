"""
Sistema de Gerenciamento Robusto de Formulários
================================================

Este módulo implementa uma estrutura robusta para criação, validação e
gerenciamento de formulários dinâmicos, seguindo as orientações do .windsurfrules.

Características:
- Prevenção de erros "unhashable type"
- Validação robusta de dados
- Fallbacks automáticos
- Logging detalhado para debugging
- Estrutura mais estável e segura
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union, Any
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from app.peticionador.models import (
    FormularioGerado, 
    PeticaoModelo, 
    PeticaoPlaceholder,
    FormularioPlaceholder
)
from app.peticionador.utils import (
    safe_extract_placeholder_keys,
    validate_placeholder_format,
    clean_placeholder_key,
    handle_placeholder_extraction_error
)

logger = logging.getLogger(__name__)


class FormularioManagerError(Exception):
    """Exceção base para erros do FormularioManager."""
    pass


class PlaceholderExtractionError(FormularioManagerError):
    """Erro na extração de placeholders."""
    pass


class FormularioValidationError(FormularioManagerError):
    """Erro na validação de formulário.""" 
    pass


class FormularioManager:
    """
    Gerenciador robusto para formulários dinâmicos.
    
    Implementa padrões seguros para evitar erros comuns e
    providencia fallbacks automáticos.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def validate_formulario_slug(self, slug: str) -> bool:
        """
        Valida se um slug de formulário é válido.
        
        Args:
            slug: Slug a ser validado
            
        Returns:
            bool: True se válido, False caso contrário
        """
        if not slug or not isinstance(slug, str):
            return False
        
        # Validar formato do slug
        if not re.match(r'^[a-zA-Z0-9\-_]+$', slug):
            return False
        
        # Verificar se não está vazio após strip
        if not slug.strip():
            return False
        
        return True
    
    def safe_get_formulario(self, slug: str) -> Optional[FormularioGerado]:
        """
        Obtém um formulário de forma segura.
        
        Args:
            slug: Slug do formulário
            
        Returns:
            FormularioGerado ou None se não encontrado
        """
        try:
            if not self.validate_formulario_slug(slug):
                self.logger.warning(f"Slug inválido fornecido: {slug}")
                return None
            
            formulario = FormularioGerado.query.filter_by(slug=slug).first()
            
            if formulario:
                self.logger.info(f"Formulário encontrado: {formulario.nome} (ID: {formulario.id})")
            else:
                self.logger.warning(f"Formulário não encontrado para slug: {slug}")
                self._log_available_formularios()
            
            return formulario
            
        except SQLAlchemyError as e:
            self.logger.error(f"Erro de banco ao buscar formulário {slug}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado ao buscar formulário {slug}: {e}")
            return None
    
    def _log_available_formularios(self, limit: int = 5):
        """Log dos formulários disponíveis para debugging."""
        try:
            formularios = FormularioGerado.query.limit(limit).all()
            if formularios:
                self.logger.info("Formulários disponíveis:")
                for form in formularios:
                    self.logger.info(f"  - {form.slug} ({form.nome})")
            else:
                self.logger.warning("Nenhum formulário encontrado no banco de dados")
        except Exception as e:
            self.logger.error(f"Erro ao listar formulários disponíveis: {e}")
    
    def safe_extract_placeholders_from_document(self, document_data: Any) -> List[str]:
        """
        Extrai placeholders de um documento de forma ultra-segura.
        
        Args:
            document_data: Dados do documento (pode ser qualquer formato)
            
        Returns:
            Lista de strings com placeholders
        """
        try:
            # Se já é uma lista de strings, retornar diretamente
            if isinstance(document_data, list) and all(isinstance(item, str) for item in document_data):
                return [item.strip() for item in document_data if item.strip()]
            
            # Usar a função safe_extract_placeholder_keys
            chaves = safe_extract_placeholder_keys(document_data)
            
            # Validação extra: garantir que são apenas strings válidas
            chaves_validadas = []
            for chave in chaves:
                if isinstance(chave, str) and chave.strip():
                    chave_limpa = clean_placeholder_key(chave)
                    if validate_placeholder_format(chave_limpa):
                        chaves_validadas.append(chave_limpa)
                    else:
                        self.logger.warning(f"Placeholder com formato inválido ignorado: {chave}")
                elif isinstance(chave, dict):
                    # Tentar extrair de dicionários
                    for key in ['key', 'chave', 'placeholder', 'name']:
                        if key in chave and isinstance(chave[key], str):
                            chave_str = clean_placeholder_key(chave[key])
                            if validate_placeholder_format(chave_str):
                                chaves_validadas.append(chave_str)
                            break
                    else:
                        self.logger.warning(f"Dicionário sem chave válida ignorado: {chave}")
                else:
                    self.logger.warning(f"Tipo de placeholder inválido ignorado: {type(chave)} - {chave}")
            
            # Remover duplicatas preservando ordem
            chaves_unicas = []
            seen = set()
            for chave in chaves_validadas:
                if chave not in seen:
                    chaves_unicas.append(chave)
                    seen.add(chave)
            
            self.logger.info(f"Extraídos {len(chaves_unicas)} placeholders válidos de {len(chaves)} originais")
            return chaves_unicas
            
        except Exception as e:
            self.logger.error(f"Erro na extração de placeholders: {e}")
            return []
    
    def safe_synchronize_placeholders(self, modelo_id: int, placeholders_data: Any) -> Dict[str, Any]:
        """
        Sincroniza placeholders de forma ultra-segura.
        
        Args:
            modelo_id: ID do modelo
            placeholders_data: Dados dos placeholders
            
        Returns:
            Dict com resultado da sincronização
        """
        try:
            # Extrair placeholders de forma segura
            chaves = self.safe_extract_placeholders_from_document(placeholders_data)
            
            if not chaves:
                self.logger.warning(f"Nenhum placeholder válido encontrado para modelo {modelo_id}")
                return {
                    'success': False,
                    'error': 'Nenhum placeholder válido encontrado',
                    'criados': 0,
                    'atualizados': 0,
                    'removidos': 0
                }
            
            # Estatísticas
            criados = 0
            atualizados = 0
            removidos = 0
            
            # Converter para set de forma segura (sabemos que são strings)
            chaves_documento = set(chaves)
            
            # Remover placeholders que não existem mais no documento
            placeholders_antigos = PeticaoPlaceholder.query.filter_by(modelo_id=modelo_id).all()
            for placeholder_antigo in placeholders_antigos:
                if placeholder_antigo.chave not in chaves_documento:
                    db.session.delete(placeholder_antigo)
                    removidos += 1
                    self.logger.info(f"Placeholder removido: {placeholder_antigo.chave}")
            
            # Criar ou atualizar placeholders
            for idx, chave in enumerate(chaves, start=1):
                existente = PeticaoPlaceholder.query.filter_by(
                    modelo_id=modelo_id, 
                    chave=chave
                ).first()
                
                if not existente:
                    # Criar novo placeholder
                    novo_placeholder = PeticaoPlaceholder(
                        modelo_id=modelo_id,
                        chave=chave,
                        categoria=self._categorize_placeholder(chave),
                        tipo_campo='string',
                        label_form=self._generate_label_from_key(chave),
                        ordem=idx,
                        obrigatorio=self._is_placeholder_required(chave)
                    )
                    db.session.add(novo_placeholder)
                    criados += 1
                    self.logger.info(f"Placeholder criado: {chave}")
                else:
                    # Atualizar existente se necessário
                    if existente.ordem != idx:
                        existente.ordem = idx
                        atualizados += 1
                        self.logger.info(f"Placeholder atualizado: {chave}")
            
            # Commit das mudanças
            db.session.commit()
            
            resultado = {
                'success': True,
                'criados': criados,
                'atualizados': atualizados,
                'removidos': removidos,
                'total_placeholders': len(chaves)
            }
            
            self.logger.info(f"Sincronização concluída para modelo {modelo_id}: {resultado}")
            return resultado
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Erro de banco na sincronização: {e}")
            return {
                'success': False,
                'error': f'Erro de banco de dados: {str(e)}',
                'criados': 0,
                'atualizados': 0,
                'removidos': 0
            }
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Erro inesperado na sincronização: {e}")
            return {
                'success': False,
                'error': f'Erro interno: {str(e)}',
                'criados': 0,
                'atualizados': 0,
                'removidos': 0
            }
    
    def _categorize_placeholder(self, chave: str) -> str:
        """Categoriza um placeholder baseado em sua chave."""
        chave_lower = chave.lower()
        
        # Mapeamento de categorias
        if any(keyword in chave_lower for keyword in ['cpf', 'rg', 'nome', 'email', 'telefone']):
            return 'cliente'
        elif any(keyword in chave_lower for keyword in ['endereco', 'cep', 'logradouro', 'bairro']):
            return 'endereco'
        elif any(keyword in chave_lower for keyword in ['processo', 'numero_processo', 'comarca']):
            return 'processo'
        elif any(keyword in chave_lower for keyword in ['autor', 'requerente']):
            return 'polo_ativo'
        elif any(keyword in chave_lower for keyword in ['reu', 'requerido']):
            return 'polo_passivo'
        elif any(keyword in chave_lower for keyword in ['autoridade', 'orgao', 'transito']):
            return 'autoridades'
        else:
            return 'outros'
    
    def _generate_label_from_key(self, chave: str) -> str:
        """Gera um label legível a partir da chave."""
        # Converter underscores e camelCase para espaços
        label = re.sub(r'[_-]', ' ', chave)
        label = re.sub(r'([a-z])([A-Z])', r'\1 \2', label)
        
        # Capitalizar palavras
        words = label.split()
        capitalized = []
        for word in words:
            if word.isdigit():
                capitalized.append(word)
            else:
                capitalized.append(word.capitalize())
        
        return ' '.join(capitalized)
    
    def _is_placeholder_required(self, chave: str) -> bool:
        """Determina se um placeholder é obrigatório."""
        chave_lower = chave.lower()
        required_keywords = ['cpf', 'nome', 'numero_processo']
        return any(keyword in chave_lower for keyword in required_keywords)
    
    def validate_form_submission(self, form_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida dados de submissão de formulário.
        
        Args:
            form_data: Dados do formulário
            
        Returns:
            Tuple (is_valid, error_messages)
        """
        errors = []
        
        # Validações básicas
        if not isinstance(form_data, dict):
            errors.append("Dados do formulário devem ser um dicionário")
            return False, errors
        
        # Verificar campos obrigatórios básicos
        required_fields = ['csrf_token']  # Campos sempre necessários
        for field in required_fields:
            if field not in form_data or not form_data[field]:
                errors.append(f"Campo obrigatório ausente: {field}")
        
        # Validar tipos de dados
        for key, value in form_data.items():
            if key == 'csrf_token':
                continue
            
            # CPF validation
            if 'cpf' in key.lower() and value:
                if not self._validate_cpf_format(str(value)):
                    errors.append(f"CPF inválido no campo {key}")
            
            # Email validation
            if 'email' in key.lower() and value:
                if not self._validate_email_format(str(value)):
                    errors.append(f"Email inválido no campo {key}")
        
        return len(errors) == 0, errors
    
    def _validate_cpf_format(self, cpf: str) -> bool:
        """Valida formato básico de CPF."""
        if not cpf:
            return True  # CPF vazio é válido (campo opcional)
        
        # Remover formatação
        cpf_numbers = re.sub(r'\D', '', cpf)
        return len(cpf_numbers) == 11
    
    def _validate_email_format(self, email: str) -> bool:
        """Valida formato básico de email."""
        if not email:
            return True  # Email vazio é válido (campo opcional)
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    def create_formulario_slug(self, nome: str, modelo_id: int) -> str:
        """
        Cria um slug único para um formulário.
        
        Args:
            nome: Nome do formulário
            modelo_id: ID do modelo
            
        Returns:
            String com slug único
        """
        # Normalizar nome
        slug_base = re.sub(r'[^\w\s-]', '', nome.lower())
        slug_base = re.sub(r'[\s_-]+', '-', slug_base)
        slug_base = slug_base.strip('-')
        
        # Adicionar timestamp para unicidade
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # Gerar hash baseado no conteúdo
        import hashlib
        content_hash = hashlib.md5(f"{nome}{modelo_id}{timestamp}".encode()).hexdigest()[:8]
        
        slug = f"{slug_base}-{timestamp}-{content_hash}"
        
        # Garantir que não existe
        counter = 1
        original_slug = slug
        while FormularioGerado.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        return slug


# Instância global do manager
formulario_manager = FormularioManager()