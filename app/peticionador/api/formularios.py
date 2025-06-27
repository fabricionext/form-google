# Standard library imports

# Third party imports
from flask import current_app, request
from flask_login import login_required
from flask_restx import Namespace, Resource, fields
from marshmallow import ValidationError

# Local application imports
from extensions import db

from ..models import FormularioGerado, PeticaoModelo
from ..schemas.formulario_schema import (
    FormularioResponseSchema,
    FormularioSchema,
    FormularioSubmissionSchema,
)

# Create namespace
formularios_ns = Namespace(
    "formularios", description="Operações com formulários dinâmicos"
)

# API Models for documentation
formulario_model = formularios_ns.model(
    "Formulario",
    {
        "modelo_slug": fields.String(required=True, description="Slug do modelo"),
        "dados_formulario": fields.Raw(
            required=True, description="Dados do formulário"
        ),
        "nome_documento": fields.String(description="Nome do documento"),
        "observacoes": fields.String(description="Observações"),
    },
)

formulario_submission_model = formularios_ns.model(
    "FormularioSubmission",
    {
        "modelo_id": fields.Integer(required=True, description="ID do modelo"),
        "dados_cliente": fields.Raw(required=True, description="Dados do cliente"),
        "dados_formulario": fields.Raw(
            required=True, description="Dados do formulário"
        ),
        "tipo_pessoa": fields.String(required=True, description="pf ou pj"),
        "documentos_requeridos": fields.List(
            fields.String, description="Documentos necessários"
        ),
    },
)

response_model = formularios_ns.model(
    "FormularioResponse",
    {
        "success": fields.Boolean(description="Sucesso da operação"),
        "message": fields.String(description="Mensagem de retorno"),
        "data": fields.Raw(description="Dados de resposta"),
        "errors": fields.List(fields.Raw, description="Lista de erros"),
        "document_url": fields.String(description="URL do documento gerado"),
        "redirect_url": fields.String(description="URL de redirecionamento"),
    },
)


