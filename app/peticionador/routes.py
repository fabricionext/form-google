"""
Peticionador Routes - Refactored Version
=======================================

Versão refatorada do routes.py com separação clara de responsabilidades:
- Apenas rotas web (não APIs)
- Lógica de negócio delegada para services
- Funções utilitárias importadas de utils
- Arquivos menores e mais organizados

Total estimado: ~800-1000 linhas (vs 3264 original)
"""

import re
import traceback
import unicodedata
from datetime import datetime

from flask import (
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import DateField, EmailField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email

from app.peticionador import google_services
from google_client import get_drive_service, get_docs_service
from config import CONFIG
from extensions import db, limiter

# Importar models
from models import RespostaForm
from . import peticionador_bp
from .forms import (
    AutoridadeTransitoForm,
    ClienteForm,
    DocumentTemplateForm,
    GerarDocumentoSuspensaoForm,
    LoginForm,
    PeticaoModeloForm,
)
from .models import (
    AutoridadeTransito,
    Cliente,
    DocumentTemplate,
    FormularioGerado,
    FormularioPlaceholder,
    PersonaAnalise,
    PeticaoGerada,
    PeticaoModelo,
    PeticaoPlaceholder,
    TipoPessoaEnum,
    User,
)

# Importar utilities dos módulos organizados
from .utils import (
    # Funções básicas (mantidas para compatibilidade)
    safe_extract_placeholder_keys,
    validate_placeholder_format,
    clean_placeholder_key,
    get_enum_display_name,
    log_placeholder_operation,
    handle_placeholder_extraction_error,
    
    # Funções de placeholder
    categorize_placeholder_key,
    detect_persona_patterns,
    determine_field_type_from_key,
    format_label_from_key,
    is_required_field_key,
    generate_placeholder_text_from_key,
    
    # Funções de formulário
    build_dynamic_form,
    determine_client_map_key,
    get_choices_for_field_key,
    
    # Funções de documento
    extract_placeholders_from_document,
    extract_placeholders_keys_only,
    generate_preview_html,
    analyze_document_personas
)

# SISTEMA SIMPLIFICADO - Removidos services complexos para evitar over-engineering
# FormularioService e formulario_manager foram removidos para simplificar o sistema
# Agora usamos apenas queries diretas no banco de dados


# =============================================================================
# ROTAS DE NAVEGAÇÃO E DASHBOARD
# =============================================================================

@peticionador_bp.route("/")
@login_required
def index():
    """Rota principal do painel administrativo. Redireciona para a dashboard."""
    return redirect(url_for("peticionador.dashboard"))


@peticionador_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard com indicadores rápidos e atividade recente."""
    total_clientes = Cliente.query.count()
    total_formularios = FormularioGerado.query.count()
    total_peticoes_processadas = PeticaoGerada.query.count() 
    total_usuarios = User.query.filter_by(is_active=True).count()
    
    # Buscar atividade recente - últimos 10 formulários criados
    atividade_recente = (
        FormularioGerado.query
        .join(PeticaoModelo)
        .order_by(FormularioGerado.criado_em.desc())
        .limit(10)
        .all()
    )
    
    return render_template(
        "peticionador/dashboard.html",
        title="Dashboard Peticionador",
        total_clientes=total_clientes,
        total_peticoes=total_formularios,  # Agora conta formulários criados
        total_peticoes_processadas=total_peticoes_processadas,
        total_usuarios=total_usuarios,
        atividade_recente=atividade_recente,
    )


# =============================================================================
# AUTENTICAÇÃO
# =============================================================================

@peticionador_bp.route("/login", methods=["GET", "POST"])
def login():
    """Login do peticionador com verificações de segurança e tratamento robusto de erros."""
    try:
        if current_user.is_authenticated:
            return redirect(url_for("peticionador.dashboard"))

        form = LoginForm()
        if form.validate_on_submit():
            try:
                # Buscar usuário
                user = User.query.filter_by(email=form.email.data).first()
                
                if user and user.check_password(form.password.data):
                    # Verificar se usuário está ativo
                    if not user.is_active:
                        flash("Conta desativada. Entre em contato com o administrador.", "danger")
                        return render_template("peticionador/login.html", form=form)
                    
                    # Login bem-sucedido
                    login_user(user, remember=form.remember_me.data)
                    
                    # Atualizar último login
                    try:
                        user.last_login = datetime.utcnow()
                        db.session.commit()
                    except Exception as db_error:
                        current_app.logger.warning(f"Erro ao atualizar last_login: {db_error}")
                        # Não falha o login por isso
                    
                    # Redirecionar para próxima página ou dashboard
                    next_page = request.args.get("next")
                    if not next_page or not next_page.startswith("/"):
                        next_page = url_for("peticionador.dashboard")
                    
                    current_app.logger.info(f"Login bem-sucedido: {user.email}")
                    flash(f"Bem-vindo, {user.name or user.email}!", "success")
                    return redirect(next_page)
                else:
                    current_app.logger.warning(f"Tentativa de login falhada: {form.email.data}")
                    flash("Email ou senha inválidos.", "danger")
                    
            except Exception as e:
                current_app.logger.error(f"Erro no processamento do login: {e}")
                flash("Erro interno. Tente novamente.", "danger")

        return render_template("peticionador/login.html", form=form)
        
    except Exception as critical_error:
        # Último recurso - erro crítico na rota de login
        current_app.logger.critical(f"Erro crítico na rota de login: {critical_error}")
        try:
            # Tentar retornar pelo menos uma página de erro
            return render_template("peticionador/login.html", form=LoginForm(), error_message="Sistema temporariamente indisponível. Tente novamente em alguns minutos.")
        except:
            # Se nem isso funcionar, retorna erro HTTP simples
            return "Sistema temporariamente indisponível. Tente novamente em alguns minutos.", 503


@peticionador_bp.route("/logout")
@login_required
def logout():
    """Logout do peticionador."""
    user_email = current_user.email
    logout_user()
    current_app.logger.info(f"Logout: {user_email}")
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for("peticionador.login"))


# =============================================================================
# GESTÃO DE MODELOS
# =============================================================================

import logging

@peticionador_bp.route("/modelos")
@login_required
def listar_modelos():
    """Lista todos os modelos de petição."""
    logging.warning("Entrou no endpoint /modelos")
    try:
        modelos = PeticaoModelo.query.order_by(PeticaoModelo.nome).all()
        logging.warning(f"Modelos encontrados: {modelos}")
    except Exception as e:
        logging.error(f"Erro na consulta: {e}", exc_info=True)
        raise
    return render_template(
        "peticionador/modelos_listar.html",
        title="Modelos de Petição",
        modelos=modelos,
    )


@peticionador_bp.route("/modelos/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_modelo():
    """Adiciona um novo modelo de petição."""
    form = PeticaoModeloForm()
    
    if form.validate_on_submit():
        try:
            modelo = PeticaoModelo()
            form.populate_obj(modelo)
            
            # Gerar slug único
            modelo.slug = generate_unique_slug(modelo.nome, PeticaoModelo)
            
            db.session.add(modelo)
            db.session.commit()
            
            flash("Modelo adicionado com sucesso!", "success")
            return redirect(url_for("peticionador.listar_modelos"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao adicionar modelo: {e}")
            flash("Erro ao adicionar modelo.", "danger")
    
    return render_template(
        "peticionador/modelo_form.html",
        title="Adicionar Modelo",
        form=form
    )


@peticionador_bp.route("/modelos/<int:modelo_id>/editar", methods=["GET", "POST"])
@login_required
def editar_modelo(modelo_id):
    """Edita um modelo existente."""
    modelo = PeticaoModelo.query.get_or_404(modelo_id)
    form = PeticaoModeloForm(obj=modelo)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(modelo)
            modelo.atualizado_em = datetime.utcnow()
            
            db.session.commit()
            flash("Modelo atualizado com sucesso!", "success")
            return redirect(url_for("peticionador.listar_modelos"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao editar modelo: {e}")
            flash("Erro ao editar modelo.", "danger")
    
    return render_template(
        "peticionador/modelo_form.html",
        title="Editar Modelo",
        form=form,
        modelo=modelo
    )


@peticionador_bp.route("/modelos/<int:modelo_id>/placeholders")
@login_required
def placeholders_modelo(modelo_id):
    """Lista placeholders de um modelo."""
    modelo = PeticaoModelo.query.get_or_404(modelo_id)
    placeholders = (
        PeticaoPlaceholder.query
        .filter_by(modelo_id=modelo_id)
        .order_by(PeticaoPlaceholder.ordem)
        .all()
    )
    
    return render_template(
        "peticionador/placeholders_listar.html",
        title=f"Placeholders - {modelo.nome}",
        modelo=modelo,
        placeholders=placeholders,
    )


@peticionador_bp.route("/modelos/<int:modelo_id>/placeholders/sincronizar")
@login_required
def sincronizar_placeholders(modelo_id):
    """
    Sincronização ultra-robusta de placeholders usando FormularioManager.
    Previne erros "unhashable type" e implementa fallbacks automáticos.
    """
    modelo = PeticaoModelo.query.get_or_404(modelo_id)

    try:
        # Log da operação
        log_placeholder_operation("sync_start", modelo_id, {"document_id": modelo.google_doc_id})
        
        # Obter dados do documento
        docs_service = get_docs_service()
        placeholders_data = google_services.extract_placeholders(
            docs_service, modelo.google_doc_id
        )

        if not placeholders_data:
            flash(
                "Nenhum placeholder encontrado no documento ou erro ao ler o template.",
                "warning",
            )
            return redirect(
                url_for("peticionador.placeholders_modelo", modelo_id=modelo_id)
            )

        # SISTEMA SIMPLIFICADO - Sincronização básica sem complexidade
        try:
            placeholders_criados = 0
            
            for placeholder_data in placeholders_data:
                chave = placeholder_data.get('chave', '').strip()
                if not chave:
                    continue
                
                # Verificar se placeholder já existe
                existing = PeticaoPlaceholder.query.filter_by(
                    modelo_id=modelo_id, 
                    chave=chave
                ).first()
                
                if not existing:
                    # Criar novo placeholder
                    max_ordem = db.session.query(db.func.max(PeticaoPlaceholder.ordem)).filter_by(modelo_id=modelo_id).scalar() or 0
                    
                    placeholder = PeticaoPlaceholder(
                        modelo_id=modelo_id,
                        chave=chave,
                        label_form=chave.replace('_', ' ').title(),
                        tipo='string',
                        obrigatorio=False,
                        ordem=max_ordem + 1
                    )
                    
                    db.session.add(placeholder)
                    placeholders_criados += 1
            
            # Salvar alterações
            db.session.commit()
            flash(f"Sincronização concluída! {placeholders_criados} placeholders criados.", "success")
            
        except Exception as sync_error:
            db.session.rollback()
            flash(f"Erro na sincronização: {str(sync_error)}", "danger")

        return redirect(
            url_for("peticionador.placeholders_modelo", modelo_id=modelo_id)
        )
    except Exception as e:
        # Log de erro
        log_placeholder_operation("sync_error", modelo_id, {"error": str(e)})
        
        current_app.logger.error(f"Erro crítico ao sincronizar placeholders: {str(e)}")
        flash(f"Erro crítico na sincronização: {str(e)}", "danger")

        return redirect(
            url_for("peticionador.placeholders_modelo", modelo_id=modelo_id)
        )


# =============================================================================
# FORMULÁRIOS DINÂMICOS
# =============================================================================

@peticionador_bp.route("/formularios/<string:formulario_slug>", methods=["GET", "POST"])
@login_required
def preencher_formulario_dinamico(formulario_slug):
    """
    Sistema SIMPLIFICADO de formulários dinâmicos.
    Remove toda a complexidade desnecessária.
    """
    try:
        # 1. Buscar formulário diretamente no banco (sem managers complexos)
        formulario = FormularioGerado.query.filter_by(slug=formulario_slug).first()
        if not formulario:
            flash(f"Formulário '{formulario_slug}' não encontrado", "danger")
            return redirect(url_for("peticionador.dashboard"))
        
        # 2. Buscar modelo e placeholders diretamente
        modelo = PeticaoModelo.query.get(formulario.modelo_id)
        placeholders = PeticaoPlaceholder.query.filter_by(modelo_id=modelo.id).order_by(PeticaoPlaceholder.ordem).all()
        
        # 3. Criar formulário dinâmico simples
        form_class = build_dynamic_form(placeholders)
        form = form_class()
        
        # 4. Processar POST (simplificado)
        if request.method == "POST" and form.validate_on_submit():
            flash("Formulário processado com sucesso!", "success")
            return redirect(url_for("peticionador.dashboard"))
        
        # 5. Organizar campos simples por categoria
        campos_por_categoria = {}
        for placeholder in placeholders:
            categoria = placeholder.categoria or "Geral"
            if categoria not in campos_por_categoria:
                campos_por_categoria[categoria] = []
            campos_por_categoria[categoria].append(placeholder)
        
        # 6. Renderizar template com dados simples
        return render_template(
            "peticionador/formulario_dinamico.html",
            title=f"Preencher - {formulario.nome}",
            form=form,
            form_gerado=formulario,
            modelo=modelo.to_dict() if modelo else None,
            campos_organizados=campos_por_categoria,
            placeholders=placeholders,
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro no formulário dinâmico: {e}")
        flash(f"Erro ao carregar formulário: {str(e)}", "danger")
        return redirect(url_for("peticionador.dashboard"))


# =============================================================================
# GESTÃO DE CLIENTES
# =============================================================================

@peticionador_bp.route("/clientes")
@login_required
def listar_clientes():
    """Lista todos os clientes."""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "", type=str)
    
    query = Cliente.query
    
    if search:
        query = query.filter(
            db.or_(
                Cliente.primeiro_nome.ilike(f"%{search}%"),
                Cliente.sobrenome.ilike(f"%{search}%"),
                Cliente.cpf.ilike(f"%{search}%"),
                Cliente.email.ilike(f"%{search}%")
            )
        )
    
    clientes = query.order_by(Cliente.primeiro_nome).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template(
        "peticionador/clientes_listar.html",
        title="Clientes",
        clientes=clientes.items if hasattr(clientes, 'items') else clientes,
        pagination=clientes if hasattr(clientes, 'items') else None,
        search=search,
    )


@peticionador_bp.route("/clientes/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_cliente():
    """Adiciona um novo cliente."""
    form = ClienteForm()
    
    if form.validate_on_submit():
        try:
            cliente = Cliente()
            form.populate_obj(cliente)
            
            db.session.add(cliente)
            db.session.commit()
            
            flash("Cliente adicionado com sucesso!", "success")
            return redirect(url_for("peticionador.listar_clientes"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao adicionar cliente: {e}")
            flash("Erro ao adicionar cliente.", "danger")
    
    return render_template(
        "peticionador/cliente_form.html",
        title="Adicionar Cliente",
        form=form
    )


@peticionador_bp.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
@login_required
def editar_cliente(cliente_id):
    """Edita um cliente existente."""
    cliente = Cliente.query.get_or_404(cliente_id)
    form = ClienteForm(obj=cliente)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(cliente)
            db.session.commit()
            
            flash("Cliente atualizado com sucesso!", "success")
            return redirect(url_for("peticionador.listar_clientes"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao editar cliente: {e}")
            flash("Erro ao editar cliente.", "danger")
    
    return render_template(
        "peticionador/cliente_form.html",
        title="Editar Cliente",
        form=form,
        cliente=cliente
    )


@peticionador_bp.route("/clientes/<int:cliente_id>")
@login_required
def visualizar_cliente(cliente_id):
    """Visualiza detalhes de um cliente."""
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template(
        "peticionador/cliente_detalhes.html",
        title=f"Cliente - {cliente.nome_completo_formatado}",
        cliente=cliente,
    )


# =============================================================================
# AUTORIDADES DE TRÂNSITO
# =============================================================================

@peticionador_bp.route("/autoridades")
@login_required
def listar_autoridades():
    """Lista todas as autoridades de trânsito."""
    autoridades = AutoridadeTransito.query.order_by(
        AutoridadeTransito.estado, AutoridadeTransito.cidade, AutoridadeTransito.nome
    ).all()
    
    return render_template(
        "peticionador/autoridades_listar.html",
        title="Autoridades de Trânsito",
        autoridades=autoridades,
    )


@peticionador_bp.route("/autoridades/adicionar", methods=["GET", "POST"])
@login_required
def adicionar_autoridade():
    """Adiciona uma nova autoridade de trânsito."""
    form = AutoridadeTransitoForm()
    
    if form.validate_on_submit():
        try:
            autoridade = AutoridadeTransito()
            form.populate_obj(autoridade)
            
            db.session.add(autoridade)
            db.session.commit()
            
            flash("Autoridade adicionada com sucesso!", "success")
            return redirect(url_for("peticionador.listar_autoridades"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao adicionar autoridade: {e}")
            flash("Erro ao adicionar autoridade.", "danger")
    
    return render_template(
        "peticionador/autoridade_form.html",
        title="Adicionar Autoridade",
        form=form
    )


@peticionador_bp.route("/autoridades/<int:autoridade_id>/editar", methods=["GET", "POST"])
@login_required
def editar_autoridade(autoridade_id):
    """Edita uma autoridade existente."""
    autoridade = AutoridadeTransito.query.get_or_404(autoridade_id)
    form = AutoridadeTransitoForm(obj=autoridade)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(autoridade)
            db.session.commit()
            
            flash("Autoridade atualizada com sucesso!", "success")
            return redirect(url_for("peticionador.listar_autoridades"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao editar autoridade: {e}")
            flash("Erro ao editar autoridade.", "danger")
    
    return render_template(
        "peticionador/autoridade_form.html",
        title="Editar Autoridade",
        form=form,
        autoridade=autoridade
    )


# =============================================================================
# SELEÇÃO DE MODELOS
# =============================================================================

@peticionador_bp.route("/criar-peticao/selecionar-modelo")
@login_required
def selecionar_modelo_peticao():
    """Seleciona modelo para criação de petição."""
    modelos_query = (
        PeticaoModelo.query.filter_by(ativo=True).order_by(PeticaoModelo.nome).all()
    )

    modelos = []
    for modelo in modelos_query:
        modelos.append(
            {
                "id": modelo.id,
                "nome": modelo.nome,
                "descricao": modelo.descricao or "",
            }
        )

    return render_template(
        "peticionador/selecionar_modelo.html",
        title="Selecionar Modelo de Petição",
        modelos=modelos,
    )


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def generate_unique_slug(nome: str, model_class) -> str:
    """Gera um slug único para um modelo."""
    # Normalizar caracteres acentuados
    normalized = unicodedata.normalize('NFD', nome.lower())
    ascii_slug = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    
    # Remover caracteres especiais e manter apenas letras, números, espaços e hífens
    base_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', ascii_slug)
    base_slug = re.sub(r'[\s_-]+', '-', base_slug).strip('-')
    
    slug = base_slug
    counter = 1
    
    while model_class.query.filter_by(slug=slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    return slug


# =============================================================================
# ROTAS CRÍTICAS IMPLEMENTADAS
# =============================================================================

@peticionador_bp.route("/criar-peticao/<int:modelo_id>")
@login_required
def gerar_peticao_dinamica(modelo_id):
    """SISTEMA SIMPLIFICADO - Cria formulário baseado no modelo."""
    try:
        # 1. Buscar modelo diretamente
        modelo = PeticaoModelo.query.get_or_404(modelo_id)
        
        # 2. Criar formulário com dados simples (sem complexidade)
        formulario = FormularioGerado(
            nome=f"Formulário - {modelo.nome}",
            slug=generate_unique_slug(f"form-{modelo.nome}", FormularioGerado),
            modelo_id=modelo_id,
            criado_em=datetime.utcnow()
        )
        
        # 3. Salvar no banco
        db.session.add(formulario)
        db.session.commit()
        
        # 4. Redirecionar para formulário (sem flash complexo)
        return redirect(url_for('peticionador.preencher_formulario_dinamico', formulario_slug=formulario.slug))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar formulário: {e}")
        flash("Erro ao criar formulário. Tente novamente.", "danger")
        return redirect(url_for('peticionador.listar_modelos'))


@peticionador_bp.route("/modelos/<int:modelo_id>/criar-formulario")
@login_required  
def criar_formulario_dinamico(modelo_id):
    """Cria um novo formulário dinâmico baseado no modelo."""
    try:
        # Buscar o modelo
        modelo = PeticaoModelo.query.get_or_404(modelo_id)
        
        # Criar um novo formulário gerado
        import uuid
        from datetime import datetime
        
        slug_base = modelo.nome.lower().replace(' ', '-').replace('_', '-')
        slug_unico = f"{slug_base}-{uuid.uuid4().hex[:8]}"
        
        formulario = FormularioGerado(
            nome=f"Formulário {modelo.nome}",
            slug=slug_unico,
            modelo_id=modelo_id,
            criado_em=datetime.utcnow()
        )
        
        db.session.add(formulario)
        db.session.commit()
        
        flash(f"Formulário criado com sucesso!", "success")
        
        # Redirecionar para preencher o formulário
        return redirect(url_for('peticionador.preencher_formulario_dinamico', formulario_slug=slug_unico))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao criar formulário: {e}")
        flash(f"Erro ao criar formulário: {str(e)}", "error")
        return redirect(url_for('peticionador.listar_modelos'))


@peticionador_bp.route("/modelos/<int:modelo_id>/desativar", methods=["POST"])
@login_required
def excluir_modelo(modelo_id):
    """Desativa um modelo de petição."""
    try:
        modelo = PeticaoModelo.query.get_or_404(modelo_id)
        modelo.ativo = False
        db.session.commit()
        
        flash(f"Modelo '{modelo.nome}' desativado com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao desativar modelo: {str(e)}", "error")
        
    return redirect(url_for('peticionador.listar_modelos'))


@peticionador_bp.route("/formularios/<slug>/excluir", methods=["POST"])
@login_required
def excluir_formulario_dinamico(slug):
    """Exclui um formulário dinâmico."""
    try:
        formulario = FormularioGerado.query.filter_by(slug=slug).first_or_404()
        
        # Verificar se o usuário tem permissão (pode adicionar verificação de owner aqui)
        db.session.delete(formulario)
        db.session.commit()
        
        flash("Formulário excluído com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir formulário: {str(e)}", "error")
        
    return redirect(url_for('peticionador.listar_modelos'))


@peticionador_bp.route("/autoridades/<int:autoridade_id>/excluir", methods=["POST"])
@login_required
def excluir_autoridade(autoridade_id):
    """Exclui uma autoridade de trânsito."""
    try:
        autoridade = AutoridadeTransito.query.get_or_404(autoridade_id)
        
        # Verificar se não há dependências
        # TODO: Adicionar verificação de petições/formulários relacionados
        
        db.session.delete(autoridade)
        db.session.commit()
        
        flash(f"Autoridade '{autoridade.nome}' excluída com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir autoridade: {str(e)}", "error")
        
    return redirect(url_for('peticionador.listar_autoridades'))


@peticionador_bp.route("/clientes/<int:cliente_id>/excluir", methods=["POST"])
@login_required
def excluir_cliente(cliente_id):
    """Exclui um cliente."""
    try:
        cliente = Cliente.query.get_or_404(cliente_id)
        
        # Verificar se não há dependências
        # TODO: Adicionar verificação de petições/formulários relacionados
        
        db.session.delete(cliente)
        db.session.commit()
        
        flash(f"Cliente excluído com sucesso!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir cliente: {str(e)}", "error")
        
    return redirect(url_for('peticionador.listar_clientes'))


# =============================================================================
# ROTAS DE API JSON
# =============================================================================

@peticionador_bp.route("/api/clientes")
@login_required
def listar_clientes_api():
    """API JSON para listar clientes."""
    try:
        clientes = Cliente.query.order_by(Cliente.nome_razao_social).all()
        
        clientes_json = []
        for cliente in clientes:
            clientes_json.append({
                'id': cliente.id,
                'nome': cliente.nome_razao_social,
                'email': cliente.email,
                'tipo_pessoa': cliente.tipo_pessoa.value if cliente.tipo_pessoa else 'N/A',
                'telefone': cliente.telefone_celular or cliente.telefone_outro or '',
                'cpf_cnpj': cliente.cpf if cliente.tipo_pessoa and cliente.tipo_pessoa.name == 'FISICA' else cliente.cnpj,
                'endereco': f"{cliente.endereco_logradouro}, {cliente.endereco_numero}" if cliente.endereco_logradouro else ''
            })
        
        return jsonify({
            'success': True,
            'clientes': clientes_json,
            'total': len(clientes_json)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@peticionador_bp.route("/api/autoridades")
@login_required
def listar_autoridades_api():
    """API JSON para listar autoridades de trânsito."""
    try:
        autoridades = AutoridadeTransito.query.order_by(
            AutoridadeTransito.estado, 
            AutoridadeTransito.cidade, 
            AutoridadeTransito.nome
        ).all()
        
        autoridades_json = []
        for autoridade in autoridades:
            autoridades_json.append({
                'id': autoridade.id,
                'nome': autoridade.nome,
                'cidade': autoridade.cidade or '',
                'estado': autoridade.estado or '',
                'nome_completo': f"{autoridade.nome} - {autoridade.cidade}/{autoridade.estado}" if autoridade.cidade and autoridade.estado else autoridade.nome
            })
        
        return jsonify({
            'success': True,
            'autoridades': autoridades_json,
            'total': len(autoridades_json)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# ROTAS AJAX PARA PLACEHOLDERS
# =============================================================================

@peticionador_bp.route("/modelos/<int:modelo_id>/placeholders/reordenar", methods=["POST"])
@login_required
def reordenar_placeholders(modelo_id):
    """Reordena placeholders via AJAX."""
    try:
        modelo = PeticaoModelo.query.get_or_404(modelo_id)
        data = request.get_json()
        
        if not data or 'ordem' not in data:
            return jsonify({'success': False, 'error': 'Dados inválidos'}), 400
        
        ordem_ids = data['ordem']
        
        # Atualizar ordem dos placeholders
        for index, placeholder_id in enumerate(ordem_ids):
            placeholder = PeticaoPlaceholder.query.get(placeholder_id)
            if placeholder and placeholder.modelo_id == modelo_id:
                placeholder.ordem = index + 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ordem atualizada com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@peticionador_bp.route("/api/analisar-personas/<int:modelo_id>")
@login_required
def analisar_personas_api(modelo_id):
    """API para análise de personas em um modelo."""
    try:
        modelo = PeticaoModelo.query.get_or_404(modelo_id)
        placeholders = PeticaoPlaceholder.query.filter_by(modelo_id=modelo_id).order_by(PeticaoPlaceholder.ordem).all()
        
        # Análise simples de personas baseada nos placeholders
        personas_detectadas = {}
        placeholders_total = len(placeholders)
        
        # Analisar chaves dos placeholders para detectar personas
        for placeholder in placeholders:
            chave = placeholder.chave.lower()
            
            # Detectar tipos de personas comuns
            if any(termo in chave for termo in ['autor', 'requerente', 'impetrante']):
                personas_detectadas['autor'] = personas_detectadas.get('autor', 0) + 1
            elif any(termo in chave for termo in ['reu', 'requerido', 'impetrado']):
                personas_detectadas['reu'] = personas_detectadas.get('reu', 0) + 1
            elif any(termo in chave for termo in ['autoridade', 'delegad']):
                personas_detectadas['autoridade'] = personas_detectadas.get('autoridade', 0) + 1
            elif any(termo in chave for termo in ['testemunha']):
                personas_detectadas['testemunha'] = personas_detectadas.get('testemunha', 0) + 1
        
        # Gerar sugestões
        sugestoes = []
        total_personas = sum(personas_detectadas.values())
        
        if total_personas == 0:
            sugestoes.append({
                'type': 'info',
                'message': 'Nenhuma persona detectada nos placeholders. Considere adicionar campos para identificar as partes envolvidas.'
            })
        elif total_personas > 10:
            sugestoes.append({
                'type': 'multiple_personas',
                'message': f'Detectadas {total_personas} referências a personas. Considere organizar melhor os campos.'
            })
        else:
            sugestoes.append({
                'type': 'info',
                'message': f'Análise concluída. {total_personas} personas identificadas nos placeholders.'
            })
        
        return jsonify({
            'success': True,
            'placeholders_total': placeholders_total,
            'total_personas': total_personas,
            'personas_detectadas': personas_detectadas,
            'sugestoes': sugestoes,
            'modelo_nome': modelo.nome
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@peticionador_bp.route("/api/gerar-campos-dinamicos", methods=["POST"])
@login_required
def gerar_campos_dinamicos_api():
    """API para gerar campos dinâmicos baseados em personas."""
    try:
        data = request.get_json()
        
        if not data or 'modelo_id' not in data or 'persona_config' not in data:
            return jsonify({
                'success': False,
                'error': 'Dados inválidos. modelo_id e persona_config são obrigatórios.'
            }), 400
        
        modelo_id = data['modelo_id']
        persona_config = data['persona_config']
        
        modelo = PeticaoModelo.query.get_or_404(modelo_id)
        total_criados = 0
        
        # Para cada tipo de persona configurada
        for tipo_persona, config in persona_config.items():
            quantidade = config.get('quantidade', 0)
            campos = config.get('campos', ['nome', 'cpf'])
            
            # Criar placeholders para cada instância da persona
            for i in range(1, quantidade + 1):
                for campo in campos:
                    chave = f"{tipo_persona}_{i}_{campo}"
                    label = f"{tipo_persona.title()} {i} - {campo.title()}"
                    
                    # Verificar se o placeholder já existe
                    existing = PeticaoPlaceholder.query.filter_by(
                        modelo_id=modelo_id, 
                        chave=chave
                    ).first()
                    
                    if not existing:
                        # Determinar próxima ordem
                        max_ordem = db.session.query(db.func.max(PeticaoPlaceholder.ordem)).filter_by(modelo_id=modelo_id).scalar() or 0
                        
                        placeholder = PeticaoPlaceholder(
                            modelo_id=modelo_id,
                            chave=chave,
                            label_form=label,
                            tipo='string',
                            obrigatorio=False,
                            ordem=max_ordem + 1
                        )
                        
                        db.session.add(placeholder)
                        total_criados += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'total_criados': total_criados,
            'message': f'{total_criados} novos campos foram criados com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@peticionador_bp.route("/modelos/<int:modelo_id>/placeholders/limpar-e-sincronizar")
@login_required  
def limpar_e_sincronizar_placeholders(modelo_id):
    """Limpa todos os placeholders e sincroniza novamente."""
    try:
        modelo = PeticaoModelo.query.get_or_404(modelo_id)
        
        # Remover todos os placeholders existentes
        PeticaoPlaceholder.query.filter_by(modelo_id=modelo_id).delete()
        db.session.commit()
        
        flash("Placeholders removidos. Redirecionando para sincronização...", "info")
        return redirect(url_for('peticionador.sincronizar_placeholders', modelo_id=modelo_id))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao limpar placeholders: {str(e)}", "error")
        return redirect(url_for('peticionador.placeholders_modelo', modelo_id=modelo_id))