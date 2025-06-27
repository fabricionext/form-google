# Standard library imports

# Third party imports
from flask import current_app, request
from flask_login import current_user, login_user, logout_user
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError

# Local application imports
from extensions import db

from ..models import User
from ..schemas.user_schema import UserLoginSchema

# Create namespace
auth_ns = Namespace("auth", description="Operações de autenticação")

# API Models for documentation
login_model = auth_ns.model(
    "Login",
    {
        "email": fields.String(required=True, description="Email do usuário"),
        "password": fields.String(required=True, description="Senha do usuário"),
        "remember_me": fields.Boolean(description="Lembrar usuário"),
    },
)

user_model = auth_ns.model(
    "User",
    {
        "id": fields.Integer(description="ID do usuário"),
        "email": fields.String(description="Email do usuário"),
        "name": fields.String(description="Nome do usuário"),
        "is_active": fields.Boolean(description="Usuário ativo"),
        "last_login": fields.DateTime(description="Último login"),
    },
)

response_model = auth_ns.model(
    "AuthResponse",
    {
        "success": fields.Boolean(description="Sucesso da operação"),
        "message": fields.String(description="Mensagem de retorno"),
        "user": fields.Nested(user_model, description="Dados do usuário"),
    },
)


@auth_ns.route("/login")
class LoginResource(Resource):
    """Endpoint para autenticação de usuários."""

    @auth_ns.expect(login_model)
    @auth_ns.marshal_with(response_model)
    @auth_ns.doc("login_user")
    def post(self):
        """Realizar login do usuário."""
        try:
            # Validar dados de entrada
            schema = UserLoginSchema()
            data = schema.load(request.json)

            # Buscar usuário
            user = User.query.filter_by(email=data["email"]).first()

            if not user or not user.check_password(data["password"]):
                return {
                    "success": False,
                    "message": "Email ou senha inválidos",
                    "user": None,
                }, 401

            if not user.is_active:
                return {
                    "success": False,
                    "message": "Usuário inativo",
                    "user": None,
                }, 401

            # Realizar login
            login_user(user, remember=data.get("remember_me", False))

            # Atualizar último login
            user.last_login = db.func.now()
            db.session.commit()

            return {
                "success": True,
                "message": "Login realizado com sucesso",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "is_active": user.is_active,
                    "last_login": user.last_login,
                },
            }, 200

        except ValidationError as e:
            return {
                "success": False,
                "message": "Dados inválidos",
                "errors": e.messages,
            }, 400

        except Exception as e:
            current_app.logger.error(f"Erro no login: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "user": None,
            }, 500


@auth_ns.route("/logout")
class LogoutResource(Resource):
    """Endpoint para logout de usuários."""

    @auth_ns.marshal_with(response_model)
    @auth_ns.doc("logout_user")
    def post(self):
        """Realizar logout do usuário."""
        try:
            logout_user()
            return {
                "success": True,
                "message": "Logout realizado com sucesso",
                "user": None,
            }, 200

        except Exception as e:
            current_app.logger.error(f"Erro no logout: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "user": None,
            }, 500


@auth_ns.route("/me")
class MeResource(Resource):
    """Endpoint para obter dados do usuário atual."""

    @auth_ns.marshal_with(response_model)
    @auth_ns.doc("get_current_user")
    def get(self):
        """Obter dados do usuário logado."""
        try:
            if not current_user.is_authenticated:
                return {
                    "success": False,
                    "message": "Usuário não autenticado",
                    "user": None,
                }, 401

            return {
                "success": True,
                "message": "Dados do usuário",
                "user": {
                    "id": current_user.id,
                    "email": current_user.email,
                    "name": current_user.name,
                    "is_active": current_user.is_active,
                    "last_login": current_user.last_login,
                },
            }, 200

        except Exception as e:
            current_app.logger.error(f"Erro ao obter usuário: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "user": None,
            }, 500
