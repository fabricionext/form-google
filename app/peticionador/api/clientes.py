# Standard library imports

# Third party imports
from flask import current_app, request
from flask_login import login_required
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError

# Local application imports
from extensions import db

from ..models import Cliente, TipoPessoaEnum
from ..schemas.cliente_schema import (
    ClienteCreateSchema,
    ClienteListSchema,
    ClienteSchema,
    ClienteUpdateSchema,
)

# Create namespace
clientes_ns = Namespace("clientes", description="Operações com clientes")

# API Models for documentation
cliente_model = clientes_ns.model(
    "Cliente",
    {
        "id": fields.Integer(description="ID do cliente"),
        "tipo_pessoa": fields.String(description="Tipo de pessoa (FISICA/JURIDICA)"),
        "email": fields.String(description="Email do cliente"),
        "telefone_celular": fields.String(description="Telefone celular"),
        "primeiro_nome": fields.String(description="Primeiro nome"),
        "sobrenome": fields.String(description="Sobrenome"),
        "cpf": fields.String(description="CPF"),
        "endereco_cidade": fields.String(description="Cidade"),
        "endereco_estado": fields.String(description="Estado"),
    },
)

cliente_create_model = clientes_ns.model(
    "ClienteCreate",
    {
        "tipo_pessoa": fields.String(required=True, description="FISICA ou JURIDICA"),
        "email": fields.String(required=True, description="Email do cliente"),
        "primeiro_nome": fields.String(description="Primeiro nome"),
        "sobrenome": fields.String(description="Sobrenome"),
        "cpf": fields.String(description="CPF"),
        "telefone_celular": fields.String(description="Telefone celular"),
        "endereco_logradouro": fields.String(description="Logradouro"),
        "endereco_numero": fields.String(description="Número"),
        "endereco_cidade": fields.String(description="Cidade"),
        "endereco_estado": fields.String(description="Estado"),
        "endereco_cep": fields.String(description="CEP"),
    },
)

response_model = clientes_ns.model(
    "ClienteResponse",
    {
        "success": fields.Boolean(description="Sucesso da operação"),
        "message": fields.String(description="Mensagem de retorno"),
        "data": fields.Raw(description="Dados do cliente"),
    },
)


@clientes_ns.route("/")
class ClienteListResource(Resource):
    """Endpoint para listagem e criação de clientes."""

    @login_required
    @clientes_ns.marshal_list_with(cliente_model)
    @clientes_ns.doc("list_clientes")
    def get(self):
        """Listar todos os clientes."""
        try:
            clientes = Cliente.query.order_by(Cliente.id.desc()).all()
            schema = ClienteListSchema(many=True)
            return schema.dump(clientes), 200

        except Exception as e:
            current_app.logger.error(f"Erro ao listar clientes: {str(e)}")
            return {"message": "Erro interno do servidor"}, 500

    @login_required
    @clientes_ns.expect(cliente_create_model)
    @clientes_ns.marshal_with(response_model)
    @clientes_ns.doc("create_cliente")
    def post(self):
        """Criar novo cliente."""
        try:
            # Validar dados de entrada
            schema = ClienteCreateSchema()
            data = schema.load(request.json)

            # Verificar se email já existe
            existing_cliente = Cliente.query.filter_by(email=data["email"]).first()
            if existing_cliente:
                return {
                    "success": False,
                    "message": "Email já cadastrado",
                    "data": None,
                }, 409

            # Verificar CPF se for pessoa física
            if data.get("tipo_pessoa") == "FISICA" and data.get("cpf"):
                existing_cpf = Cliente.query.filter_by(cpf=data["cpf"]).first()
                if existing_cpf:
                    return {
                        "success": False,
                        "message": "CPF já cadastrado",
                        "data": None,
                    }, 409

            # Criar cliente
            cliente = Cliente()
            for key, value in data.items():
                if key == "tipo_pessoa":
                    setattr(cliente, key, TipoPessoaEnum[value])
                else:
                    setattr(cliente, key, value)

            db.session.add(cliente)
            db.session.commit()

            # Retornar cliente criado
            schema_response = ClienteSchema()
            return {
                "success": True,
                "message": "Cliente criado com sucesso",
                "data": schema_response.dump(cliente),
            }, 201

        except ValidationError as e:
            return {
                "success": False,
                "message": "Dados inválidos",
                "errors": e.messages,
            }, 400

        except Exception as e:
            current_app.logger.error(f"Erro ao criar cliente: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500


@clientes_ns.route("/<int:cliente_id>")
class ClienteResource(Resource):
    """Endpoint para operações com cliente específico."""

    @login_required
    @clientes_ns.marshal_with(response_model)
    @clientes_ns.doc("get_cliente")
    def get(self, cliente_id):
        """Obter dados de um cliente específico."""
        try:
            cliente = Cliente.query.get_or_404(cliente_id)
            schema = ClienteSchema()
            return {
                "success": True,
                "message": "Cliente encontrado",
                "data": schema.dump(cliente),
            }, 200

        except Exception as e:
            current_app.logger.error(f"Erro ao obter cliente: {str(e)}")
            return {
                "success": False,
                "message": "Cliente não encontrado",
                "data": None,
            }, 404

    @login_required
    @clientes_ns.expect(cliente_model)
    @clientes_ns.marshal_with(response_model)
    @clientes_ns.doc("update_cliente")
    def put(self, cliente_id):
        """Atualizar dados de um cliente."""
        try:
            cliente = Cliente.query.get_or_404(cliente_id)

            # Validar dados de entrada
            schema = ClienteUpdateSchema()
            data = schema.load(request.json)

            # Verificar se email já existe (exceto o próprio cliente)
            if "email" in data:
                existing_cliente = (
                    Cliente.query.filter_by(email=data["email"])
                    .filter(Cliente.id != cliente_id)
                    .first()
                )
                if existing_cliente:
                    return {
                        "success": False,
                        "message": "Email já cadastrado",
                        "data": None,
                    }, 409

            # Atualizar cliente
            for key, value in data.items():
                if key == "tipo_pessoa":
                    setattr(cliente, key, TipoPessoaEnum[value])
                else:
                    setattr(cliente, key, value)

            db.session.commit()

            # Retornar cliente atualizado
            schema_response = ClienteSchema()
            return {
                "success": True,
                "message": "Cliente atualizado com sucesso",
                "data": schema_response.dump(cliente),
            }, 200

        except ValidationError as e:
            return {
                "success": False,
                "message": "Dados inválidos",
                "errors": e.messages,
            }, 400

        except Exception as e:
            current_app.logger.error(f"Erro ao atualizar cliente: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500

    @login_required
    @clientes_ns.marshal_with(response_model)
    @clientes_ns.doc("delete_cliente")
    def delete(self, cliente_id):
        """Excluir um cliente."""
        try:
            cliente = Cliente.query.get_or_404(cliente_id)

            db.session.delete(cliente)
            db.session.commit()

            return {
                "success": True,
                "message": "Cliente excluído com sucesso",
                "data": None,
            }, 200

        except Exception as e:
            current_app.logger.error(f"Erro ao excluir cliente: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500
