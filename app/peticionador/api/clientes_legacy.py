"""
Legacy Client API Endpoints
===========================

Endpoints migrados do routes.py para organizar melhor o código.
Estes endpoints mantêm compatibilidade com o frontend existente.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required

from ..models import Cliente
from app.validators.cliente_validator import ClienteValidator

# Blueprint para endpoints legacy de clientes
clientes_legacy_bp = Blueprint('clientes_legacy', __name__)


@clientes_legacy_bp.route("/api/clientes/busca_cpf", methods=["GET"], strict_slashes=False)
@login_required
def api_busca_cliente_cpf():
    """Retorna dados do cliente em JSON, padronizados e com tratamento de erros."""
    try:
        cpf_raw = request.args.get("cpf", "").strip()
        current_app.logger.info(f"API: Recebida solicitação de busca de CPF")
        
        # SEGURANÇA: Validação rigorosa do CPF
        valido, cpf_digits, erro = ClienteValidator.validar_cpf(cpf_raw)
        if not valido:
            current_app.logger.warning(f"API: CPF inválido rejeitado - {erro}")
            return jsonify({"success": False, "error": erro}), 400
        
        current_app.logger.info(f"API: Buscando CPF validado com {len(cpf_digits)} dígitos")

        # Buscar pelo CPF no modelo Cliente (corrigido)
        cliente = Cliente.query.filter_by(cpf=cpf_digits).first()

        # Se não encontrou com apenas números, tentar com formatação padrão
        if not cliente:
            cpf_formatado = (
                f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:11]}"
                if len(cpf_digits) == 11
                else cpf_digits
            )
            cliente = Cliente.query.filter_by(cpf=cpf_formatado).first()
            current_app.logger.info(
                f"API: Tentando busca com CPF formatado '{cpf_formatado}'"
            )

        # Se ainda não encontrou, fazer busca usando LIKE para ser mais flexível
        if not cliente:
            cpf_pattern = f"%{cpf_digits}%"
            cliente = Cliente.query.filter(
                Cliente.cpf.like(cpf_pattern)
            ).first()
            current_app.logger.info(
                f"API: Tentando busca com padrão LIKE '{cpf_pattern}'"
            )

        if not cliente:
            current_app.logger.warning(
                f"API: CPF '{cpf_digits}' não encontrado no modelo Cliente com nenhum formato."
            )
            return jsonify({"success": False, "error": "Cliente não encontrado"}), 404
        
        # Converte data_nascimento para string se for datetime/date
        data_nascimento_str = None
        if hasattr(cliente, "data_nascimento") and cliente.data_nascimento:
            if hasattr(cliente.data_nascimento, "isoformat"):
                data_nascimento_str = cliente.data_nascimento.isoformat()
            else:
                data_nascimento_str = str(cliente.data_nascimento)
        
        data = {
            "id": cliente.id,
            "primeiro_nome": cliente.primeiro_nome,
            "sobrenome": cliente.sobrenome,
            "nacionalidade": cliente.nacionalidade,
            "estado_civil": cliente.estado_civil,
            "profissao": cliente.profissao,
            "cpf": cliente.cpf,
            "rg": cliente.rg_numero,
            "estado_emissor_rg": cliente.rg_uf_emissor,
            "cnh_numero": cliente.cnh_numero,
            "razao_social": getattr(cliente, "razao_social", None),
            "cnpj": getattr(cliente, "cnpj", None),
            "endereco_cep": cliente.endereco_cep,
            "endereco_logradouro": cliente.endereco_logradouro,
            "endereco_numero": cliente.endereco_numero,
            "endereco_complemento": cliente.endereco_complemento,
            "endereco_bairro": cliente.endereco_bairro,
            "endereco_cidade": cliente.endereco_cidade,
            "endereco_estado": cliente.endereco_estado,
            "email": cliente.email,
            "telefone_celular": cliente.telefone_celular,
            "telefone_outro": getattr(cliente, "outro_telefone", None),
            "nome_completo": f"{cliente.primeiro_nome or ''} {cliente.sobrenome or ''}".strip(),
            "data_nascimento": data_nascimento_str,
            "rg_uf_emissor": cliente.rg_uf_emissor,
            "rg_numero": cliente.rg_numero,
        }
        current_app.logger.info(
            f"API: Cliente '{data.get('nome_completo')}' encontrado. Enviando dados."
        )
        return jsonify({"success": True, "cliente": data})
    except Exception as e:
        current_app.logger.error(
            f"Erro CRÍTICO na rota api_busca_cliente_cpf: {e}", exc_info=True
        )
        return (
            jsonify(
                {"success": False, "error": "Ocorreu um erro interno no servidor."}
            ),
            500,
        )


@clientes_legacy_bp.route("/api/clientes/busca_nome", methods=["GET"])
@login_required
def api_busca_cliente_nome():
    """
    Busca clientes por primeiro nome e/ou sobrenome com busca fuzzy.
    Desenvolvido especificamente para formulários de auto-preenchimento.
    """
    try:
        # Parâmetros de busca
        primeiro_nome = request.args.get("primeiro_nome", "").strip()
        sobrenome = request.args.get("sobrenome", "").strip()
        
        # Log da busca
        current_app.logger.info(f"API: Busca por nome - primeiro_nome: '{primeiro_nome}', sobrenome: '{sobrenome}'")
        
        # Validação: pelo menos um campo deve ser fornecido
        if not primeiro_nome and not sobrenome:
            return jsonify({
                "success": False,
                "error": "Pelo menos o primeiro nome ou sobrenome deve ser fornecido"
            }), 400
        
        # Construir query com busca fuzzy usando ILIKE (case-insensitive)
        query = Cliente.query
        
        if primeiro_nome:
            query = query.filter(Cliente.primeiro_nome.ilike(f"%{primeiro_nome}%"))
        
        if sobrenome:
            query = query.filter(Cliente.sobrenome.ilike(f"%{sobrenome}%"))
        
        # Ordenar por relevância e limitar resultados
        clientes = query.order_by(Cliente.primeiro_nome, Cliente.sobrenome).limit(10).all()
        
        # Formatar resultados
        resultados = []
        for cliente in clientes:
            # Converter data_nascimento
            data_nascimento_str = None
            if hasattr(cliente, "data_nascimento") and cliente.data_nascimento:
                if hasattr(cliente.data_nascimento, "isoformat"):
                    data_nascimento_str = cliente.data_nascimento.isoformat()
                else:
                    data_nascimento_str = str(cliente.data_nascimento)
            
            cliente_data = {
                "id": cliente.id,
                "primeiro_nome": cliente.primeiro_nome or "",
                "sobrenome": cliente.sobrenome or "",
                "nome_completo": cliente.nome_completo_formatado,
                "cpf": cliente.cpf or "",
                "rg_numero": cliente.rg_numero or "",
                "email": cliente.email or "",
                "telefone_celular": cliente.telefone_celular or "",
                "telefone_outro": cliente.telefone_outro or "",
                "data_nascimento": data_nascimento_str,
                "nacionalidade": cliente.nacionalidade or "",
                "estado_civil": getattr(cliente, 'estado_civil', '') or "",
                "profissao": cliente.profissao or "",
                "cnh_numero": cliente.cnh_numero or "",
                "endereco_logradouro": cliente.endereco_logradouro or "",
                "endereco_numero": cliente.endereco_numero or "",
                "endereco_complemento": cliente.endereco_complemento or "",
                "endereco_bairro": cliente.endereco_bairro or "",
                "endereco_cidade": cliente.endereco_cidade or "",
                "endereco_estado": cliente.endereco_estado or "",
                "endereco_cep": cliente.endereco_cep or "",
                "endereco_formatado": getattr(cliente, 'endereco_formatado', '') or ""
            }
            resultados.append(cliente_data)
        
        current_app.logger.info(f"API: {len(resultados)} cliente(s) encontrado(s) por nome")
        return jsonify({"success": True, "clientes": resultados})
        
    except Exception as e:
        current_app.logger.error(f"Erro na busca por nome: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500


@clientes_legacy_bp.route("/api/clientes/<int:cliente_id>/detalhes")
@login_required
def api_detalhes_cliente(cliente_id):
    """
    Retorna detalhes completos de um cliente específico em formato JSON.
    Endpoint usado para visualização detalhada e edição.
    """
    try:
        # Buscar cliente
        cliente = Cliente.query.get(cliente_id)
        if not cliente:
            current_app.logger.warning(f"API: Cliente ID {cliente_id} não encontrado")
            return jsonify({"success": False, "error": "Cliente não encontrado"}), 404
        
        # Converter para JSON completo
        data_nascimento_str = None
        if hasattr(cliente, "data_nascimento") and cliente.data_nascimento:
            if hasattr(cliente.data_nascimento, "isoformat"):
                data_nascimento_str = cliente.data_nascimento.isoformat()
            else:
                data_nascimento_str = str(cliente.data_nascimento)
        
        # Dados completos do cliente
        cliente_data = {
            "id": cliente.id,
            "tipo_pessoa": cliente.tipo_pessoa.value if cliente.tipo_pessoa else None,
            "primeiro_nome": cliente.primeiro_nome,
            "sobrenome": cliente.sobrenome,
            "nome_completo": getattr(cliente, 'nome_completo_formatado', f"{cliente.primeiro_nome or ''} {cliente.sobrenome or ''}".strip()),
            "cpf": cliente.cpf,
            "rg_numero": cliente.rg_numero,
            "rg_uf_emissor": cliente.rg_uf_emissor,
            "cnh_numero": cliente.cnh_numero,
            "data_nascimento": data_nascimento_str,
            "nacionalidade": cliente.nacionalidade,
            "estado_civil": cliente.estado_civil.value if hasattr(cliente.estado_civil, 'value') else cliente.estado_civil,
            "profissao": cliente.profissao,
            "email": cliente.email,
            "telefone_celular": cliente.telefone_celular,
            "telefone_outro": getattr(cliente, 'telefone_outro', None),
            "endereco_logradouro": cliente.endereco_logradouro,
            "endereco_numero": cliente.endereco_numero,
            "endereco_complemento": cliente.endereco_complemento,
            "endereco_bairro": cliente.endereco_bairro,
            "endereco_cidade": cliente.endereco_cidade,
            "endereco_estado": cliente.endereco_estado,
            "endereco_cep": cliente.endereco_cep,
            "endereco_formatado": getattr(cliente, 'endereco_formatado', ''),
            "observacoes": getattr(cliente, 'observacoes', ''),
            "criado_em": cliente.criado_em.isoformat() if hasattr(cliente, 'criado_em') and cliente.criado_em else None,
            "atualizado_em": cliente.atualizado_em.isoformat() if hasattr(cliente, 'atualizado_em') and cliente.atualizado_em else None
        }
        
        current_app.logger.info(f"API: Detalhes do cliente {cliente_id} enviados")
        return jsonify({"success": True, "cliente": cliente_data})
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter detalhes do cliente {cliente_id}: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500


@clientes_legacy_bp.route("/api/clientes/todos", methods=["GET"])
@login_required
def api_listar_todos_clientes():
    """
    Lista todos os clientes de forma otimizada para dropdown/autocomplete.
    Retorna apenas os campos essenciais para performance.
    """
    try:
        # Buscar apenas os campos necessários para otimizar
        clientes = Cliente.query.with_entities(
            Cliente.id,
            Cliente.primeiro_nome,
            Cliente.sobrenome,
            Cliente.cpf,
            Cliente.email
        ).order_by(Cliente.primeiro_nome, Cliente.sobrenome).all()
        
        # Formatar para resposta JSON
        clientes_list = []
        for cliente in clientes:
            nome_completo = f"{cliente.primeiro_nome or ''} {cliente.sobrenome or ''}".strip()
            clientes_list.append({
                "id": cliente.id,
                "nome_completo": nome_completo,
                "cpf": cliente.cpf or "",
                "email": cliente.email or "",
                "display_name": f"{nome_completo} ({cliente.cpf or 'Sem CPF'})"
            })
        
        current_app.logger.info(f"API: Lista de {len(clientes_list)} clientes enviada")
        return jsonify({
            "success": True,
            "clientes": clientes_list,
            "total": len(clientes_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao listar todos os clientes: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500