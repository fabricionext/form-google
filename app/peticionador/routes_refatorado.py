"""
REFATORAÇÃO SEGURA - Nova implementação da rota preencher_formulario_dinamico

Esta implementação usa os services e pode ser testada através da rota V2.
Uma vez validada, pode substituir a implementação original.
"""

from flask import current_app, request, render_template, jsonify, abort
from flask_login import login_required

from . import peticionador_bp
from .services import FormularioService, DocumentoService


def preencher_formulario_dinamico_refatorado(slug):
    """
    VERSÃO REFATORADA da rota preencher_formulario_dinamico.
    Demonstra como ficaria com a camada de serviços.
    
    BENEFÍCIOS:
    - Rota com apenas 30 linhas (vs 230 linhas originais)
    - Responsabilidades bem separadas
    - Fácil de testar unitariamente
    - Reutilização de lógica entre rotas
    """
    try:
        current_app.logger.info(f"[V2] Processando formulário com slug: {slug}")
        
        # 1. Instanciar services (responsabilidade única)
        form_service = FormularioService(slug)
        
        # 2. Construir formulário dinâmico
        DynamicForm = form_service.build_dynamic_form_class()
        form = DynamicForm()

        # 3. Processar submissão (POST)
        if request.method == "POST":
            try:
                current_app.logger.info(f"[V2] Processando submissão POST para '{form_service.form_gerado.nome}'")
                
                # Delegação para serviço de documentos
                doc_service = DocumentoService()
                novo_id, link = doc_service.gerar_documento_dinamico(
                    form_service.modelo, 
                    request.form, 
                    form_service.placeholders
                )
                
                if novo_id:
                    current_app.logger.info(f"[V2] Documento gerado com sucesso! ID: {novo_id}")
                    return jsonify({"success": True, "link": link})
                else:
                    raise Exception("Falha ao gerar o ID do documento.")
                    
            except Exception as e:
                current_app.logger.error(f"[V2] Erro ao gerar documento: {e}", exc_info=True)
                return jsonify({"success": False, "error": str(e)}), 500

        # 4. Renderizar formulário (GET)
        current_app.logger.info(f"[V2] Renderizando formulário para slug: {slug}")
        campo_grupos = form_service.agrupar_campos_por_categoria()
        
        return render_template(
            "peticionador/formulario_dinamico.html",
            form=form,
            modelo=form_service.modelo,
            form_gerado=form_service.form_gerado,
            campo_grupos=campo_grupos,
        )
        
    except Exception as e:
        # Tratamento de erros gerais
        current_app.logger.error(f"[V2] Erro na rota: {e}", exc_info=True)
        if "404" in str(e):
            abort(404, description=str(e))
        else:
            abort(500, description="Erro interno do servidor")


# ROTA V2 ATIVA - Para testes paralelos sem afetar a produção
@peticionador_bp.route("/formularios/<slug>/v2", methods=["GET", "POST"])
@login_required  
def preencher_formulario_dinamico_v2(slug):
    """
    NOVA ROTA V2 - Para testes paralelos sem afetar a produção
    
    Esta rota usa os novos services e pode ser testada independentemente.
    Uma vez validada, a rota original pode ser migrada.
    
    Teste através de: /formularios/{seu-slug}/v2
    """
    return preencher_formulario_dinamico_refatorado(slug) 