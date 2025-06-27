"""
Entity Service - Business logic for client and traffic authority management.

Handles client searches, authority management, and related entity operations
with caching and fuzzy matching capabilities.
"""

from typing import List, Optional, Dict, Any
import logging
import re
from datetime import datetime, timedelta

from app.repositories.client_repository import ClientRepository
from app.utils.exceptions import (
    ClientNotFoundException,
    ValidationException,
    BusinessException
)


logger = logging.getLogger(__name__)


class EntityService:
    """
    Service for managing clients and traffic authorities.
    
    Provides business logic for:
    - Client search and management (CPF/CNPJ)
    - Traffic authority search with fuzzy matching
    - Entity creation and updates
    - Autocomplete and suggestions
    """
    
    def __init__(self):
        self.client_repo = ClientRepository()
        self._cache = {}  # Simple in-memory cache
        self._cache_ttl = timedelta(minutes=30)
    
    def find_client_by_cpf(self, cpf: str) -> Optional[Dict[str, Any]]:
        """
        Finds client by CPF with caching.
        
        Args:
            cpf: Client CPF (with or without formatting)
            
        Returns:
            Client data dict or None if not found
            
        Raises:
            ValidationException: If CPF format is invalid
        """
        # Sanitize and validate CPF
        clean_cpf = self._clean_document(cpf)
        if not self._validate_cpf(clean_cpf):
            raise ValidationException(f"Invalid CPF format: {cpf}")
        
        # Check cache first
        cache_key = f"client:cpf:{clean_cpf}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"Client found in cache: {clean_cpf}")
            return cached_result
        
        # Search in database
        client = self.client_repo.find_by_cpf(clean_cpf)
        result = self.client_repo.to_dict(client) if client else None
        
        # Cache result (including None for not found)
        self._set_cache(cache_key, result)
        
        if result:
            logger.info(f"Client found: {clean_cpf}")
        else:
            logger.info(f"Client not found: {clean_cpf}")
            
        return result
    
    def find_client_by_cnpj(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """
        Finds client by CNPJ with caching.
        
        Args:
            cnpj: Client CNPJ (with or without formatting)
            
        Returns:
            Client data dict or None if not found
            
        Raises:
            ValidationException: If CNPJ format is invalid
        """
        # Sanitize and validate CNPJ
        clean_cnpj = self._clean_document(cnpj)
        if not self._validate_cnpj(clean_cnpj):
            raise ValidationException(f"Invalid CNPJ format: {cnpj}")
        
        # Check cache first
        cache_key = f"client:cnpj:{clean_cnpj}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            logger.debug(f"Client found in cache: {clean_cnpj}")
            return cached_result
        
        # Search in database
        client = self.client_repo.find_by_cnpj(clean_cnpj)
        result = self.client_repo.to_dict(client) if client else None
        
        # Cache result
        self._set_cache(cache_key, result)
        
        if result:
            logger.info(f"Client found: {clean_cnpj}")
        else:
            logger.info(f"Client not found: {clean_cnpj}")
            
        return result
    
    def search_clients_by_name(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Searches clients by name with fuzzy matching.
        
        Args:
            name: Partial or complete client name
            limit: Maximum number of results
            
        Returns:
            List of matching client dictionaries
        """
        if len(name.strip()) < 2:
            return []
        
        cache_key = f"client:search:{name.lower()}:{limit}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        clients = self.client_repo.search_by_name(name, limit)
        result = [self.client_repo.to_dict(c) for c in clients]
        
        # Cache search results for shorter time
        self._set_cache(cache_key, result, ttl_minutes=10)
        
        logger.info(f"Found {len(result)} clients matching '{name}'")
        return result
    
    def create_or_update_client(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates new client or updates existing one.
        
        Args:
            data: Client data dictionary
            
        Returns:
            Created/updated client data
            
        Raises:
            ValidationException: If client data is invalid
        """
        # Validate required fields
        self._validate_client_data(data)
        
        # Check if client already exists
        document = data.get('cpf') or data.get('cnpj')
        if not document:
            raise ValidationException("CPF or CNPJ is required")
        
        existing_client = None
        if 'cpf' in data:
            existing_client = self.find_client_by_cpf(data['cpf'])
        elif 'cnpj' in data:
            existing_client = self.find_client_by_cnpj(data['cnpj'])
        
        try:
            if existing_client:
                # Update existing client
                updated_client = self.client_repo.update(existing_client['id'], data)
                result = self.client_repo.to_dict(updated_client)
                logger.info(f"Client updated: {document}")
            else:
                # Create new client
                new_client = self.client_repo.create(data)
                result = self.client_repo.to_dict(new_client)
                logger.info(f"Client created: {document}")
            
            # Invalidate related cache entries
            self._invalidate_client_cache(document)
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating/updating client: {str(e)}")
            raise BusinessException(f"Failed to save client: {str(e)}")
    
    def suggest_authorities(self, partial_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Provides autocomplete suggestions for traffic authorities.
        
        Args:
            partial_name: Partial authority name
            limit: Maximum number of suggestions
            
        Returns:
            List of authority suggestions
        """
        if len(partial_name.strip()) < 2:
            return []
        
        # Cache key for authority suggestions
        cache_key = f"authority:suggest:{partial_name.lower()}:{limit}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Search authorities (assuming we have a repository for this)
        # For now, return mock data - this would be implemented with actual repository
        mock_authorities = self._get_mock_authorities()
        
        # Simple fuzzy matching
        suggestions = []
        partial_lower = partial_name.lower()
        
        for authority in mock_authorities:
            if partial_lower in authority['nome'].lower():
                suggestions.append(authority)
                if len(suggestions) >= limit:
                    break
        
        # Cache suggestions for longer time since authorities don't change often
        self._set_cache(cache_key, suggestions, ttl_minutes=60)
        
        logger.debug(f"Found {len(suggestions)} authority suggestions for '{partial_name}'")
        return suggestions
    
    def get_common_authority_sets(self, location: str = None) -> List[List[Dict[str, Any]]]:
        """
        Gets common sets of authorities based on location.
        
        Args:
            location: Optional location filter
            
        Returns:
            List of authority sets commonly used together
        """
        # This would be implemented based on historical usage patterns
        # For now, return some common combinations
        
        common_sets = [
            [
                {"id": 1, "nome": "DETRAN-SP", "tipo": "estadual"},
                {"id": 2, "nome": "Prefeitura de São Paulo", "tipo": "municipal"}
            ],
            [
                {"id": 1, "nome": "DETRAN-SP", "tipo": "estadual"},
                {"id": 3, "nome": "PRF", "tipo": "federal"}
            ]
        ]
        
        return common_sets
    
    def validate_client_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validates client data and returns list of errors.
        
        Args:
            data: Client data to validate
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        try:
            self._validate_client_data(data)
        except ValidationException as e:
            errors.append(str(e))
        
        return errors
    
    def get_client_statistics(self) -> Dict[str, Any]:
        """
        Gets statistics about clients in the system.
        
        Returns:
            Dictionary with client statistics
        """
        stats = self.client_repo.get_statistics()
        
        return {
            'total_clients': stats.get('total', 0),
            'pessoa_fisica': stats.get('pf_count', 0),
            'pessoa_juridica': stats.get('pj_count', 0),
            'created_this_month': stats.get('created_this_month', 0),
            'last_update': datetime.utcnow().isoformat()
        }
    
    def _validate_client_data(self, data: Dict[str, Any]) -> None:
        """
        Validates client data structure and content.
        
        Args:
            data: Client data to validate
            
        Raises:
            ValidationException: If validation fails
        """
        # Check required fields
        required_fields = ['nome']
        for field in required_fields:
            if not data.get(field):
                raise ValidationException(f"Field '{field}' is required")
        
        # Validate document (CPF or CNPJ)
        if 'cpf' in data and data['cpf']:
            clean_cpf = self._clean_document(data['cpf'])
            if not self._validate_cpf(clean_cpf):
                raise ValidationException("Invalid CPF")
            data['cpf'] = clean_cpf
        
        if 'cnpj' in data and data['cnpj']:
            clean_cnpj = self._clean_document(data['cnpj'])
            if not self._validate_cnpj(clean_cnpj):
                raise ValidationException("Invalid CNPJ")
            data['cnpj'] = clean_cnpj
        
        # Validate email format if provided
        if 'email' in data and data['email']:
            if not self._validate_email(data['email']):
                raise ValidationException("Invalid email format")
        
        # Validate phone format if provided
        if 'telefone' in data and data['telefone']:
            clean_phone = self._clean_phone(data['telefone'])
            if len(clean_phone) < 10:
                raise ValidationException("Invalid phone number")
            data['telefone'] = clean_phone
    
    def _clean_document(self, document: str) -> str:
        """Removes formatting from CPF/CNPJ."""
        return re.sub(r'[^\d]', '', document or '')
    
    def _clean_phone(self, phone: str) -> str:
        """Removes formatting from phone number."""
        return re.sub(r'[^\d]', '', phone or '')
    
    def _validate_cpf(self, cpf: str) -> bool:
        """
        Validates CPF using check digits.
        
        Args:
            cpf: Clean CPF string (numbers only)
            
        Returns:
            True if valid CPF
        """
        if not cpf or len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        
        # Calculate check digits
        def calculate_digit(cpf_partial):
            total = sum(int(digit) * weight for digit, weight in 
                       zip(cpf_partial, range(len(cpf_partial) + 1, 1, -1)))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        first_digit = calculate_digit(cpf[:9])
        second_digit = calculate_digit(cpf[:10])
        
        return cpf[9:11] == f"{first_digit}{second_digit}"
    
    def _validate_cnpj(self, cnpj: str) -> bool:
        """
        Validates CNPJ using check digits.
        
        Args:
            cnpj: Clean CNPJ string (numbers only)
            
        Returns:
            True if valid CNPJ
        """
        if not cnpj or len(cnpj) != 14:
            return False
        
        # CNPJ validation algorithm
        weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        def calculate_digit(cnpj_partial, weights):
            total = sum(int(digit) * weight for digit, weight in zip(cnpj_partial, weights))
            remainder = total % 11
            return 0 if remainder < 2 else 11 - remainder
        
        first_digit = calculate_digit(cnpj[:12], weights1)
        second_digit = calculate_digit(cnpj[:13], weights2)
        
        return cnpj[12:14] == f"{first_digit}{second_digit}"
    
    def _validate_email(self, email: str) -> bool:
        """Simple email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _get_from_cache(self, key: str) -> Any:
        """Gets value from cache if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                return value
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any, ttl_minutes: int = None) -> None:
        """Sets value in cache with timestamp."""
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self._cache_ttl
        self._cache[key] = (value, datetime.utcnow())
    
    def _invalidate_client_cache(self, document: str) -> None:
        """Invalidates cache entries for a client."""
        clean_doc = self._clean_document(document)
        keys_to_remove = [
            f"client:cpf:{clean_doc}",
            f"client:cnpj:{clean_doc}"
        ]
        
        for key in keys_to_remove:
            if key in self._cache:
                del self._cache[key]
    
    def _get_mock_authorities(self) -> List[Dict[str, Any]]:
        """Returns mock authority data. Replace with actual repository call."""
        return [
            {"id": 1, "nome": "DETRAN-SP", "cnpj": "12345678000195", "tipo": "estadual"},
            {"id": 2, "nome": "Prefeitura de São Paulo", "cnpj": "98765432000156", "tipo": "municipal"},
            {"id": 3, "nome": "PRF - Polícia Rodoviária Federal", "cnpj": "11223344000177", "tipo": "federal"},
            {"id": 4, "nome": "CETESB", "cnpj": "55667788000133", "tipo": "estadual"},
            {"id": 5, "nome": "CET - Companhia de Engenharia de Tráfego", "cnpj": "99887766000122", "tipo": "municipal"},
        ] 