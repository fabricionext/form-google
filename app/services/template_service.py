"""
Template Service - Business logic for template management.

Handles template creation, synchronization with Google Docs,
placeholder extraction and validation.
"""

from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.repositories.template_repository import TemplateRepository
from app.repositories.placeholder_repository import PlaceholderRepository
from app.adapters.google_drive import GoogleDriveAdapter
from app.utils.exceptions import (
    TemplateNotFoundException,
    TemplateValidationException,
    GoogleDriveException
)
from app.config.constants import DocumentTypes


logger = logging.getLogger(__name__)


class TemplateService:
    """
    Service for template management and synchronization.
    
    Handles business logic for template operations including:
    - Template creation and validation
    - Synchronization with Google Docs
    - Placeholder extraction and management
    - Template metadata operations
    """
    
    def __init__(self):
        self.template_repo = TemplateRepository()
        self.placeholder_repo = PlaceholderRepository()
        self.google_adapter = GoogleDriveAdapter()
    
    def create_template(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new template with validation.
        
        Args:
            data: Template data including name, description, google_doc_id
            
        Returns:
            Dict containing created template data
            
        Raises:
            TemplateValidationException: If template data is invalid
            GoogleDriveException: If Google Docs integration fails
        """
        logger.info(f"Creating template: {data.get('nome', 'Unknown')}")
        
        try:
            # Validate Google Doc exists and is accessible
            if 'google_doc_id' in data:
                self._validate_google_doc_access(data['google_doc_id'])
            
            # Create template
            template = self.template_repo.create(data)
            
            # Extract and sync placeholders if Google Doc provided
            if template.google_doc_id:
                self.sync_placeholders(template.id)
            
            logger.info(f"Template created successfully: ID {template.id}")
            return self.template_repo.to_dict(template)
            
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            raise TemplateValidationException(f"Failed to create template: {str(e)}")
    
    def sync_placeholders(self, template_id: int) -> Dict[str, Any]:
        """
        Synchronizes placeholders from Google Docs template.
        
        Args:
            template_id: ID of the template to sync
            
        Returns:
            Dict with sync statistics
            
        Raises:
            TemplateNotFoundException: If template not found
            GoogleDriveException: If Google Docs access fails
        """
        logger.info(f"Syncing placeholders for template {template_id}")
        
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundException(f"Template {template_id} not found")
        
        if not template.google_doc_id:
            raise TemplateValidationException("Template has no Google Doc associated")
        
        try:
            # Extract placeholders from Google Doc
            placeholders = self.google_adapter.extract_placeholders(template.google_doc_id)
            
            # Update database with new placeholders
            sync_result = self._update_placeholders(template_id, placeholders)
            
            # Update template sync timestamp
            self.template_repo.update(template_id, {
                'last_sync': datetime.utcnow(),
                'status': 'active'
            })
            
            logger.info(f"Placeholder sync completed for template {template_id}")
            return sync_result
            
        except Exception as e:
            logger.error(f"Error syncing placeholders: {str(e)}")
            raise GoogleDriveException(f"Failed to sync placeholders: {str(e)}")
    
    def validate_template(self, template_id: int) -> Dict[str, Any]:
        """
        Validates template structure and placeholders.
        
        Args:
            template_id: ID of template to validate
            
        Returns:
            Dict with validation results
            
        Raises:
            TemplateNotFoundException: If template not found
        """
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundException(f"Template {template_id} not found")
        
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'stats': {}
        }
        
        try:
            # Validate Google Doc accessibility
            if template.google_doc_id:
                if not self.google_adapter.document_exists(template.google_doc_id):
                    validation_result['errors'].append("Google Doc not accessible")
                    validation_result['valid'] = False
            
            # Validate placeholders
            placeholders = self.placeholder_repo.find_by_template_id(template_id)
            validation_result['stats']['total_placeholders'] = len(placeholders)
            
            # Check for required placeholders based on document type
            required_placeholders = self._get_required_placeholders(template.tipo)
            missing_required = [p for p in required_placeholders 
                              if not any(ph.chave == p for ph in placeholders)]
            
            if missing_required:
                validation_result['warnings'].extend([
                    f"Missing recommended placeholder: {p}" for p in missing_required
                ])
            
            # Check for duplicate placeholders
            placeholder_keys = [p.chave for p in placeholders]
            duplicates = [k for k in placeholder_keys if placeholder_keys.count(k) > 1]
            if duplicates:
                validation_result['errors'].extend([
                    f"Duplicate placeholder: {d}" for d in set(duplicates)
                ])
                validation_result['valid'] = False
            
            logger.info(f"Template validation completed for {template_id}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating template: {str(e)}")
            validation_result['valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
            return validation_result
    
    def get_template_metadata(self, template_id: int) -> Dict[str, Any]:
        """
        Gets comprehensive template metadata.
        
        Args:
            template_id: ID of template
            
        Returns:
            Dict with template metadata and statistics
            
        Raises:
            TemplateNotFoundException: If template not found
        """
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundException(f"Template {template_id} not found")
        
        # Get basic template data
        metadata = self.template_repo.to_dict(template)
        
        # Add placeholder statistics
        placeholders = self.placeholder_repo.find_by_template_id(template_id)
        metadata['placeholder_stats'] = {
            'total': len(placeholders),
            'by_type': self._group_placeholders_by_type(placeholders),
            'required_count': len([p for p in placeholders if p.obrigatorio])
        }
        
        # Add usage statistics
        metadata['usage_stats'] = self.template_repo.get_usage_stats(template_id)
        
        # Add sync status
        if template.google_doc_id:
            metadata['sync_status'] = {
                'last_sync': template.last_sync,
                'google_doc_accessible': self.google_adapter.document_exists(template.google_doc_id)
            }
        
        return metadata
    
    def get_templates_by_type(self, document_type: str) -> List[Dict[str, Any]]:
        """
        Gets all templates filtered by document type.
        
        Args:
            document_type: Type of document (from DocumentTypes enum)
            
        Returns:
            List of template dictionaries
        """
        # Validate document type
        if document_type not in [dt.value for dt in DocumentTypes]:
            raise TemplateValidationException(f"Invalid document type: {document_type}")
        
        templates = self.template_repo.find_by_type(document_type)
        return [self.template_repo.to_dict(t) for t in templates]
    
    def get_active_templates(self) -> List[Dict[str, Any]]:
        """
        Gets all active templates with basic metadata.
        
        Returns:
            List of active template dictionaries
        """
        templates = self.template_repo.find_active()
        return [self.template_repo.to_dict(t) for t in templates]
    
    def _validate_google_doc_access(self, google_doc_id: str) -> bool:
        """
        Validates that Google Doc is accessible.
        
        Args:
            google_doc_id: Google Doc ID to validate
            
        Returns:
            True if accessible
            
        Raises:
            GoogleDriveException: If doc is not accessible
        """
        if not self.google_adapter.document_exists(google_doc_id):
            raise GoogleDriveException(f"Google Doc {google_doc_id} not accessible")
        return True
    
    def _update_placeholders(self, template_id: int, placeholders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Updates placeholders for a template.
        
        Args:
            template_id: Template ID
            placeholders: List of placeholder data
            
        Returns:
            Dict with update statistics
        """
        current_placeholders = self.placeholder_repo.find_by_template_id(template_id)
        current_keys = {p.chave for p in current_placeholders}
        new_keys = {p['chave'] for p in placeholders}
        
        # Statistics
        added = new_keys - current_keys
        removed = current_keys - new_keys
        updated = new_keys & current_keys
        
        # Remove obsolete placeholders
        for key in removed:
            placeholder = next(p for p in current_placeholders if p.chave == key)
            self.placeholder_repo.delete(placeholder.id)
        
        # Add new placeholders
        for placeholder_data in placeholders:
            placeholder_data['template_id'] = template_id
            if placeholder_data['chave'] in added:
                self.placeholder_repo.create(placeholder_data)
            elif placeholder_data['chave'] in updated:
                # Update existing
                existing = next(p for p in current_placeholders 
                              if p.chave == placeholder_data['chave'])
                self.placeholder_repo.update(existing.id, placeholder_data)
        
        return {
            'added': len(added),
            'removed': len(removed),
            'updated': len(updated),
            'total': len(placeholders)
        }
    
    def _get_required_placeholders(self, document_type: str) -> List[str]:
        """
        Gets list of required placeholders for document type.
        
        Args:
            document_type: Type of document
            
        Returns:
            List of required placeholder keys
        """
        required_map = {
            DocumentTypes.FICHA_CADASTRAL_PF.value: [
                'cliente_nome', 'cliente_cpf', 'cliente_telefone'
            ],
            DocumentTypes.FICHA_CADASTRAL_PJ.value: [
                'empresa_nome', 'empresa_cnpj', 'representante_nome'
            ],
            DocumentTypes.DEFESA_PREVIA.value: [
                'cliente_nome', 'processo_numero', 'infracao_data'
            ],
            DocumentTypes.ACAO_ANULATORIA.value: [
                'autor_1_nome', 'autoridade_1_nome', 'processo_numero'
            ]
        }
        
        return required_map.get(document_type, [])
    
    def _group_placeholders_by_type(self, placeholders: List[Any]) -> Dict[str, int]:
        """
        Groups placeholders by type for statistics.
        
        Args:
            placeholders: List of placeholder objects
            
        Returns:
            Dict with counts by type
        """
        type_counts = {}
        for placeholder in placeholders:
            tipo = placeholder.tipo or 'text'
            type_counts[tipo] = type_counts.get(tipo, 0) + 1
        
        return type_counts 