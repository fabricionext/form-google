"""
Document Service - Main business logic for document generation.

Orchestrates the complete document generation process including
template processing, placeholder filling, naming, and organization.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import json

from app.repositories.document_repository import DocumentRepository
from app.repositories.template_repository import TemplateRepository
from app.repositories.placeholder_repository import PlaceholderRepository
from app.services.entity_service import EntityService
from app.services.advanced_placeholder_service import AdvancedPlaceholderService
from app.services.document_naming_service import DocumentNamingService
from app.services.legal_validation_service import LegalValidationService
from app.adapters.enhanced_google_drive import EnhancedGoogleDriveAdapter
from app.utils.exceptions import (
    DocumentGenerationException,
    TemplateNotFoundException,
    ValidationException,
    BusinessException
)
from app.config.constants import DocumentTypes, DocumentStatus


logger = logging.getLogger(__name__)


class DocumentService:
    """
    Main service for document generation and management.
    
    Orchestrates:
    - Document generation from templates
    - Data validation and processing
    - Google Drive integration
    - File naming and organization
    - Status tracking and error handling
    """
    
    def __init__(self):
        self.document_repo = DocumentRepository()
        self.template_repo = TemplateRepository()
        self.placeholder_repo = PlaceholderRepository()
        self.entity_service = EntityService()
        self.placeholder_service = AdvancedPlaceholderService()
        self.naming_service = DocumentNamingService()
        self.validation_service = LegalValidationService()
        self.google_adapter = EnhancedGoogleDriveAdapter()
    
    def generate_document(self, template_id: int, data: Dict[str, Any], 
                         options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generates a complete document from template and data.
        
        Args:
            template_id: ID of template to use
            data: Data to fill placeholders
            options: Additional options like target_folder, custom_name, etc.
            
        Returns:
            Dict with generation results and document metadata
            
        Raises:
            DocumentGenerationException: If generation fails
            TemplateNotFoundException: If template not found
            ValidationException: If data validation fails
        """
        logger.info(f"Starting document generation for template {template_id}")
        
        options = options or {}
        generation_start = datetime.utcnow()
        
        try:
            # 1. Load and validate template
            template = self._load_and_validate_template(template_id)
            
            # 2. Process and validate input data
            processed_data = self._process_input_data(data, template_id)
            
            # 3. Validate business rules
            validation_errors = self._validate_business_rules(processed_data, template)
            if validation_errors:
                raise ValidationException(f"Validation errors: {'; '.join(validation_errors)}")
            
            # 4. Generate document name
            document_name = self._generate_document_name(template, processed_data, options)
            
            # 5. Organize folder structure
            target_folder = self._organize_folder_structure(processed_data, template.tipo, options)
            
            # 6. Create document record (tracking)
            document_record = self._create_document_record(
                template_id, processed_data, document_name, target_folder
            )
            
            # 7. Generate document in Google Drive
            google_doc_id = self._generate_google_document(
                template, processed_data, document_name, target_folder, options
            )
            
            # 8. Update document record with success
            generation_time = (datetime.utcnow() - generation_start).total_seconds()
            final_document = self._finalize_document_record(
                document_record['id'], google_doc_id, generation_time
            )
            
            logger.info(f"Document generation completed: {document_name} (ID: {google_doc_id})")
            
            return {
                'success': True,
                'document_id': google_doc_id,
                'document_name': document_name,
                'target_folder': target_folder,
                'generation_time': generation_time,
                'metadata': final_document
            }
            
        except Exception as e:
            # Log error and update document record if it exists
            logger.error(f"Document generation failed: {str(e)}")
            
            if 'document_record' in locals():
                self._handle_generation_error(document_record['id'], str(e))
            
            if isinstance(e, (TemplateNotFoundException, ValidationException)):
                raise
            else:
                raise DocumentGenerationException(f"Failed to generate document: {str(e)}")
    
    def validate_document_data(self, template_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates document data against template requirements.
        
        Args:
            template_id: ID of template
            data: Data to validate
            
        Returns:
            Dict with validation results
        """
        logger.debug(f"Validating document data for template {template_id}")
        
        try:
            template = self.template_repo.find_by_id(template_id)
            if not template:
                raise TemplateNotFoundException(f"Template {template_id} not found")
            
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'suggestions': []
            }
            
            # Basic data validation
            basic_errors = self._validate_basic_data_structure(data)
            validation_result['errors'].extend(basic_errors)
            
            # Template-specific validation
            template_errors = self._validate_template_requirements(template_id, data)
            validation_result['errors'].extend(template_errors)
            
            # Business rule validation
            business_errors = self.validation_service.validate_required_parties(
                template.tipo, data
            )
            validation_result['errors'].extend(business_errors)
            
            # Cross-field validation
            related_errors = self.placeholder_service.validate_related_fields(data, template_id)
            validation_result['errors'].extend(related_errors)
            
            # Entity validation (clients, authorities)
            entity_warnings = self._validate_entities(data)
            validation_result['warnings'].extend(entity_warnings)
            
            # Generate suggestions
            suggestions = self._generate_improvement_suggestions(data, template)
            validation_result['suggestions'].extend(suggestions)
            
            # Set overall validity
            validation_result['valid'] = len(validation_result['errors']) == 0
            
            logger.debug(f"Validation completed: {len(validation_result['errors'])} errors, "
                        f"{len(validation_result['warnings'])} warnings")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating document data: {str(e)}")
            return {
                'valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'suggestions': []
            }
    
    def save_generated_document(self, document_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Saves metadata for a generated document.
        
        Args:
            document_id: Google Drive document ID
            metadata: Additional metadata to save
            
        Returns:
            Updated document record
        """
        logger.info(f"Saving metadata for document {document_id}")
        
        try:
            # Find existing document record
            document = self.document_repo.find_by_google_doc_id(document_id)
            
            if document:
                # Update existing record
                update_data = {
                    'metadata': json.dumps(metadata),
                    'updated_at': datetime.utcnow()
                }
                updated_document = self.document_repo.update(document.id, update_data)
            else:
                # Create new record
                document_data = {
                    'google_doc_id': document_id,
                    'nome': metadata.get('name', 'Unknown Document'),
                    'tipo': metadata.get('type', 'Unknown'),
                    'status': DocumentStatus.COMPLETED.value,
                    'metadata': json.dumps(metadata)
                }
                updated_document = self.document_repo.create(document_data)
            
            logger.info(f"Document metadata saved: {document_id}")
            return self.document_repo.to_dict(updated_document)
            
        except Exception as e:
            logger.error(f"Error saving document metadata: {str(e)}")
            raise BusinessException(f"Failed to save document metadata: {str(e)}")
    
    def get_document_history(self, client_cpf: str = None, template_id: int = None, 
                           days: int = 30) -> List[Dict[str, Any]]:
        """
        Gets document generation history with filters.
        
        Args:
            client_cpf: Optional client CPF filter
            template_id: Optional template filter
            days: Number of days to look back
            
        Returns:
            List of document history records
        """
        logger.debug(f"Getting document history: CPF={client_cpf}, template={template_id}, days={days}")
        
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            documents = self.document_repo.find_recent(
                since_date=since_date,
                template_id=template_id,
                client_filter=client_cpf
            )
            
            history = []
            for doc in documents:
                doc_dict = self.document_repo.to_dict(doc)
                
                # Add template information
                if doc.template_id:
                    template = self.template_repo.find_by_id(doc.template_id)
                    if template:
                        doc_dict['template_name'] = template.nome
                
                # Parse metadata if available
                if doc.metadata:
                    try:
                        doc_dict['parsed_metadata'] = json.loads(doc.metadata)
                    except:
                        pass
                
                history.append(doc_dict)
            
            logger.info(f"Retrieved {len(history)} document history records")
            return history
            
        except Exception as e:
            logger.error(f"Error getting document history: {str(e)}")
            return []
    
    def get_generation_statistics(self, period_days: int = 30) -> Dict[str, Any]:
        """
        Gets statistics about document generation.
        
        Args:
            period_days: Period to analyze
            
        Returns:
            Dict with generation statistics
        """
        logger.debug(f"Getting generation statistics for {period_days} days")
        
        try:
            since_date = datetime.utcnow() - timedelta(days=period_days)
            stats = self.document_repo.get_generation_stats(since_date)
            
            # Enhance with template information
            template_stats = {}
            for template_id, count in stats.get('by_template', {}).items():
                template = self.template_repo.find_by_id(int(template_id))
                template_name = template.nome if template else f"Template {template_id}"
                template_stats[template_name] = count
            
            enhanced_stats = {
                'period_days': period_days,
                'total_documents': stats.get('total', 0),
                'successful': stats.get('successful', 0),
                'failed': stats.get('failed', 0),
                'success_rate': stats.get('success_rate', 0),
                'by_template': template_stats,
                'by_status': stats.get('by_status', {}),
                'average_generation_time': stats.get('avg_generation_time', 0),
                'generated_at': datetime.utcnow().isoformat()
            }
            
            return enhanced_stats
            
        except Exception as e:
            logger.error(f"Error getting generation statistics: {str(e)}")
            return {
                'error': str(e),
                'period_days': period_days,
                'generated_at': datetime.utcnow().isoformat()
            }
    
    def _load_and_validate_template(self, template_id: int) -> Any:
        """Loads and validates template."""
        template = self.template_repo.find_by_id(template_id)
        if not template:
            raise TemplateNotFoundException(f"Template {template_id} not found")
        
        if template.status != 'active':
            raise ValidationException(f"Template {template_id} is not active")
        
        if not template.google_doc_id:
            raise ValidationException(f"Template {template_id} has no Google Doc associated")
        
        return template
    
    def _process_input_data(self, data: Dict[str, Any], template_id: int) -> Dict[str, Any]:
        """Processes and enhances input data."""
        # Process calculated fields
        enhanced_data = self.placeholder_service.process_calculated_fields(data)
        
        # Process numbered placeholders if applicable
        numbered_info = self.placeholder_service.process_numbered_placeholders(template_id)
        if numbered_info['total_entities'] > 0:
            enhanced_data['_numbered_entities'] = numbered_info
        
        return enhanced_data
    
    def _validate_business_rules(self, data: Dict[str, Any], template: Any) -> List[str]:
        """Validates business rules specific to document type."""
        errors = []
        
        # Legal validation
        legal_errors = self.validation_service.validate_required_parties(template.tipo, data)
        errors.extend(legal_errors)
        
        # Process number validation if present
        if 'processo_numero' in data:
            if not self.validation_service.validate_process_number(data['processo_numero']):
                errors.append("Número de processo inválido")
        
        # Date validation
        date_errors = self.validation_service.validate_legal_deadlines(template.tipo, data)
        errors.extend(date_errors)
        
        return errors
    
    def _generate_document_name(self, template: Any, data: Dict[str, Any], 
                              options: Dict[str, Any]) -> str:
        """Generates standardized document name."""
        # Extract authors
        authors = []
        
        # Single author case
        if 'cliente_nome' in data:
            authors.append({'nome': data['cliente_nome']})
        
        # Multiple authors case
        i = 1
        while f'autor_{i}_nome' in data:
            authors.append({'nome': data[f'autor_{i}_nome']})
            i += 1
        
        # Fallback
        if not authors:
            authors = [{'nome': 'Cliente'}]
        
        return self.naming_service.generate_filename(
            document_type=template.tipo,
            authors=authors,
            **options.get('naming_options', {})
        )
    
    def _organize_folder_structure(self, data: Dict[str, Any], document_type: str, 
                                 options: Dict[str, Any]) -> str:
        """Organizes folder structure for document."""
        if options.get('target_folder'):
            return options['target_folder']
        
        # Extract client information
        client_name = data.get('cliente_nome') or data.get('autor_1_nome', 'Cliente')
        client_cpf = data.get('cliente_cpf') or data.get('autor_1_cpf')
        
        # Create/get client folder
        client_folder = self.google_adapter.organize_by_client(client_name, client_cpf)
        
        # Create/get document type subfolder
        doc_folder = self.google_adapter.organize_by_document_type(client_folder, document_type)
        
        return doc_folder
    
    def _create_document_record(self, template_id: int, data: Dict[str, Any], 
                              document_name: str, target_folder: str) -> Dict[str, Any]:
        """Creates initial document record for tracking."""
        document_data = {
            'template_id': template_id,
            'nome': document_name,
            'tipo': data.get('document_type', 'Unknown'),
            'status': DocumentStatus.PROCESSING.value,
            'target_folder_id': target_folder,
            'metadata': json.dumps({
                'client_info': {
                    'nome': data.get('cliente_nome') or data.get('autor_1_nome'),
                    'cpf': data.get('cliente_cpf') or data.get('autor_1_cpf')
                },
                'generation_start': datetime.utcnow().isoformat()
            })
        }
        
        document = self.document_repo.create(document_data)
        return self.document_repo.to_dict(document)
    
    def _generate_google_document(self, template: Any, data: Dict[str, Any], 
                                document_name: str, target_folder: str, 
                                options: Dict[str, Any]) -> str:
        """Generates document in Google Drive."""
        # Copy template
        google_doc_id = self.google_adapter.copy_document(
            template.google_doc_id,
            document_name,
            target_folder
        )
        
        # Fill placeholders
        self.google_adapter.fill_placeholders(google_doc_id, data)
        
        # Handle conditional blocks if needed
        if options.get('process_conditional_blocks', True):
            # This would require additional Google Docs API operations
            pass
        
        # Handle images if provided
        if 'images' in options:
            # This would be implemented with proper image handling
            pass
        
        return google_doc_id
    
    def _finalize_document_record(self, record_id: int, google_doc_id: str, 
                                generation_time: float) -> Dict[str, Any]:
        """Finalizes document record after successful generation."""
        update_data = {
            'google_doc_id': google_doc_id,
            'status': DocumentStatus.COMPLETED.value,
            'generation_time': generation_time,
            'completed_at': datetime.utcnow()
        }
        
        updated_document = self.document_repo.update(record_id, update_data)
        return self.document_repo.to_dict(updated_document)
    
    def _handle_generation_error(self, record_id: int, error_message: str) -> None:
        """Handles error during document generation."""
        try:
            update_data = {
                'status': DocumentStatus.FAILED.value,
                'error_message': error_message,
                'failed_at': datetime.utcnow()
            }
            self.document_repo.update(record_id, update_data)
        except Exception as e:
            logger.error(f"Error updating document record {record_id}: {str(e)}")
    
    def _validate_basic_data_structure(self, data: Dict[str, Any]) -> List[str]:
        """Validates basic data structure and types."""
        errors = []
        
        if not isinstance(data, dict):
            errors.append("Data must be a dictionary")
            return errors
        
        # Check for required base fields
        if not any(key in data for key in ['cliente_nome', 'autor_1_nome']):
            errors.append("At least one author name is required")
        
        # Validate data types for specific fields
        date_fields = [k for k in data.keys() if 'data' in k.lower()]
        for field in date_fields:
            if data.get(field) and not self._is_valid_date_format(data[field]):
                errors.append(f"Invalid date format in field: {field}")
        
        return errors
    
    def _validate_template_requirements(self, template_id: int, data: Dict[str, Any]) -> List[str]:
        """Validates data against template-specific requirements."""
        errors = []
        
        # Get required placeholders for template
        placeholders = self.placeholder_repo.find_by_template_id(template_id)
        required_placeholders = [p for p in placeholders if p.obrigatorio]
        
        for placeholder in required_placeholders:
            if placeholder.chave not in data or not data[placeholder.chave]:
                errors.append(f"Required field missing: {placeholder.chave}")
        
        return errors
    
    def _validate_entities(self, data: Dict[str, Any]) -> List[str]:
        """Validates entity data (clients, authorities)."""
        warnings = []
        
        # Validate client CPF if present
        for key in data:
            if 'cpf' in key.lower() and data[key]:
                try:
                    client = self.entity_service.find_client_by_cpf(data[key])
                    if not client:
                        warnings.append(f"Client with CPF {data[key]} not found in database")
                except ValidationException:
                    warnings.append(f"Invalid CPF format: {data[key]}")
        
        return warnings
    
    def _generate_improvement_suggestions(self, data: Dict[str, Any], template: Any) -> List[str]:
        """Generates suggestions for data improvement."""
        suggestions = []
        
        # Suggest filling optional but common fields
        common_optional_fields = ['telefone', 'email', 'endereco']
        for field in common_optional_fields:
            if field not in data or not data[field]:
                suggestions.append(f"Consider adding {field} for more complete documentation")
        
        # Suggest process number format if applicable
        if 'processo_numero' in data and data['processo_numero']:
            if not self.validation_service.validate_process_number(data['processo_numero']):
                suggestions.append("Process number format may not be standard")
        
        return suggestions
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Validates date format."""
        date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
        for fmt in date_formats:
            try:
                datetime.strptime(date_str, fmt)
                return True
            except ValueError:
                continue
        return False
