# Standard library imports

# Third party imports
try:
    from flask_marshmallow import Marshmallow
    ma = Marshmallow()
    
    # Import all schemas for easy access
    from .cliente_schema import ClienteSchema
    from .formulario_schema import FormularioSchema, PeticaoModeloSchema
    from .user_schema import UserSchema
except Exception as e:
    print(f"Warning: Could not import marshmallow schemas: {e}")
    ma = None
    ClienteSchema = None
    FormularioSchema = None
    PeticaoModeloSchema = None
    UserSchema = None

__all__ = [
    "ma",
    "ClienteSchema",
    "FormularioSchema",
    "PeticaoModeloSchema",
    "UserSchema",
]
