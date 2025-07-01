"""
Legacy Authority API Endpoints
==============================

Endpoints migrados do routes.py para organizar melhor o código.
Estes endpoints mantêm compatibilidade com o frontend existente.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required

from ..models import AutoridadeTransito
from app.extensions import db

# Blueprint para endpoints legacy de autoridades
autoridades_legacy_bp = Blueprint('autoridades_legacy', __name__)


@autoridades_legacy_bp.route("/api/autoridades/busca", methods=["GET"])
@login_required
def api_busca_autoridade():
    """
    Busca autoridades de trânsito por nome ou cidade.
    Endpoint usado para autocomplete em formulários.
    """
    try:
        termo_busca = request.args.get("q", "").strip()
        limite = request.args.get("limit", 10, type=int)
        
        if not termo_busca:
            return jsonify({
                "success": False,
                "error": "Termo de busca é obrigatório"
            }), 400
        
        if len(termo_busca) < 2:
            return jsonify({
                "success": False,
                "error": "Termo de busca deve ter pelo menos 2 caracteres"
            }), 400
        
        # Buscar por nome ou cidade usando ILIKE (case-insensitive)
        autoridades = AutoridadeTransito.query.filter(
            db.or_(
                AutoridadeTransito.nome.ilike(f"%{termo_busca}%"),
                AutoridadeTransito.cidade.ilike(f"%{termo_busca}%"),
                AutoridadeTransito.sigla.ilike(f"%{termo_busca}%")
            )
        ).limit(limite).all()
        
        # Formatar resultados
        resultados = []
        for autoridade in autoridades:
            resultados.append({
                "id": autoridade.id,
                "nome": autoridade.nome,
                "sigla": autoridade.sigla,
                "cidade": autoridade.cidade,
                "estado": autoridade.estado,
                "endereco": autoridade.endereco,
                "telefone": autoridade.telefone,
                "email": autoridade.email,
                "display_name": f"{autoridade.nome} - {autoridade.cidade}/{autoridade.estado}"
            })
        
        current_app.logger.info(f"API: {len(resultados)} autoridades encontradas para '{termo_busca}'")
        return jsonify({
            "success": True,
            "autoridades": resultados,
            "total": len(resultados)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na busca de autoridades: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500


@autoridades_legacy_bp.route("/api/autoridades", methods=["POST"])
@login_required
def api_criar_autoridade():
    """
    Cria uma nova autoridade de trânsito via API.
    Endpoint para criação rápida durante preenchimento de formulários.
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                "success": False,
                "error": "Dados JSON são obrigatórios"
            }), 400
        
        # Validar campos obrigatórios
        campos_obrigatorios = ["nome", "cidade", "estado"]
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return jsonify({
                    "success": False,
                    "error": f"Campo '{campo}' é obrigatório"
                }), 400
        
        # Verificar se já existe autoridade com mesmo nome na mesma cidade
        existe = AutoridadeTransito.query.filter_by(
            nome=dados["nome"],
            cidade=dados["cidade"],
            estado=dados["estado"]
        ).first()
        
        if existe:
            return jsonify({
                "success": False,
                "error": "Autoridade já cadastrada para esta cidade/estado"
            }), 409
        
        # Criar nova autoridade
        autoridade = AutoridadeTransito()
        autoridade.nome = dados["nome"]
        autoridade.sigla = dados.get("sigla", "")
        autoridade.cidade = dados["cidade"]
        autoridade.estado = dados["estado"]
        autoridade.endereco = dados.get("endereco", "")
        autoridade.telefone = dados.get("telefone", "")
        autoridade.email = dados.get("email", "")
        
        db.session.add(autoridade)
        db.session.commit()
        
        # Retornar autoridade criada
        resultado = {
            "id": autoridade.id,
            "nome": autoridade.nome,
            "sigla": autoridade.sigla,
            "cidade": autoridade.cidade,
            "estado": autoridade.estado,
            "endereco": autoridade.endereco,
            "telefone": autoridade.telefone,
            "email": autoridade.email,
            "display_name": f"{autoridade.nome} - {autoridade.cidade}/{autoridade.estado}"
        }
        
        current_app.logger.info(f"API: Autoridade criada - {autoridade.nome}")
        return jsonify({
            "success": True,
            "autoridade": resultado,
            "message": "Autoridade criada com sucesso"
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar autoridade: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500


@autoridades_legacy_bp.route("/api/autoridades/todas", methods=["GET"])
@login_required
def api_listar_todas_autoridades():
    """
    Lista todas as autoridades de trânsito.
    Endpoint otimizado para dropdown/autocomplete.
    """
    try:
        autoridades = AutoridadeTransito.query.order_by(
            AutoridadeTransito.estado,
            AutoridadeTransito.cidade,
            AutoridadeTransito.nome
        ).all()
        
        # Formatar para resposta JSON
        autoridades_list = []
        for autoridade in autoridades:
            autoridades_list.append({
                "id": autoridade.id,
                "nome": autoridade.nome,
                "sigla": autoridade.sigla,
                "cidade": autoridade.cidade,
                "estado": autoridade.estado,
                "endereco": autoridade.endereco,
                "telefone": autoridade.telefone,
                "email": autoridade.email,
                "display_name": f"{autoridade.nome} - {autoridade.cidade}/{autoridade.estado}"
            })
        
        current_app.logger.info(f"API: Lista de {len(autoridades_list)} autoridades enviada")
        return jsonify({
            "success": True,
            "autoridades": autoridades_list,
            "total": len(autoridades_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar autoridades: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500