# Standard library imports

# Third party imports
from marshmallow import Schema, ValidationError, fields, validate, validates


class UserSchema(Schema):
    """Schema para validação de dados do usuário."""

    id = fields.Int(dump_only=True)
    email = fields.Email(required=True)
    name = fields.Str(validate=validate.Length(min=2, max=100))
    is_active = fields.Bool(load_default=True)
    last_login = fields.DateTime(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserCreateSchema(UserSchema):
    """Schema para criação de usuário."""

    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    confirm_password = fields.Str(required=True)

    @validates("password")
    def validate_password(self, value):
        """Validação de senha."""
        if len(value) < 8:
            raise ValidationError("Senha deve ter pelo menos 8 caracteres.")

        # Verifica se tem pelo menos uma letra maiúscula
        if not any(c.isupper() for c in value):
            raise ValidationError("Senha deve ter pelo menos uma letra maiúscula.")

        # Verifica se tem pelo menos uma letra minúscula
        if not any(c.islower() for c in value):
            raise ValidationError("Senha deve ter pelo menos uma letra minúscula.")

        # Verifica se tem pelo menos um número
        if not any(c.isdigit() for c in value):
            raise ValidationError("Senha deve ter pelo menos um número.")

        return value

    def validate(self, data, **kwargs):
        """Validação geral do schema."""
        errors = super().validate(data, **kwargs)

        # Verifica se as senhas coincidem
        if "password" in data and "confirm_password" in data:
            if data["password"] != data["confirm_password"]:
                errors["confirm_password"] = ["Senhas não coincidem."]

        return errors


class UserUpdateSchema(Schema):
    """Schema para atualização de usuário."""

    name = fields.Str(validate=validate.Length(min=2, max=100))
    email = fields.Email()
    is_active = fields.Bool()


class UserLoginSchema(Schema):
    """Schema para login de usuário."""

    email = fields.Email(required=True)
    password = fields.Str(required=True)
    remember_me = fields.Bool(load_default=False)


class UserPasswordChangeSchema(Schema):
    """Schema para mudança de senha."""

    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    confirm_new_password = fields.Str(required=True)

    @validates("new_password")
    def validate_new_password(self, value):
        """Validação de nova senha."""
        if len(value) < 8:
            raise ValidationError("Nova senha deve ter pelo menos 8 caracteres.")

        # Verifica se tem pelo menos uma letra maiúscula
        if not any(c.isupper() for c in value):
            raise ValidationError("Nova senha deve ter pelo menos uma letra maiúscula.")

        # Verifica se tem pelo menos uma letra minúscula
        if not any(c.islower() for c in value):
            raise ValidationError("Nova senha deve ter pelo menos uma letra minúscula.")

        # Verifica se tem pelo menos um número
        if not any(c.isdigit() for c in value):
            raise ValidationError("Nova senha deve ter pelo menos um número.")

        return value

    def validate(self, data, **kwargs):
        """Validação geral do schema."""
        errors = super().validate(data, **kwargs)

        # Verifica se as novas senhas coincidem
        if "new_password" in data and "confirm_new_password" in data:
            if data["new_password"] != data["confirm_new_password"]:
                errors["confirm_new_password"] = ["Novas senhas não coincidem."]

        # Verifica se a nova senha é diferente da atual
        if "current_password" in data and "new_password" in data:
            if data["current_password"] == data["new_password"]:
                errors["new_password"] = ["Nova senha deve ser diferente da atual."]

        return errors


class UserListSchema(Schema):
    """Schema simplificado para listagem de usuários."""

    id = fields.Int()
    email = fields.Email()
    name = fields.Str()
    is_active = fields.Bool()
    last_login = fields.DateTime()
    created_at = fields.DateTime()
