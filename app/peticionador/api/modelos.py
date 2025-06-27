# Standard library imports

# Third party imports
from flask import current_app, request
from flask_login import login_required
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError

# Local application imports
from extensions import db

from ..models import PeticaoModelo
from ..schemas.formulario_schema import PeticaoModeloListSchema, PeticaoModeloSchema

# Create namespace
modelos_ns = Namespace("modelos", description="Operações com modelos de petição")

# API Models for documentation
modelo_model = modelos_ns.model(
    "PeticaoModelo",
    {
        "id": fields.Integer(description="ID do modelo"),
        "nome": fields.String(description="Nome do modelo"),
        "slug": fields.String(description="Slug do modelo"),
        "descricao": fields.String(description="Descrição do modelo"),
        "ativo": fields.Boolean(description="Modelo ativo"),
        "total_placeholders": fields.Integer(description="Total de placeholders"),
        "total_personas": fields.Integer(description="Total de personas"),
        "criado_em": fields.DateTime(description="Data de criação"),
    },
)

modelo_create_model = modelos_ns.model(
    "PeticaoModeloCreate",
    {
        "nome": fields.String(required=True, description="Nome do modelo"),
        "slug": fields.String(required=True, description="Slug único do modelo"),
        "google_doc_id": fields.String(required=True, description="ID do Google Docs"),
        "pasta_destino_id": fields.String(
            required=True, description="ID da pasta no Google Drive"
        ),
        "descricao": fields.String(description="Descrição do modelo"),
        "ativo": fields.Boolean(description="Modelo ativo", default=True),
    },
)

response_model = modelos_ns.model(
    "ModeloResponse",
    {
        "success": fields.Boolean(description="Sucesso da operação"),
        "message": fields.String(description="Mensagem de retorno"),
        "data": fields.Raw(description="Dados do modelo"),
    },
)


@modelos_ns.route("/")
class ModeloListResource(Resource):
    """Endpoint para listagem e criação de modelos."""

    @login_required
    @modelos_ns.marshal_list_with(modelo_model)
    @modelos_ns.doc("list_modelos")
    def get(self):
        """Listar todos os modelos de petição."""
        try:
            modelos = (
                PeticaoModelo.query.filter_by(ativo=True)
                .order_by(PeticaoModelo.nome)
                .all()
            )
            schema = PeticaoModeloListSchema(many=True)
            return schema.dump(modelos), 200

        except Exception as e:
            current_app.logger.error(f"Erro ao listar modelos: {str(e)}")
            return {"message": "Erro interno do servidor"}, 500

    @login_required
    @modelos_ns.expect(modelo_create_model)
    @modelos_ns.marshal_with(response_model)
    @modelos_ns.doc("create_modelo")
    def post(self):
        """Criar novo modelo de petição."""
        try:
            # Validar dados de entrada
            schema = PeticaoModeloSchema()
            data = schema.load(request.json)

            # Verificar se slug já existe
            existing_modelo = PeticaoModelo.query.filter_by(slug=data["slug"]).first()
            if existing_modelo:
                return {
                    "success": False,
                    "message": "Slug já existe",
                    "data": None,
                }, 409

            # Criar modelo
            modelo = PeticaoModelo()
            for key, value in data.items():
                setattr(modelo, key, value)

            db.session.add(modelo)
            db.session.commit()

            # Retornar modelo criado
            schema_response = PeticaoModeloSchema()
            return {
                "success": True,
                "message": "Modelo criado com sucesso",
                "data": schema_response.dump(modelo),
            }, 201

        except ValidationError as e:
            return {
                "success": False,
                "message": "Dados inválidos",
                "errors": e.messages,
            }, 400

        except Exception as e:
            current_app.logger.error(f"Erro ao criar modelo: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500


@modelos_ns.route("/<int:modelo_id>")
class ModeloResource(Resource):
    """Endpoint para operações com modelo específico."""

    @login_required
    @modelos_ns.marshal_with(response_model)
    @modelos_ns.doc("get_modelo")
    def get(self, modelo_id):
        """Obter dados de um modelo específico."""
        try:
            modelo = PeticaoModelo.query.get_or_404(modelo_id)
            schema = PeticaoModeloSchema()
            return {
                "success": True,
                "message": "Modelo encontrado",
                "data": schema.dump(modelo),
            }, 200

        except Exception as e:
            current_app.logger.error(f"Erro ao obter modelo: {str(e)}")
            return {
                "success": False,
                "message": "Modelo não encontrado",
                "data": None,
            }, 404

    @login_required
    @modelos_ns.expect(modelo_model)
    @modelos_ns.marshal_with(response_model)
    @modelos_ns.doc("update_modelo")
    def put(self, modelo_id):
        """Atualizar dados de um modelo."""
        try:
            modelo = PeticaoModelo.query.get_or_404(modelo_id)

            # Validar dados de entrada
            schema = PeticaoModeloSchema(partial=True)
            data = schema.load(request.json)

            # Verificar se slug já existe (exceto o próprio modelo)
            if "slug" in data:
                existing_modelo = (
                    PeticaoModelo.query.filter_by(slug=data["slug"])
                    .filter(PeticaoModelo.id != modelo_id)
                    .first()
                )
                if existing_modelo:
                    return {
                        "success": False,
                        "message": "Slug já existe",
                        "data": None,
                    }, 409

            # Atualizar modelo
            for key, value in data.items():
                setattr(modelo, key, value)

            db.session.commit()

            # Retornar modelo atualizado
            schema_response = PeticaoModeloSchema()
            return {
                "success": True,
                "message": "Modelo atualizado com sucesso",
                "data": schema_response.dump(modelo),
            }, 200

        except ValidationError as e:
            return {
                "success": False,
                "message": "Dados inválidos",
                "errors": e.messages,
            }, 400

        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar modelo: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500

    @login_required
    @modelos_ns.marshal_with(response_model)
    @modelos_ns.doc("delete_modelo")
    def delete(self, modelo_id):
        """Desativar um modelo (soft delete)."""
        try:
            modelo = PeticaoModelo.query.get_or_404(modelo_id)

            # Soft delete - apenas marcar como inativo
            modelo.ativo = False
            db.session.commit()

            return {
                "success": True,
                "message": "Modelo desativado com sucesso",
                "data": None,
            }, 200

        except Exception as e:
            current_app.logger.error(f"Erro ao desativar modelo: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500


@modelos_ns.route("/<string:slug>")
class ModeloBySlugResource(Resource):
    """Endpoint para obter modelo por slug."""

    @login_required
    @modelos_ns.marshal_with(response_model)
    @modelos_ns.doc("get_modelo_by_slug")
    def get(self, slug):
        """Obter dados de um modelo por slug."""
        try:
            modelo = PeticaoModelo.query.filter_by(slug=slug, ativo=True).first()

            if not modelo:
                return {
                    "success": False,
                    "message": "Modelo não encontrado",
                    "data": None,
                }, 404

            schema = PeticaoModeloSchema()
            return {
                "success": True,
                "message": "Modelo encontrado",
                "data": schema.dump(modelo),
            }, 200

        except Exception as e:
            current_app.logger.error(f"Erro ao obter modelo por slug: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500
