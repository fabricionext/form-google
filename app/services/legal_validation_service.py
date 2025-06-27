"""
Legal Validation Service - Business logic for legal document validation.

Handles validation of legal requirements, process numbers, deadlines,
and document-specific business rules.
"""

from typing import List, Dict, Any, Optional
import logging
import re
from datetime import datetime, timedelta

from app.config.constants import DocumentTypes
from app.utils.exceptions import ValidationException


logger = logging.getLogger(__name__)


class LegalValidationService:
    """
    Service for legal document validation.
    
    Provides:
    - Process number format validation
    - Legal deadline calculations and validation
    - Required parties validation
    - Document-specific legal rules
    """
    
    def __init__(self):
        # Process number patterns by type
        self.process_patterns = {
            'CNJ': r'^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$',  # CNJ standard
            'DETRAN': r'^\d{10,15}$',  # DETRAN process numbers
            'MUNICIPAL': r'^[A-Z]{2,5}\d{4,10}$',  # Municipal patterns
            'FEDERAL': r'^\d{4}\.\d{2}\.\d{6}/\d{4}-\d{2}$'  # Federal processes
        }
        
        # Legal deadlines by document type (in days)
        self.legal_deadlines = {
            DocumentTypes.DEFESA_PREVIA.value: 15,
            DocumentTypes.RECURSO_JARI.value: 30,
            DocumentTypes.ACAO_ANULATORIA.value: 120,
            DocumentTypes.TERMO_ACORDO.value: 30
        }
        
        # Required parties by document type
        self.required_parties = {
            DocumentTypes.FICHA_CADASTRAL_PF.value: ['cliente'],
            DocumentTypes.FICHA_CADASTRAL_PJ.value: ['empresa', 'representante'],
            DocumentTypes.DEFESA_PREVIA.value: ['cliente', 'autoridade'],
            DocumentTypes.RECURSO_JARI.value: ['cliente', 'autoridade'],
            DocumentTypes.TERMO_ACORDO.value: ['autor_1', 'autor_2'],
            DocumentTypes.ACAO_ANULATORIA.value: ['autor_1', 'autoridade_1']
        }
    
    def validate_process_number(self, process_number: str) -> bool:
        """
        Validates process number format.
        
        Args:
            process_number: Process number to validate
            
        Returns:
            True if valid format
        """
        if not process_number or not process_number.strip():
            return False
        
        clean_number = self._clean_process_number(process_number)
        
        # Try to match against known patterns
        for pattern_type, pattern in self.process_patterns.items():
            if re.match(pattern, clean_number):
                logger.debug(f"Process number matches {pattern_type} pattern: {clean_number}")
                return True
        
        # Check CNJ check digit if it looks like CNJ format
        if self._looks_like_cnj_format(clean_number):
            return self._validate_cnj_check_digit(clean_number)
        
        logger.warning(f"Process number format not recognized: {process_number}")
        return False
    
    def validate_legal_deadlines(self, document_type: str, dates: Dict[str, Any]) -> List[str]:
        """
        Validates legal deadlines for document type.
        
        Args:
            document_type: Type of legal document
            dates: Dictionary with relevant dates
            
        Returns:
            List of deadline validation errors
        """
        errors = []
        
        deadline_days = self.legal_deadlines.get(document_type)
        if not deadline_days:
            return errors  # No specific deadline for this document type
        
        # Check notification to defense deadline
        if 'data_notificacao' in dates and 'data_defesa' in dates:
            try:
                notif_date = self._parse_date(dates['data_notificacao'])
                defense_date = self._parse_date(dates['data_defesa'])
                
                if notif_date and defense_date:
                    max_defense_date = notif_date + timedelta(days=deadline_days)
                    
                    if defense_date > max_defense_date:
                        errors.append(
                            f"Prazo para {document_type} excedido. "
                            f"Máximo: {max_defense_date.strftime('%d/%m/%Y')}, "
                            f"Informado: {defense_date.strftime('%d/%m/%Y')}"
                        )
                    
                    # Check if defense is too early (before notification)
                    if defense_date <= notif_date:
                        errors.append("Data da defesa deve ser posterior à notificação")
                        
            except ValueError as e:
                errors.append(f"Error parsing dates: {str(e)}")
        
        # Check if deadline is approaching (warning for current date)
        if 'data_notificacao' in dates and not dates.get('data_defesa'):
            try:
                notif_date = self._parse_date(dates['data_notificacao'])
                if notif_date:
                    max_defense_date = notif_date + timedelta(days=deadline_days)
                    days_remaining = (max_defense_date - datetime.now().date()).days
                    
                    if days_remaining < 0:
                        errors.append(f"Prazo para {document_type} já expirou")
                    elif days_remaining <= 3:
                        errors.append(f"Prazo para {document_type} expira em {days_remaining} dias")
                        
            except ValueError:
                pass  # Invalid date format handled elsewhere
        
        return errors
    
    def validate_required_parties(self, document_type: str, parties: Dict[str, Any]) -> List[str]:
        """
        Validates if all required parties are present.
        
        Args:
            document_type: Type of document
            parties: Dictionary with party information
            
        Returns:
            List of missing party errors
        """
        errors = []
        
        required = self.required_parties.get(document_type, [])
        
        for party_type in required:
            if not self._validate_party_presence(party_type, parties):
                errors.append(f"Parte obrigatória não informada: {party_type}")
        
        # Special validation for multi-author documents
        if document_type in [DocumentTypes.TERMO_ACORDO.value, DocumentTypes.ACAO_ANULATORIA.value]:
            errors.extend(self._validate_multi_party_requirements(document_type, parties))
        
        return errors
    
    def validate_document_consistency(self, document_type: str, data: Dict[str, Any]) -> List[str]:
        """
        Validates document-specific consistency rules.
        
        Args:
            document_type: Type of document
            data: Complete document data
            
        Returns:
            List of consistency errors
        """
        errors = []
        
        # Document-specific validations
        if document_type == DocumentTypes.DEFESA_PREVIA.value:
            errors.extend(self._validate_defesa_previa_rules(data))
        elif document_type == DocumentTypes.RECURSO_JARI.value:
            errors.extend(self._validate_recurso_jari_rules(data))
        elif document_type == DocumentTypes.ACAO_ANULATORIA.value:
            errors.extend(self._validate_acao_anulatoria_rules(data))
        elif document_type == DocumentTypes.TERMO_ACORDO.value:
            errors.extend(self._validate_termo_acordo_rules(data))
        
        return errors
    
    def calculate_legal_deadline(self, document_type: str, notification_date: str) -> Optional[datetime]:
        """
        Calculates legal deadline based on notification date.
        
        Args:
            document_type: Type of document
            notification_date: Date of notification
            
        Returns:
            Deadline date or None if no deadline applies
        """
        deadline_days = self.legal_deadlines.get(document_type)
        if not deadline_days:
            return None
        
        try:
            notif_date = self._parse_date(notification_date)
            if notif_date:
                return notif_date + timedelta(days=deadline_days)
        except ValueError:
            logger.warning(f"Invalid notification date format: {notification_date}")
        
        return None
    
    def get_deadline_status(self, document_type: str, notification_date: str) -> Dict[str, Any]:
        """
        Gets comprehensive deadline status information.
        
        Args:
            document_type: Type of document
            notification_date: Date of notification
            
        Returns:
            Dict with deadline information
        """
        deadline = self.calculate_legal_deadline(document_type, notification_date)
        
        if not deadline:
            return {
                'has_deadline': False,
                'deadline_date': None,
                'status': 'no_deadline'
            }
        
        now = datetime.now().date()
        days_remaining = (deadline.date() - now).days
        
        if days_remaining < 0:
            status = 'expired'
        elif days_remaining == 0:
            status = 'expires_today'
        elif days_remaining <= 3:
            status = 'urgent'
        elif days_remaining <= 7:
            status = 'approaching'
        else:
            status = 'ok'
        
        return {
            'has_deadline': True,
            'deadline_date': deadline.date(),
            'days_remaining': days_remaining,
            'status': status,
            'urgency_level': self._get_urgency_level(days_remaining)
        }
    
    def _clean_process_number(self, process_number: str) -> str:
        """Cleans process number for validation."""
        # Remove common separators but keep the structure
        return process_number.strip().replace(' ', '')
    
    def _looks_like_cnj_format(self, process_number: str) -> bool:
        """Checks if process number looks like CNJ format."""
        # CNJ format: NNNNNNN-DD.AAAA.J.TR.OOOO
        return bool(re.match(r'^\d{7}-\d{2}\.\d{4}\.\d{1}\.\d{2}\.\d{4}$', process_number))
    
    def _validate_cnj_check_digit(self, process_number: str) -> bool:
        """Validates CNJ process number check digit."""
        try:
            # Extract sequential number (first 7 digits)
            sequential = process_number[:7]
            # Extract check digits (after first dash)
            check_digits = process_number[8:10]
            
            # CNJ check digit calculation
            weights = [2, 3, 4, 5, 6, 7, 8, 9]
            total = sum(int(digit) * weight for digit, weight in zip(sequential, weights))
            
            remainder1 = total % 11
            first_digit = 0 if remainder1 < 2 else 11 - remainder1
            
            # Second digit calculation includes first digit
            total += first_digit * 2
            remainder2 = total % 11
            second_digit = 0 if remainder2 < 2 else 11 - remainder2
            
            calculated_check = f"{first_digit}{second_digit}"
            
            return check_digits == calculated_check
            
        except (IndexError, ValueError):
            return False
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parses date string in various formats."""
        if not date_str:
            return None
        
        formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y%m%d']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Invalid date format: {date_str}")
    
    def _validate_party_presence(self, party_type: str, parties: Dict[str, Any]) -> bool:
        """Validates if a party type is present with required information."""
        if party_type == 'cliente':
            return bool(parties.get('cliente_nome'))
        elif party_type == 'empresa':
            return bool(parties.get('empresa_nome') and parties.get('empresa_cnpj'))
        elif party_type == 'representante':
            return bool(parties.get('representante_nome'))
        elif party_type == 'autoridade':
            return bool(parties.get('autoridade_nome') or parties.get('autoridade_1_nome'))
        elif party_type.startswith('autor_'):
            author_num = party_type.split('_')[1]
            return bool(parties.get(f'autor_{author_num}_nome'))
        elif party_type.startswith('autoridade_'):
            auth_num = party_type.split('_')[1]
            return bool(parties.get(f'autoridade_{auth_num}_nome'))
        
        return False
    
    def _validate_multi_party_requirements(self, document_type: str, parties: Dict[str, Any]) -> List[str]:
        """Validates requirements for multi-party documents."""
        errors = []
        
        if document_type == DocumentTypes.TERMO_ACORDO.value:
            # Must have exactly 2 authors
            author_count = sum(1 for key in parties if key.startswith('autor_') and key.endswith('_nome') and parties[key])
            if author_count < 2:
                errors.append("Termo de acordo requer pelo menos 2 autores")
            elif author_count > 2:
                errors.append("Termo de acordo suporta no máximo 2 autores")
        
        elif document_type == DocumentTypes.ACAO_ANULATORIA.value:
            # Can have 1-2 authors, 1-3 authorities
            author_count = sum(1 for key in parties if key.startswith('autor_') and key.endswith('_nome') and parties[key])
            auth_count = sum(1 for key in parties if key.startswith('autoridade_') and key.endswith('_nome') and parties[key])
            
            if author_count == 0:
                errors.append("Ação anulatória requer pelo menos 1 autor")
            elif author_count > 2:
                errors.append("Ação anulatória suporta no máximo 2 autores")
            
            if auth_count == 0:
                errors.append("Ação anulatória requer pelo menos 1 autoridade")
            elif auth_count > 3:
                errors.append("Ação anulatória suporta no máximo 3 autoridades")
        
        return errors
    
    def _validate_defesa_previa_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validates specific rules for Defesa Prévia."""
        errors = []
        
        # Must have infraction data
        required_fields = ['infracao_data', 'infracao_local', 'infracao_codigo']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Campo obrigatório para Defesa Prévia: {field}")
        
        return errors
    
    def _validate_recurso_jari_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validates specific rules for Recurso JARI."""
        errors = []
        
        # Must have defense rejection data
        if not data.get('defesa_rejeitada_data'):
            errors.append("Recurso JARI requer data de rejeição da defesa prévia")
        
        return errors
    
    def _validate_acao_anulatoria_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validates specific rules for Ação Anulatória."""
        errors = []
        
        # Must have legal grounds
        if not data.get('fundamento_legal'):
            errors.append("Ação anulatória requer fundamento legal")
        
        # Check competent court
        if not data.get('vara_competente'):
            errors.append("Ação anulatória requer indicação da vara competente")
        
        return errors
    
    def _validate_termo_acordo_rules(self, data: Dict[str, Any]) -> List[str]:
        """Validates specific rules for Termo de Acordo."""
        errors = []
        
        # Must have vehicle data
        if not data.get('veiculo_placa'):
            errors.append("Termo de acordo requer dados do veículo")
        
        # Must have transfer conditions
        if not data.get('condicoes_transferencia'):
            errors.append("Termo de acordo requer condições da transferência")
        
        return errors
    
    def _get_urgency_level(self, days_remaining: int) -> str:
        """Gets urgency level based on days remaining."""
        if days_remaining < 0:
            return 'expired'
        elif days_remaining == 0:
            return 'critical'
        elif days_remaining <= 3:
            return 'high'
        elif days_remaining <= 7:
            return 'medium'
        else:
            return 'low' 