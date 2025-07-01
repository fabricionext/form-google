"""
Rotas públicas para formulários - sem necessidade de autenticação.
"""

from flask import (
    render_template, 
    request, 
    jsonify, 
    current_app,
    flash,
    redirect,
    url_for
)
from . import public_bp

# Import services
from app.peticionador.services.formulario_service import FormularioService
from app.peticionador.services.documento_service import DocumentoService


@public_bp.route("/formularios/<string:formulario_slug>", methods=["GET", "POST"])
def formulario_publico(formulario_slug):
    """
    Rota pública para acesso a formulários sem necessidade de login.
    Esta é a rota correta para usuários finais preencherem formulários.
    """
    try:
        current_app.logger.info(f"[PUBLIC] Acessando formulário público: {formulario_slug}")
        
        # 1. Instanciar service (sem login_required)
        form_service = FormularioService(formulario_slug)
        
        # 2. Verificar se formulário existe e está ativo
        if not form_service.form_gerado:
            current_app.logger.error(f"[PUBLIC] Formulário não encontrado: {formulario_slug}")
            return render_template("errors/404.html", 
                                 message="Formulário não encontrado"), 404
        
        # 3. Construir formulário dinâmico
        DynamicForm = form_service.build_dynamic_form_class()
        form = DynamicForm(request.form)

        # 4. Processar submissão (POST)
        if request.method == 'POST' and form.validate_on_submit():
            try:
                current_app.logger.info(f"[PUBLIC] Processando submissão para '{form_service.form_gerado.nome}'")
                
                # Delegação para serviço de documentos
                doc_service = DocumentoService()
                novo_id, link = doc_service.gerar_documento_dinamico(
                    form_service.modelo, 
                    request.form, 
                    form_service.placeholders
                )
                
                if novo_id:
                    current_app.logger.info(f"[PUBLIC] Documento gerado com sucesso! ID: {novo_id}")
                    return jsonify({
                        "success": True, 
                        "link": link,
                        "message": "Documento gerado com sucesso!"
                    })
                else:
                    raise Exception("Falha ao gerar o documento.")
                    
            except Exception as e:
                current_app.logger.error(f"[PUBLIC] Erro ao gerar documento: {e}", exc_info=True)
                return jsonify({
                    "success": False, 
                    "error": "Erro ao gerar o documento. Tente novamente."
                }), 500

        # 5. Renderizar formulário (GET)
        current_app.logger.info(f"[PUBLIC] Renderizando formulário público: {formulario_slug}")
        campo_grupos = form_service.agrupar_campos_por_categoria()
        
        return render_template(
            "public/formulario_publico.html",
            form=form,
            modelo=form_service.modelo,
            form_gerado=form_service.form_gerado,
            campo_grupos=campo_grupos,
            formulario_slug=formulario_slug
        )
        
    except Exception as e:
        current_app.logger.error(f"[PUBLIC] Erro no formulário público {formulario_slug}: {e}", exc_info=True)
        return render_template("errors/500.html", 
                             message="Erro interno do servidor"), 500


@public_bp.route("/formularios", methods=["GET"])
def listar_formularios_publicos():
    """
    Lista todos os formulários públicos disponíveis.
    """
    try:
        from app.peticionador.models import FormularioGerado
        
        formularios = FormularioGerado.query.all()
        
        return render_template(
            "public/lista_formularios.html",
            formularios=formularios
        )
        
    except Exception as e:
        current_app.logger.error(f"[PUBLIC] Erro ao listar formulários: {e}", exc_info=True)
        return render_template("errors/500.html"), 500


# @public_bp.route("/", methods=["GET"])
# def home():
#     """
#     Página inicial pública redirecionando para lista de formulários.
#     COMENTADO: A rota raiz agora é servida pelo frontend Vue.js via nginx
#     """
#     return redirect(url_for('public.listar_formularios_publicos'))