@formularios_ns.route("/<string:modelo_slug>")
class FormularioResource(Resource):
    """Endpoint para operações com formulário específico."""

    @login_required
    @formularios_ns.marshal_with(response_model)
    @formularios_ns.doc("get_formulario")
    def get(self, modelo_slug):
        """Obter dados de um formulário por slug do modelo."""
        try:
            modelo = PeticaoModelo.query.filter_by(slug=modelo_slug, ativo=True).first()

            if not modelo:
                return {
                    "success": False,
                    "message": "Modelo não encontrado",
                    "data": None,
                }, 404

            # Buscar placeholders do modelo
            placeholders = []
            for placeholder in modelo.formulario_placeholders:
                if placeholder.ativo:
                    placeholders.append(
                        {
                            "chave": placeholder.chave,
                            "label": placeholder.label,
                            "tipo_campo": placeholder.tipo_campo,
                            "categoria": placeholder.categoria,
                            "obrigatorio": placeholder.obrigatorio,
                            "placeholder_text": placeholder.placeholder_text,
                            "opcoes_json": placeholder.opcoes_json,
                            "ordem": placeholder.ordem,
                        }
                    )

            return {
                "success": True,
                "message": "Formulário encontrado",
                "data": {
                    "modelo": {
                        "id": modelo.id,
                        "nome": modelo.nome,
                        "slug": modelo.slug,
                        "descricao": modelo.descricao,
                    },
                    "placeholders": sorted(placeholders, key=lambda x: x["ordem"]),
                },
            }, 200

        except Exception as e:
            current_app.logger.error(f"Erro ao obter formulário: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500

    @login_required
    @formularios_ns.expect(formulario_submission_model)
    @formularios_ns.marshal_with(response_model)
    @formularios_ns.doc("submit_formulario")
    def post(self, modelo_slug):
        """Submeter formulário preenchido para processamento."""
        try:
            # Validar dados de entrada
            schema = FormularioSubmissionSchema()
            data = schema.load(request.json)

            # Verificar se modelo existe
            modelo = PeticaoModelo.query.filter_by(slug=modelo_slug, ativo=True).first()
            if not modelo:
                return {
                    "success": False,
                    "message": "Modelo não encontrado",
                    "data": None,
                }, 404

            # Log dos dados recebidos
            current_app.logger.info(
                f"Dados do formulário recebidos para {modelo_slug}: {data}"
            )

            # Por enquanto, apenas processar e retornar sucesso
            # Aqui seria chamado o serviço de geração de documento

            return {
                "success": True,
                "message": "Formulário processado com sucesso! Processamento em desenvolvimento.",
                "data": {
                    "modelo_slug": modelo_slug,
                    "processed_at": db.func.now(),
                },
                "redirect_url": f"/peticionador/formularios/{modelo_slug}",
            }, 200

        except ValidationError as e:
            return {
                "success": False,
                "message": "Dados inválidos",
                "errors": [
                    {"field": field, "message": messages}
                    for field, messages in e.messages.items()
                ],
            }, 400

        except Exception as e:
            current_app.logger.error(
                f"Erro ao processar formulário {modelo_slug}: {str(e)}"
            )
            return {
                "success": False,
                "message": f"Erro ao processar formulário: {str(e)}",
                "data": None,
            }, 500


@formularios_ns.route("/<string:slug>/excluir")
class FormularioDeleteResource(Resource):
    """Endpoint para exclusão de formulários gerados."""

    @login_required
    @formularios_ns.marshal_with(response_model)
    @formularios_ns.doc("delete_formulario")
    def post(self, slug):
        """Excluir um formulário gerado."""
        try:
            form_gerado = FormularioGerado.query.filter_by(slug=slug).first()

            if not form_gerado:
                return {
                    "success": False,
                    "message": "Formulário não encontrado",
                    "data": None,
                }, 404

            db.session.delete(form_gerado)
            db.session.commit()

            return {
                "success": True,
                "message": "Formulário excluído com sucesso",
                "data": None,
            }, 200

        except Exception as e:
            current_app.logger.error(f"Erro ao excluir formulário: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500


@formularios_ns.route("/validar")
class FormularioValidationResource(Resource):
    """Endpoint para validação de dados de formulário."""

    @login_required
    @formularios_ns.expect(formulario_model)
    @formularios_ns.marshal_with(response_model)
    @formularios_ns.doc("validate_formulario")
    def post(self):
        """Validar dados de formulário sem processar."""
        try:
            # Validar dados de entrada
            schema = FormularioSchema()
            data = schema.load(request.json)

            # Verificar se modelo existe
            modelo = PeticaoModelo.query.filter_by(
                slug=data["modelo_slug"], ativo=True
            ).first()

            if not modelo:
                return {
                    "success": False,
                    "message": "Modelo não encontrado",
                    "data": None,
                }, 404

            # Validar campos obrigatórios do formulário
            errors = []
            dados_formulario = data["dados_formulario"]

            for placeholder in modelo.formulario_placeholders:
                if placeholder.ativo and placeholder.obrigatorio:
                    if (
                        placeholder.chave not in dados_formulario
                        or not dados_formulario[placeholder.chave]
                    ):
                        errors.append(
                            {
                                "field": placeholder.chave,
                                "message": f"{placeholder.label} é obrigatório",
                            }
                        )

            if errors:
                return {
                    "success": False,
                    "message": "Campos obrigatórios não preenchidos",
                    "errors": errors,
                }, 400

            return {
                "success": True,
                "message": "Formulário válido",
                "data": {"valid": True},
            }, 200

        except ValidationError as e:
            return {
                "success": False,
                "message": "Dados inválidos",
                "errors": [
                    {"field": field, "message": messages}
                    for field, messages in e.messages.items()
                ],
            }, 400

        except Exception as e:
            current_app.logger.error(f"Erro na validação: {str(e)}")
            return {
                "success": False,
                "message": "Erro interno do servidor",
                "data": None,
            }, 500
