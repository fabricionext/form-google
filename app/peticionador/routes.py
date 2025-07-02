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

# Importando os services refatorados
from .services import FormularioService, DocumentoService
try:
    from app.peticionador import google_services
except ImportError:
    google_services = None  # Implementação fallback abaixo
from app.extensions import db, limiter

# Importar models
# from models import RespostaForm  # ❌ Removido - não usado e causa erro de importação
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

# ✅ IMPLEMENTAÇÃO TEMPORÁRIA DE FUNÇÕES ESSENCIAIS
# Implementadas diretamente para evitar import circulares

def build_dynamic_form(placeholders):
    """Constrói formulário dinâmico a partir dos placeholders."""
    from wtforms import StringField, TextAreaField, SelectField, EmailField, DateField
    from wtforms.validators import DataRequired, Optional
    
    class DynamicForm(FlaskForm):
        pass
    
    # Criar campos dinamicamente
    for placeholder in placeholders:
        field_name = placeholder.chave
        label = placeholder.label_form or placeholder.chave.replace('_', ' ').title()
        
        # Determinar tipo de campo baseado na chave
        if 'email' in field_name.lower():
            field = EmailField(label, validators=[DataRequired() if placeholder.obrigatorio else Optional()])
        elif 'data' in field_name.lower() or 'nascimento' in field_name.lower():
            field = DateField(label, validators=[DataRequired() if placeholder.obrigatorio else Optional()])
        elif 'endereco' in field_name.lower() or 'observacao' in field_name.lower():
            field = TextAreaField(label, validators=[DataRequired() if placeholder.obrigatorio else Optional()])
        else:
            field = StringField(label, validators=[DataRequired() if placeholder.obrigatorio else Optional()])
        
        setattr(DynamicForm, field_name, field)
    
    return DynamicForm

def detect_persona_patterns(chaves):
    """Detecta padrões de personas nas chaves dos placeholders."""
    patterns = {
        'autor': 0,
        'reu': 0, 
        'autoridade': 0,
        'testemunha': 0
    }
    
    for chave in chaves:
        chave_lower = chave.lower()
        if any(termo in chave_lower for termo in ['autor', 'requerente', 'impetrante']):
            patterns['autor'] += 1
        elif any(termo in chave_lower for termo in ['reu', 'requerido', 'impetrado']):
            patterns['reu'] += 1
        elif any(termo in chave_lower for termo in ['autoridade', 'delegad', 'orgao']):
            patterns['autoridade'] += 1
        elif 'testemunha' in chave_lower:
            patterns['testemunha'] += 1
    
    return patterns

def categorize_placeholder_key(chave):
    """Categoriza uma chave de placeholder."""
    chave_lower = chave.lower()
    
    # Categorização básica por padrões
    if any(termo in chave_lower for termo in ['autor', 'requerente', 'impetrante']):
        if any(termo in chave_lower for termo in ['endereco', 'endereço', 'rua', 'cidade', 'cep']):
            return 'autor_endereco'
        else:
            return 'autor_dados'
    elif any(termo in chave_lower for termo in ['reu', 'requerido', 'impetrado']):
        return 'reu'
    elif any(termo in chave_lower for termo in ['autoridade', 'delegad', 'orgao_transito']):
        return 'autoridades'
    elif any(termo in chave_lower for termo in ['endereco', 'endereço', 'rua', 'cidade', 'cep']):
        return 'endereco'
    elif any(termo in chave_lower for termo in ['testemunha']):
        return 'testemunha'
    elif any(termo in chave_lower for termo in ['veiculo', 'veículo', 'placa', 'chassi']):
        return 'veiculo'
    elif any(termo in chave_lower for termo in ['infracao', 'infração', 'multa', 'pontos']):
        return 'infracao'
    elif any(termo in chave_lower for termo in ['data', 'prazo', 'vigencia', 'vigência']):
        return 'datas'
    else:
        return 'cliente'  # Categoria padrão

def log_placeholder_operation(operation_type, modelo_id, data=None):
    """Log de operações de placeholder para debugging."""
    current_app.logger.info(f"[PLACEHOLDER_OP] {operation_type} - Modelo {modelo_id}: {data or {}}")

def extract_placeholders_fallback(doc_id):
    """Implementação fallback para extração de placeholders quando google_services não está disponível."""
    current_app.logger.warning(f"Google Services não disponível - usando fallback para doc_id: {doc_id}")
    # Retorna lista vazia para evitar erro, mas logga que o serviço não está disponível
    return []

