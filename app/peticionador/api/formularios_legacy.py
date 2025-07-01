"""
Legacy Form API Endpoints
=========================

Endpoints migrados do routes.py para organizar melhor o código.
Estes endpoints mantêm compatibilidade com o frontend existente.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required

from ..models import PeticaoModelo, PeticaoPlaceholder
from app.extensions import db

# Blueprint para endpoints legacy de formulários
formularios_legacy_bp = Blueprint('formularios_legacy', __name__)


@formularios_legacy_bp.route("/api/validate-field", methods=["POST"])
@login_required
def api_validate_field():
    """
    Valida um campo específico do formulário em tempo real.
    Usado para validação enquanto o usuário digita.
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                "success": False,
                "error": "Dados JSON são obrigatórios"
            }), 400
        
        field_name = dados.get("field_name")
        field_value = dados.get("field_value")
        field_type = dados.get("field_type", "text")
        
        if not field_name:
            return jsonify({
                "success": False,
                "error": "Nome do campo é obrigatório"
            }), 400
        
        # Validações por tipo de campo
        validation_result = {
            "valid": True,
            "message": "",
            "formatted_value": field_value
        }
        
        # Validação de CPF
        if "cpf" in field_name.lower() and field_value:
            from app.validators.cliente_validator import ClienteValidator
            valido, cpf_limpo, erro = ClienteValidator.validar_cpf(field_value)
            
            if not valido:
                validation_result["valid"] = False
                validation_result["message"] = erro
            else:
                # Formatar CPF
                if len(cpf_limpo) == 11:
                    cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:11]}"
                    validation_result["formatted_value"] = cpf_formatado
        
        # Validação de Email
        elif "email" in field_name.lower() and field_value:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, field_value):
                validation_result["valid"] = False
                validation_result["message"] = "Email inválido"
        
        # Validação de CEP
        elif "cep" in field_name.lower() and field_value:
            import re
            # Remover formatação e validar
            cep_digits = re.sub(r'\D', '', field_value)
            if len(cep_digits) != 8:
                validation_result["valid"] = False
                validation_result["message"] = "CEP deve ter 8 dígitos"
            else:
                # Formatar CEP
                cep_formatado = f"{cep_digits[:5]}-{cep_digits[5:]}"
                validation_result["formatted_value"] = cep_formatado
        
        # Validação de telefone
        elif "telefone" in field_name.lower() and field_value:
            import re
            telefone_digits = re.sub(r'\D', '', field_value)
            if len(telefone_digits) not in [10, 11]:
                validation_result["valid"] = False
                validation_result["message"] = "Telefone deve ter 10 ou 11 dígitos"
            else:
                # Formatar telefone
                if len(telefone_digits) == 11:
                    telefone_formatado = f"({telefone_digits[:2]}) {telefone_digits[2:7]}-{telefone_digits[7:]}"
                else:
                    telefone_formatado = f"({telefone_digits[:2]}) {telefone_digits[2:6]}-{telefone_digits[6:]}"
                validation_result["formatted_value"] = telefone_formatado
        
        return jsonify({
            "success": True,
            "field_name": field_name,
            "validation": validation_result
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na validação de campo: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500


@formularios_legacy_bp.route("/api/validate-form", methods=["POST"])
@login_required
def api_validate_form():
    """
    Valida um formulário completo antes da submissão.
    Verifica todos os campos obrigatórios e formatos.
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                "success": False,
                "error": "Dados JSON são obrigatórios"
            }), 400
        
        form_data = dados.get("form_data", {})
        modelo_id = dados.get("modelo_id")
        
        validation_errors = []
        
        # Se modelo_id fornecido, validar campos obrigatórios
        if modelo_id:
            placeholders = PeticaoPlaceholder.query.filter_by(
                modelo_id=modelo_id,
                obrigatorio=True
            ).all()
            
            for placeholder in placeholders:
                field_value = form_data.get(placeholder.chave)
                if not field_value or str(field_value).strip() == "":
                    validation_errors.append({
                        "field": placeholder.chave,
                        "message": f"{placeholder.label_form or placeholder.chave} é obrigatório"
                    })
        
        # Validações específicas
        for field_name, field_value in form_data.items():
            if not field_value:
                continue
            
            # Validar CPF
            if "cpf" in field_name.lower():
                from app.validators.cliente_validator import ClienteValidator
                valido, _, erro = ClienteValidator.validar_cpf(field_value)
                if not valido:
                    validation_errors.append({
                        "field": field_name,
                        "message": erro
                    })
            
            # Validar email
            elif "email" in field_name.lower():
                import re
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', field_value):
                    validation_errors.append({
                        "field": field_name,
                        "message": "Email inválido"
                    })
        
        return jsonify({
            "success": len(validation_errors) == 0,
            "errors": validation_errors,
            "total_errors": len(validation_errors)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na validação de formulário: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500


@formularios_legacy_bp.route("/api/preview-document", methods=["POST"])
@login_required
def api_preview_document():
    """
    Gera uma prévia do documento antes da criação final.
    Permite ao usuário revisar o conteúdo antes de confirmar.
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                "success": False,
                "error": "Dados JSON são obrigatórios"
            }), 400
        
        modelo_id = dados.get("modelo_id")
        form_data = dados.get("form_data", {})
        
        if not modelo_id:
            return jsonify({
                "success": False,
                "error": "ID do modelo é obrigatório"
            }), 400
        
        # Buscar modelo
        modelo = PeticaoModelo.query.get(modelo_id)
        if not modelo:
            return jsonify({
                "success": False,
                "error": "Modelo não encontrado"
            }), 404
        
        # Gerar prévia HTML simples
        preview_html = f"""
        <div class="document-preview">
            <h2>{modelo.nome}</h2>
            <div class="preview-content">
                <h3>Dados do Formulário</h3>
                <table class="table table-sm">
        """
        
        # Adicionar dados do formulário à prévia
        for field_name, field_value in form_data.items():
            if field_value:
                label = field_name.replace("_", " ").title()
                preview_html += f"""
                    <tr>
                        <td><strong>{label}:</strong></td>
                        <td>{field_value}</td>
                    </tr>
                """
        
        preview_html += """
                </table>
            </div>
        </div>
        """
        
        return jsonify({
            "success": True,
            "preview_html": preview_html,
            "modelo_nome": modelo.nome
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na geração de prévia: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500


@formularios_legacy_bp.route("/api/analisar-personas/<modelo_id>", methods=["GET"])
@login_required
def api_analisar_personas(modelo_id):
    """
    Analisa as personas detectadas em um modelo.
    Retorna informações sobre tipos de pessoas encontradas no documento.
    """
    try:
        modelo = PeticaoModelo.query.get(modelo_id)
        if not modelo:
            return jsonify({
                "success": False,
                "error": "Modelo não encontrado"
            }), 404
        
        # Buscar placeholders do modelo
        placeholders = PeticaoPlaceholder.query.filter_by(modelo_id=modelo_id).all()
        chaves = [p.chave for p in placeholders]
        
        # Analisar personas (importar função do routes)
        from ..routes import detect_persona_patterns
        persona_analysis = detect_persona_patterns(chaves)
        
        # Adicionar estatísticas extras
        analise_completa = {
            "modelo_id": modelo_id,
            "modelo_nome": modelo.nome,
            "total_placeholders": len(chaves),
            "personas_analysis": persona_analysis,
            "categorias_encontradas": {},
            "sugestoes": []
        }
        
        # Contar por categoria
        for placeholder in placeholders:
            categoria = placeholder.categoria or "outros"
            if categoria not in analise_completa["categorias_encontradas"]:
                analise_completa["categorias_encontradas"][categoria] = 0
            analise_completa["categorias_encontradas"][categoria] += 1
        
        # Gerar sugestões
        if persona_analysis["total_personas"] == 0:
            analise_completa["sugestoes"].append("Nenhuma persona detectada - revisar placeholders")
        elif persona_analysis["total_personas"] > 10:
            analise_completa["sugestoes"].append("Muitas personas detectadas - considerar simplificar")
        
        return jsonify({
            "success": True,
            "analise": analise_completa
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na análise de personas: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500


@formularios_legacy_bp.route("/api/gerar-campos-dinamicos", methods=["POST"])
@login_required
def api_gerar_campos_dinamicos():
    """
    Gera campos de formulário dinamicamente baseado em placeholders.
    Usado para criar formulários on-the-fly.
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                "success": False,
                "error": "Dados JSON são obrigatórios"
            }), 400
        
        placeholders = dados.get("placeholders", [])
        
        if not placeholders:
            return jsonify({
                "success": False,
                "error": "Lista de placeholders é obrigatória"
            }), 400
        
        # Gerar campos dinamicamente
        campos_gerados = []
        
        for i, placeholder in enumerate(placeholders):
            if isinstance(placeholder, str):
                chave = placeholder
                tipo = "text"
                label = placeholder.replace("_", " ").title()
                obrigatorio = False
            else:
                chave = placeholder.get("chave", f"campo_{i}")
                tipo = placeholder.get("tipo", "text")
                label = placeholder.get("label", chave.replace("_", " ").title())
                obrigatorio = placeholder.get("obrigatorio", False)
            
            # Determinar tipo de campo baseado na chave
            if "email" in chave.lower():
                tipo = "email"
            elif "telefone" in chave.lower():
                tipo = "tel"
            elif "data" in chave.lower() or "nascimento" in chave.lower():
                tipo = "date"
            elif "cpf" in chave.lower():
                tipo = "text"
                # Adicionar máscara de CPF
            elif "cep" in chave.lower():
                tipo = "text"
                # Adicionar máscara de CEP
            
            campo = {
                "chave": chave,
                "tipo": tipo,
                "label": label,
                "obrigatorio": obrigatorio,
                "ordem": i + 1,
                "placeholder_text": f"Digite {label.lower()}",
                "css_class": "form-control",
                "validacao": {}
            }
            
            # Adicionar validações específicas
            if "cpf" in chave.lower():
                campo["validacao"]["pattern"] = r"\d{3}\.\d{3}\.\d{3}-\d{2}"
                campo["validacao"]["mask"] = "999.999.999-99"
            elif "cep" in chave.lower():
                campo["validacao"]["pattern"] = r"\d{5}-\d{3}"
                campo["validacao"]["mask"] = "99999-999"
            elif "telefone" in chave.lower():
                campo["validacao"]["mask"] = "(99) 99999-9999"
            
            campos_gerados.append(campo)
        
        return jsonify({
            "success": True,
            "campos": campos_gerados,
            "total_campos": len(campos_gerados)
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na geração de campos dinâmicos: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500