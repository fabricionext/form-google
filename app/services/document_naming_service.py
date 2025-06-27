"""
Document Naming Service - Business logic for standardized document naming.

Handles generation of standardized filenames following the pattern:
dd-mm-aaaa-Nome e Sobrenome-Tipo-Timestamp
"""

from typing import List, Dict, Any, Optional
import logging
import re
from datetime import datetime
import unicodedata

from app.config.constants import DocumentTypes
from app.utils.exceptions import ValidationException


logger = logging.getLogger(__name__)


class DocumentNamingService:
    """
    Service for standardized document naming.
    
    Provides:
    - Standardized filename generation
    - Filename sanitization
    - Uniqueness validation
    - Batch naming operations
    """
    
    def __init__(self):
        self.timestamp_format = "%H%M%S"
        self.date_format = "%d-%m-%Y"
        self.max_filename_length = 150
    
    def generate_filename(self, document_type: str, authors: List[Dict[str, Any]], **kwargs) -> str:
        """
        Generates standardized filename.
        
        Pattern: dd-mm-aaaa-Nome e Sobrenome-Tipo-Timestamp
        
        Args:
            document_type: Type of document (e.g., "Defesa Prévia", "Ação Anulatória")
            authors: List of author dictionaries with 'nome' field
            **kwargs: Additional parameters like custom_date, include_timestamp
            
        Returns:
            Standardized filename string
            
        Raises:
            ValidationException: If required data is invalid or missing
        """
        logger.debug(f"Generating filename for {document_type} with {len(authors)} authors")
        
        # Validate inputs
        self._validate_inputs(document_type, authors)
        
        # Get date part
        date_part = self._format_date_part(kwargs.get('custom_date'))
        
        # Get names part
        names_part = self._format_names_part(authors)
        
        # Get document type part
        type_part = self._format_document_type(document_type)
        
        # Get timestamp part (optional)
        timestamp_part = ""
        if kwargs.get('include_timestamp', True):
            timestamp_part = f"-{datetime.now().strftime(self.timestamp_format)}"
        
        # Combine parts
        filename = f"{date_part}-{names_part}-{type_part}{timestamp_part}"
        
        # Sanitize and validate length
        sanitized_filename = self.sanitize_filename(filename)
        
        if len(sanitized_filename) > self.max_filename_length:
            sanitized_filename = self._truncate_filename(sanitized_filename)
        
        logger.info(f"Generated filename: {sanitized_filename}")
        return sanitized_filename
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Removes invalid characters for filenames.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove accents and normalize unicode
        normalized = unicodedata.normalize('NFD', filename)
        ascii_filename = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        # Replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        sanitized = re.sub(invalid_chars, '', ascii_filename)
        
        # Replace multiple spaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Replace spaces with underscores for better compatibility
        sanitized = sanitized.replace(' ', '_')
        
        # Remove leading/trailing underscores and dots
        sanitized = sanitized.strip('_.')
        
        # Ensure not empty
        if not sanitized:
            sanitized = "documento_sem_nome"
        
        return sanitized
    
    def ensure_uniqueness(self, filename: str, existing_files: List[str]) -> str:
        """
        Ensures filename uniqueness by adding suffix if needed.
        
        Args:
            filename: Base filename
            existing_files: List of existing filenames to check against
            
        Returns:
            Unique filename
        """
        if filename not in existing_files:
            return filename
        
        # Extract extension if present
        name_parts = filename.rsplit('.', 1)
        base_name = name_parts[0]
        extension = f".{name_parts[1]}" if len(name_parts) > 1 else ""
        
        # Try numbered suffixes
        counter = 1
        while True:
            new_filename = f"{base_name}_{counter:02d}{extension}"
            if new_filename not in existing_files:
                logger.info(f"Made filename unique: {new_filename}")
                return new_filename
            counter += 1
            
            # Safety check to avoid infinite loop
            if counter > 999:
                # Add timestamp to ensure uniqueness
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_filename = f"{base_name}_{timestamp}{extension}"
                logger.warning(f"Used timestamp for uniqueness: {new_filename}")
                return new_filename
    
    def generate_batch_filenames(self, documents: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Generates filenames for multiple documents ensuring uniqueness.
        
        Args:
            documents: List of document dictionaries with 'type', 'authors', etc.
            
        Returns:
            Dict mapping document IDs to generated filenames
        """
        logger.info(f"Generating batch filenames for {len(documents)} documents")
        
        generated_filenames = []
        filename_map = {}
        
        for doc in documents:
            doc_id = doc.get('id', f"doc_{len(filename_map)}")
            
            try:
                filename = self.generate_filename(
                    document_type=doc['type'],
                    authors=doc['authors'],
                    **doc.get('options', {})
                )
                
                # Ensure uniqueness within the batch
                unique_filename = self.ensure_uniqueness(filename, generated_filenames)
                
                filename_map[doc_id] = unique_filename
                generated_filenames.append(unique_filename)
                
            except Exception as e:
                logger.error(f"Error generating filename for document {doc_id}: {str(e)}")
                # Generate fallback filename
                fallback = f"documento_{doc_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                filename_map[doc_id] = fallback
                generated_filenames.append(fallback)
        
        return filename_map
    
    def parse_filename(self, filename: str) -> Dict[str, Any]:
        """
        Parses a standardized filename to extract components.
        
        Args:
            filename: Filename to parse
            
        Returns:
            Dict with parsed components (date, names, type, timestamp)
        """
        # Remove extension
        name_without_ext = filename.rsplit('.', 1)[0]
        
        # Pattern: dd-mm-aaaa-Nome_e_Sobrenome-Tipo-HHMMSS
        pattern = r'^(\d{2}-\d{2}-\d{4})-(.+?)-(.+?)(?:-(\d{6}))?$'
        match = re.match(pattern, name_without_ext)
        
        if not match:
            return {'parsed': False, 'filename': filename}
        
        date_part, names_part, type_part, timestamp_part = match.groups()
        
        # Parse names (convert underscores back to spaces)
        names = names_part.replace('_', ' ')
        
        # Parse date
        try:
            parsed_date = datetime.strptime(date_part, self.date_format).date()
        except ValueError:
            parsed_date = None
        
        # Parse timestamp
        parsed_timestamp = None
        if timestamp_part:
            try:
                parsed_timestamp = datetime.strptime(timestamp_part, self.timestamp_format).time()
            except ValueError:
                pass
        
        return {
            'parsed': True,
            'date': parsed_date,
            'names': names,
            'document_type': type_part.replace('_', ' '),
            'timestamp': parsed_timestamp,
            'raw_parts': {
                'date': date_part,
                'names': names_part,
                'type': type_part,
                'timestamp': timestamp_part
            }
        }
    
    def suggest_filename_improvements(self, filename: str) -> List[str]:
        """
        Suggests improvements for non-standard filenames.
        
        Args:
            filename: Filename to analyze
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        parsed = self.parse_filename(filename)
        if parsed['parsed']:
            return suggestions  # Already follows standard
        
        # Check common issues
        if not re.search(r'\d{2}-\d{2}-\d{4}', filename):
            suggestions.append("Adicionar data no formato dd-mm-aaaa")
        
        if len(filename) > self.max_filename_length:
            suggestions.append(f"Reduzir tamanho (atual: {len(filename)}, máximo: {self.max_filename_length})")
        
        if re.search(r'[<>:"/\\|?*]', filename):
            suggestions.append("Remover caracteres inválidos para nome de arquivo")
        
        if not any(char.isalpha() for char in filename):
            suggestions.append("Incluir nome do cliente no arquivo")
        
        return suggestions
    
    def _validate_inputs(self, document_type: str, authors: List[Dict[str, Any]]) -> None:
        """Validates input parameters."""
        if not document_type or not document_type.strip():
            raise ValidationException("Document type is required")
        
        if not authors:
            raise ValidationException("At least one author is required")
        
        for i, author in enumerate(authors):
            if not isinstance(author, dict) or 'nome' not in author:
                raise ValidationException(f"Author {i+1} must have 'nome' field")
            
            if not author['nome'] or not author['nome'].strip():
                raise ValidationException(f"Author {i+1} name cannot be empty")
    
    def _format_date_part(self, custom_date: Optional[datetime] = None) -> str:
        """Formats the date part of the filename."""
        date_to_use = custom_date or datetime.now()
        return date_to_use.strftime(self.date_format)
    
    def _format_names_part(self, authors: List[Dict[str, Any]]) -> str:
        """Formats the names part of the filename."""
        # Extract and clean names
        names = []
        for author in authors[:3]:  # Limit to first 3 authors to avoid overly long names
            name = author['nome'].strip()
            # Keep only first and last name for brevity
            name_parts = name.split()
            if len(name_parts) >= 2:
                formatted_name = f"{name_parts[0]} {name_parts[-1]}"
            else:
                formatted_name = name_parts[0] if name_parts else "Sem_Nome"
            names.append(formatted_name)
        
        if len(authors) > 3:
            names.append("e_outros")
        
        # Join with " e " for readability
        if len(names) == 1:
            return names[0]
        elif len(names) == 2:
            return f"{names[0]} e {names[1]}"
        else:
            return f"{' '.join(names[:-1])} e {names[-1]}"
    
    def _format_document_type(self, document_type: str) -> str:
        """Formats the document type part."""
        # Normalize document type
        type_mapping = {
            DocumentTypes.FICHA_CADASTRAL_PF.value: "Ficha_Cadastral_PF",
            DocumentTypes.FICHA_CADASTRAL_PJ.value: "Ficha_Cadastral_PJ", 
            DocumentTypes.DEFESA_PREVIA.value: "Defesa_Previa",
            DocumentTypes.RECURSO_JARI.value: "Recurso_JARI",
            DocumentTypes.TERMO_ACORDO.value: "Termo_Acordo",
            DocumentTypes.ACAO_ANULATORIA.value: "Acao_Anulatoria"
        }
        
        return type_mapping.get(document_type, document_type.replace(' ', '_'))
    
    def _truncate_filename(self, filename: str) -> str:
        """Truncates filename while preserving important parts."""
        # Split into parts
        parts = filename.split('-')
        if len(parts) < 3:
            return filename[:self.max_filename_length]
        
        date_part = parts[0]
        names_part = parts[1]
        type_part = parts[2]
        timestamp_part = parts[3] if len(parts) > 3 else ""
        
        # Calculate available space for names
        fixed_parts_length = len(date_part) + len(type_part) + len(timestamp_part) + 6  # 6 for separators
        available_for_names = self.max_filename_length - fixed_parts_length
        
        if len(names_part) > available_for_names:
            # Truncate names part intelligently
            truncated_names = names_part[:available_for_names-3] + "..."
            return f"{date_part}-{truncated_names}-{type_part}" + (f"-{timestamp_part}" if timestamp_part else "")
        
        return filename 