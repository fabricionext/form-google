"""
Base Controller - Common functionality for all API controllers.

Provides standard HTTP response handling, validation patterns,
error handling, and authentication checks.
"""

from typing import Dict, Any, Optional, Tuple
import logging
from functools import wraps
from flask import request, jsonify, g
from pydantic import ValidationError

from app.utils.exceptions import (
    ValidationException,
    BusinessException,
    NotFoundException,
    UnauthorizedException
)


logger = logging.getLogger(__name__)


class BaseController:
    """
    Base controller with common functionality.
    
    Provides:
    - Standard HTTP response formatting
    - Request validation
    - Error handling
    - Authentication and authorization
    - Logging and monitoring
    """
    
    def __init__(self):
        self.logger = logger
    
    def success_response(self, data: Any = None, message: str = "Success", 
                        status_code: int = 200) -> Tuple[Dict[str, Any], int]:
        """
        Creates standardized success response.
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "success": True,
            "message": message,
            "data": data
        }
        
        if hasattr(g, 'request_id'):
            response["request_id"] = g.request_id
        
        return response, status_code
    
    def error_response(self, message: str, status_code: int = 400, 
                      error_code: str = None, details: Dict[str, Any] = None) -> Tuple[Dict[str, Any], int]:
        """
        Creates standardized error response.
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Application-specific error code
            details: Additional error details
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            "success": False,
            "message": message,
            "error_code": error_code,
            "details": details
        }
        
        if hasattr(g, 'request_id'):
            response["request_id"] = g.request_id
        
        return response, status_code
    
    def validation_error_response(self, errors: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Creates response for validation errors.
        
        Args:
            errors: Validation error dictionary
            
        Returns:
            Tuple of (response_dict, 422)
        """
        return self.error_response(
            message="Validation failed",
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"validation_errors": errors}
        )
    
    def handle_exceptions(self, func):
        """
        Decorator for handling common exceptions in controller methods.
        
        Args:
            func: Controller method to wrap
            
        Returns:
            Wrapped function with exception handling
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
                
            except ValidationError as e:
                self.logger.warning(f"Validation error in {func.__name__}: {e.messages}")
                return self.validation_error_response(e.messages)
                
            except ValidationException as e:
                self.logger.warning(f"Business validation error: {str(e)}")
                return self.error_response(str(e), 400, "VALIDATION_ERROR")
                
            except NotFoundException as e:
                self.logger.info(f"Resource not found: {str(e)}")
                return self.error_response(str(e), 404, "NOT_FOUND")
                
            except UnauthorizedException as e:
                self.logger.warning(f"Unauthorized access: {str(e)}")
                return self.error_response(str(e), 401, "UNAUTHORIZED")
                
            except BusinessException as e:
                self.logger.error(f"Business logic error: {str(e)}")
                return self.error_response(str(e), 400, "BUSINESS_ERROR")
                
            except Exception as e:
                self.logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
                return self.error_response(
                    "Internal server error", 
                    500, 
                    "INTERNAL_ERROR"
                )
        
        return wrapper
    
    def validate_json_request(self, schema_class, partial: bool = False) -> Dict[str, Any]:
        """
        Validates JSON request data against a Pydantic schema.
        
        Args:
            schema_class: Pydantic schema class
            partial: Allow partial validation (ignored for Pydantic)
            
        Returns:
            Validated data dictionary
            
        Raises:
            ValidationError: If validation fails
        """
        if not request.is_json:
            raise ValidationException("Request must be JSON")
        
        data = request.get_json()
        if data is None:
            raise ValidationException("Invalid JSON data")
        
        try:
            # Pydantic validation
            validated_model = schema_class(**data)
            return validated_model.dict()
        except ValidationError as e:
            raise ValidationException(f"Validation error: {e}")
        except Exception as e:
            raise ValidationException(f"Data validation failed: {e}")
    
    def validate_query_params(self, schema_class) -> Dict[str, Any]:
        """
        Validates query parameters against a Pydantic schema.
        
        Args:
            schema_class: Pydantic schema class
            
        Returns:
            Validated parameters dictionary
        """
        try:
            # Convert query args to dict
            params = dict(request.args)
            # Pydantic validation
            validated_model = schema_class(**params)
            return validated_model.dict()
        except ValidationError as e:
            raise ValidationException(f"Query parameter validation error: {e}")
        except Exception as e:
            raise ValidationException(f"Parameter validation failed: {e}")
    
    def get_pagination_params(self, default_page: int = 1, default_per_page: int = 20, 
                            max_per_page: int = 100) -> Dict[str, int]:
        """
        Extracts and validates pagination parameters.
        
        Args:
            default_page: Default page number
            default_per_page: Default items per page
            max_per_page: Maximum items per page
            
        Returns:
            Dict with page, per_page, offset
        """
        try:
            page = int(request.args.get('page', default_page))
            per_page = int(request.args.get('per_page', default_per_page))
        except ValueError:
            raise ValidationException("Page and per_page must be integers")
        
        if page < 1:
            raise ValidationException("Page must be greater than 0")
        
        if per_page < 1:
            per_page = default_per_page
        elif per_page > max_per_page:
            per_page = max_per_page
        
        offset = (page - 1) * per_page
        
        return {
            'page': page,
            'per_page': per_page,
            'offset': offset
        }
    
    def paginated_response(self, items: list, total: int, pagination_params: Dict[str, int], 
                          message: str = "Success") -> Tuple[Dict[str, Any], int]:
        """
        Creates paginated response.
        
        Args:
            items: List of items for current page
            total: Total number of items
            pagination_params: Pagination parameters
            message: Response message
            
        Returns:
            Paginated response tuple
        """
        page = pagination_params['page']
        per_page = pagination_params['per_page']
        
        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        data = {
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev,
                'next_page': page + 1 if has_next else None,
                'prev_page': page - 1 if has_prev else None
            }
        }
        
        return self.success_response(data, message)
    
    def require_auth(self, func):
        """
        Decorator to require authentication for controller methods.
        
        Args:
            func: Controller method to protect
            
        Returns:
            Wrapped function with auth check
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Authentication logic would go here
            # For now, just check if user is in session or g object
            if not hasattr(g, 'current_user') or not g.current_user:
                raise UnauthorizedException("Authentication required")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    def require_permission(self, permission: str):
        """
        Decorator to require specific permission for controller methods.
        
        Args:
            permission: Required permission string
            
        Returns:
            Decorator function
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not hasattr(g, 'current_user') or not g.current_user:
                    raise UnauthorizedException("Authentication required")
                
                # Permission check logic would go here
                user_permissions = getattr(g.current_user, 'permissions', [])
                if permission not in user_permissions:
                    raise UnauthorizedException(f"Permission '{permission}' required")
                
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def log_request(self, action: str, details: Dict[str, Any] = None):
        """
        Logs controller action for auditing.
        
        Args:
            action: Action being performed
            details: Additional details to log
        """
        log_data = {
            'action': action,
            'user_id': getattr(g, 'current_user', {}).get('id') if hasattr(g, 'current_user') else None,
            'request_id': getattr(g, 'request_id', None),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'details': details or {}
        }
        
        self.logger.info(f"Controller action: {action}", extra=log_data)
    
    def extract_filters(self, allowed_filters: list) -> Dict[str, Any]:
        """
        Extracts and validates filter parameters from query string.
        
        Args:
            allowed_filters: List of allowed filter field names
            
        Returns:
            Dict of validated filters
        """
        filters = {}
        
        for filter_name in allowed_filters:
            value = request.args.get(filter_name)
            if value is not None:
                # Basic sanitization
                if isinstance(value, str):
                    value = value.strip()
                    if value:  # Only add non-empty strings
                        filters[filter_name] = value
                else:
                    filters[filter_name] = value
        
        return filters
    
    def validate_id_parameter(self, id_value: Any, parameter_name: str = "id") -> int:
        """
        Validates ID parameter.
        
        Args:
            id_value: ID value to validate
            parameter_name: Name of parameter for error messages
            
        Returns:
            Validated integer ID
            
        Raises:
            ValidationException: If ID is invalid
        """
        try:
            id_int = int(id_value)
            if id_int <= 0:
                raise ValueError("ID must be positive")
            return id_int
        except (ValueError, TypeError):
            raise ValidationException(f"Invalid {parameter_name}: must be a positive integer")
    
    def format_datetime(self, dt: Any) -> Optional[str]:
        """
        Formats datetime for API response.
        
        Args:
            dt: Datetime object
            
        Returns:
            ISO formatted datetime string or None
        """
        if dt is None:
            return None
        
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        
        return str(dt)
    
    def clean_response_data(self, data: Any) -> Any:
        """
        Cleans response data for JSON serialization.
        
        Args:
            data: Data to clean
            
        Returns:
            JSON-serializable data
        """
        if data is None:
            return None
        
        if isinstance(data, dict):
            return {key: self.clean_response_data(value) for key, value in data.items()}
        
        elif isinstance(data, list):
            return [self.clean_response_data(item) for item in data]
        
        elif hasattr(data, 'isoformat'):  # datetime objects
            return data.isoformat()
        
        elif hasattr(data, '__dict__'):  # Model objects
            return {key: self.clean_response_data(value) 
                   for key, value in data.__dict__.items() 
                   if not key.startswith('_')}
        
        else:
            return data 