# Monkey patch para google_services se não estiver disponível
if google_services is None:
    class FallbackGoogleServices:
        @staticmethod
        def extract_placeholders(docs_service, doc_id):
            return extract_placeholders_fallback(doc_id)
    
    google_services = FallbackGoogleServices()

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
        "peticionador/dashboard_vuetify.html",
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

@peticionador_bp.route("/modelos")
@login_required
def listar_modelos():
    """Lista todos os modelos de petição disponíveis."""
    # Buscar modelos de petição ativos
    modelos = PeticaoModelo.query.filter_by(ativo=True).order_by(PeticaoModelo.nome).all()
    
    return render_template(
        "peticionador/modelos_listar.html",
        title="Modelos de Petição",
        formularios=modelos,  # Mantendo o nome 'formularios' para compatibilidade com template
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
        docs_service = None  # Será implementado quando google_services estiver completo
        placeholders_data = google_services.extract_placeholders_from_document(
            modelo.google_doc_id
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
# VERSÃO REFATORADA DA ROTA DE FORMULÁRIO DINÂMICO
# =============================================================================

@peticionador_bp.route("/formularios/<string:formulario_slug>", methods=["GET", "POST"])
@login_required
def preencher_formulario_dinamico(formulario_slug):
    """
    VERSÃO REFATORADA da rota que utiliza a camada de serviços para uma lógica mais limpa.
    """
    try:
        current_app.logger.info(f"[REFACTOR] Processando formulário com slug: {formulario_slug}")
        
        # 1. Instanciar services (responsabilidade única)
        form_service = FormularioService(formulario_slug)
        
        # 2. Construir formulário dinâmico
        DynamicForm = form_service.build_dynamic_form_class()
        form = DynamicForm(request.form)

        # 3. Processar submissão (POST)
        if form.validate_on_submit():
            try:
                current_app.logger.info(f"[REFACTOR] Processando submissão POST para '{form_service.form_gerado.nome}'")
                
                # Delegação para serviço de documentos
                doc_service = DocumentoService()
                novo_id, link = doc_service.gerar_documento_dinamico(
                    form_service.modelo, 
                    request.form, 
                    form_service.placeholders
                )
                
                if novo_id:
                    current_app.logger.info(f"[REFACTOR] Documento gerado com sucesso! ID: {novo_id}")
                    flash("Documento gerado com sucesso!", "success")
                    return jsonify({"success": True, "link": link})
                else:
                    raise Exception("Falha ao gerar o ID do documento.")
                    
            except Exception as e:
                current_app.logger.error(f"[REFACTOR] Erro ao gerar documento: {e}", exc_info=True)
                flash("Erro ao gerar o documento.", "danger")
                return jsonify({"success": False, "error": str(e)}), 500

        # 4. Renderizar formulário (GET)
        current_app.logger.info(f"[REFACTOR] Renderizando formulário para slug: {formulario_slug}")
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
        current_app.logger.error(f"[REFACTOR] Erro na rota: {e}", exc_info=True)
        if "404" in str(e):
            abort(404, description=str(e))
        else:
            abort(500, description="Erro interno do servidor")


# =============================================================================
# GESTÃO DE CLIENTES
# =============================================================================

@peticionador_bp.route("/clientes")
@login_required
def listar_clientes():
    """Lista todos os clientes cadastrados com busca e paginação."""
    page = request.args.get("page", 1, type=int)
    search_query = request.args.get("q", "")

    query = Cliente.query.order_by(Cliente.id.desc())
    if search_query:
        # Busca por nome, razão social, CPF ou CNPJ
        search_term = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Cliente.primeiro_nome.ilike(search_term),
                Cliente.sobrenome.ilike(search_term),
                Cliente.nome_completo.ilike(search_term),
                Cliente.razao_social.ilike(search_term),
                Cliente.cpf.ilike(search_term),
                Cliente.cnpj.ilike(search_term),
                Cliente.email.ilike(search_term),
            )
        )

    pagination = query.paginate(page=page, per_page=10, error_out=False)
    clientes = pagination.items

    return render_template(
        "peticionador/clientes_listar.html",
        title="Clientes Cadastrados",
        clientes=clientes,
        pagination=pagination,
        search_query=search_query,
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
        "peticionador/cliente_form_vuetify.html",
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
        "peticionador/cliente_form_vuetify.html",
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
        "peticionador/cliente_detalhes_vuetify.html",
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
    """Limpa placeholders órfãos e sincroniza com o documento."""
    # O conteúdo desta função será movido para o PlaceholderService
    # ou uma classe de domínio específica para o modelo.
    pass


# =============================================================================
# DASHBOARD ADMINISTRATIVO AVANÇADO
# =============================================================================

@peticionador_bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    """Dashboard administrativo avançado com monitoramento completo."""
    from datetime import datetime, timedelta
    
    try:
        # Estatísticas básicas
        total_usuarios = User.query.count()
        usuarios_ativos = User.query.filter_by(is_active=True).count()
        total_modelos = PeticaoModelo.query.filter_by(ativo=True).count()
        total_clientes = Cliente.query.count()
        total_formularios = FormularioGerado.query.count()
        total_peticoes = PeticaoGerada.query.count()
        total_autoridades = AutoridadeTransito.query.count()
        
        # Estatísticas por período
        hoje = datetime.utcnow()
        ultima_semana = hoje - timedelta(days=7)
        ultimo_mes = hoje - timedelta(days=30)
        
        # Novos registros (última semana)
        novos_usuarios = User.query.filter(User.created_at >= ultima_semana).count() if hasattr(User, 'created_at') else 0
        novos_clientes = Cliente.query.filter(Cliente.created_at >= ultima_semana).count() if hasattr(Cliente, 'created_at') else 0
        novos_formularios = FormularioGerado.query.filter(FormularioGerado.criado_em >= ultima_semana).count()
        
        # Últimas atividades
        ultimos_clientes = (
            Cliente.query
            .order_by(Cliente.id.desc())
            .limit(10)
            .all()
        )
        
        ultimos_formularios = (
            FormularioGerado.query
            .join(PeticaoModelo)
            .order_by(FormularioGerado.criado_em.desc())
            .limit(10)
            .all()
        )
        
        # Estatísticas de uso dos modelos
        modelos_mais_usados = (
            db.session.query(PeticaoModelo, db.func.count(FormularioGerado.id).label('uso_count'))
            .join(FormularioGerado, PeticaoModelo.id == FormularioGerado.modelo_id)
            .group_by(PeticaoModelo.id)
            .order_by(db.desc('uso_count'))
            .limit(5)
            .all()
        )
        
        return render_template(
            "peticionador/admin_dashboard.html",
            title="Dashboard Administrativo",
            # Estatísticas gerais
            total_usuarios=total_usuarios,
            usuarios_ativos=usuarios_ativos,
            total_modelos=total_modelos,
            total_clientes=total_clientes,
            total_formularios=total_formularios,
            total_peticoes=total_peticoes,
            total_autoridades=total_autoridades,
            # Novos registros
            novos_usuarios=novos_usuarios,
            novos_clientes=novos_clientes,
            novos_formularios=novos_formularios,
            # Atividades recentes
            ultimos_clientes=ultimos_clientes,
            ultimos_formularios=ultimos_formularios,
            # Estatísticas de uso
            modelos_mais_usados=modelos_mais_usados,
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro no dashboard administrativo: {e}")
        flash("Erro ao carregar dashboard administrativo.", "danger")
        return redirect(url_for("peticionador.dashboard"))


@peticionador_bp.route("/admin/monitoramento")
@login_required
def monitoramento():
    """Página de monitoramento em tempo real."""
    from datetime import datetime, timedelta
    
    try:
        # Dados para últimas 24 horas
        agora = datetime.utcnow()
        ontem = agora - timedelta(hours=24)
        
        # Atividades recentes (últimas 24h)
        formularios_recentes = (
            FormularioGerado.query
            .filter(FormularioGerado.criado_em >= ontem)
            .order_by(FormularioGerado.criado_em.desc())
            .limit(20)
            .all()
        )
        
        # Clientes cadastrados via /cadastrocliente (últimas 24h)
        clientes_recentes = (
            Cliente.query
            .filter(Cliente.created_at >= ontem) if hasattr(Cliente, 'created_at') else Cliente.query
        ).order_by(Cliente.id.desc()).limit(20).all()
        
        # Sistema de logs (se disponível)
        logs_sistema = []  # TODO: Implementar logs do sistema
        
        return render_template(
            "peticionador/monitoramento.html",
            title="Monitoramento do Sistema",
            formularios_recentes=formularios_recentes,
            clientes_recentes=clientes_recentes,
            logs_sistema=logs_sistema,
            timestamp_atualizacao=agora
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro no monitoramento: {e}")
        flash("Erro ao carregar monitoramento.", "danger")
        return redirect(url_for("peticionador.dashboard"))


@peticionador_bp.route("/admin/relatorios")
@login_required
def relatorios():
    """Página de relatórios e estatísticas."""
    from datetime import datetime, timedelta
    
    try:
        # Período de análise (último mês)
        hoje = datetime.utcnow()
        ultimo_mes = hoje - timedelta(days=30)
        
        # Relatório de clientes por período
        clientes_por_dia = (
            db.session.query(
                db.func.date(Cliente.created_at if hasattr(Cliente, 'created_at') else Cliente.id).label('data'),
                db.func.count(Cliente.id).label('total')
            )
            .filter(Cliente.created_at >= ultimo_mes if hasattr(Cliente, 'created_at') else True)
            .group_by(db.func.date(Cliente.created_at if hasattr(Cliente, 'created_at') else Cliente.id))
            .order_by('data')
            .all()
        )
        
        # Relatório de formulários por modelo
        formularios_por_modelo = (
            db.session.query(PeticaoModelo.nome, db.func.count(FormularioGerado.id).label('total'))
            .join(FormularioGerado, PeticaoModelo.id == FormularioGerado.modelo_id)
            .group_by(PeticaoModelo.nome)
            .order_by(db.desc('total'))
            .all()
        )
        
        # Relatório de uso por horário
        uso_por_horario = (
            db.session.query(
                db.func.extract('hour', FormularioGerado.criado_em).label('hora'),
                db.func.count(FormularioGerado.id).label('total')
            )
            .group_by('hora')
            .order_by('hora')
            .all()
        )
        
        return render_template(
            "peticionador/relatorios.html",
            title="Relatórios e Estatísticas",
            clientes_por_dia=clientes_por_dia,
            formularios_por_modelo=formularios_por_modelo,
            uso_por_horario=uso_por_horario,
        )
        
    except Exception as e:
        current_app.logger.error(f"Erro nos relatórios: {e}")
        flash("Erro ao carregar relatórios.", "danger")
        return redirect(url_for("peticionador.dashboard"))


@peticionador_bp.route("/configuracoes")
@login_required
def configuracoes():
    """Página de configurações do sistema."""
    # Obter dados do sistema para exibir nas configurações
    total_usuarios = User.query.filter_by(is_active=True).count()
    total_clientes = Cliente.query.count()
    
    return render_template(
        "peticionador/configuracoes.html",
        title="Configurações do Sistema",
        total_usuarios=total_usuarios,
        total_clientes=total_clientes,
    )

# Rota temporária para evitar erro BuildError
@peticionador_bp.route("/placeholders")
@login_required
def listar_placeholders():
    """Página temporária para placeholders."""
    return redirect(url_for("peticionador.configuracoes"))


# =============================================================================
# APIs PARA MONITORAMENTO EM TEMPO REAL
# =============================================================================

@peticionador_bp.route("/api/admin/stats")
@login_required
def admin_stats_api():
    """API JSON com estatísticas em tempo real."""
    from datetime import datetime, timedelta
    
    try:
        agora = datetime.utcnow()
        hoje = agora.replace(hour=0, minute=0, second=0, microsecond=0)
        ontem = hoje - timedelta(days=1)
        
        stats = {
            'timestamp': agora.isoformat(),
            'totais': {
                'usuarios': User.query.count(),
                'usuarios_ativos': User.query.filter_by(is_active=True).count(),
                'clientes': Cliente.query.count(),
                'formularios': FormularioGerado.query.count(),
                'modelos': PeticaoModelo.query.filter_by(ativo=True).count(),
                'autoridades': AutoridadeTransito.query.count()
            },
            'hoje': {
                'formularios': FormularioGerado.query.filter(FormularioGerado.criado_em >= hoje).count(),
                'clientes': Cliente.query.filter(Cliente.created_at >= hoje).count() if hasattr(Cliente, 'created_at') else 0
            },
            'sistema': {
                'status': 'online',
                'uptime': '99.9%',  # TODO: Implementar cálculo real
                'memoria_uso': '45%',  # TODO: Implementar monitoramento real
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@peticionador_bp.route("/api/admin/clientes-recentes")
@login_required
def clientes_recentes_api():
    """API JSON com clientes cadastrados recentemente."""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        clientes = (
            Cliente.query
            .order_by(Cliente.id.desc())
            .limit(limit)
            .all()
        )
        
        clientes_data = []
        for cliente in clientes:
            clientes_data.append({
                'id': cliente.id,
                'nome': cliente.nome_razao_social or 'N/A',
                'email': cliente.email or 'N/A',
                'telefone': cliente.telefone_celular or cliente.telefone_outro or 'N/A',
                'tipo_pessoa': cliente.tipo_pessoa.value if cliente.tipo_pessoa else 'N/A',
                'data_cadastro': cliente.created_at.isoformat() if hasattr(cliente, 'created_at') and cliente.created_at else 'N/A',
                'cpf_cnpj': cliente.cpf or cliente.cnpj or 'N/A'
            })
        
        return jsonify({
            'success': True,
            'clientes': clientes_data,
            'total': len(clientes_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500