import datetime
import re
import traceback

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
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired

from app.peticionador import google_services
from app.peticionador.utils import get_enum_display_name
from config import CONFIG

# Ajuste o import de 'db' conforme a estrutura do seu projeto.
# from app import db
from models import RespostaForm  # Importa RespostaForm da raiz
from models import db  # Utiliza o db do models.py na raiz do projeto

from . import peticionador_bp
from .forms import (
    AutoridadeTransitoForm,
    ClienteForm,
    GerarDocumentoSuspensaoForm,
    LoginForm,
)
from .models import (  # Cliente removido daqui
    AutoridadeTransito,
    Cliente,
    PeticaoGerada,
    PeticaoModelo,
    PeticaoPlaceholder,
    TipoPessoaEnum,
    User,
)


@peticionador_bp.route("/")
@login_required
def index():
    """Dashboard com indicadores rápidos."""
    total_clientes = Cliente.query.count()
    total_peticoes = PeticaoGerada.query.count()
    total_usuarios = User.query.filter_by(is_active=True).count()
    return render_template(
        "peticionador/dashboard.html",
        title="Dashboard Peticionador",
        total_clientes=total_clientes,
        total_peticoes=total_peticoes,
        total_usuarios=total_usuarios,
    )


@peticionador_bp.route("/criar-peticao/selecionar-modelo")
@login_required
def selecionar_modelo_peticao():
    # No futuro, podemos buscar os modelos de um banco de dados ou configuração
    modelos = [
        {
            "id": "suspensao_direito_dirigir",
            "nome": "Defesa de Suspensão do Direito de Dirigir",
        }
        # Adicionar outros modelos aqui
    ]
    return render_template(
        "peticionador/selecionar_modelo.html",
        title="Selecionar Modelo de Petição",
        modelos=modelos,
    )


@peticionador_bp.route(
    "/criar-peticao/suspensao-direito-dirigir/dados", methods=["GET", "POST"]
)
@login_required
def gerar_suspensao_peticao_dados_form():
    form = GerarDocumentoSuspensaoForm(
        request.form if request.method == "POST" else None
    )
    cliente_encontrado = None

    if request.method == "GET" and "cpf_buscado" in request.args:
        cpf_para_buscar = request.args.get("cpf_buscado")
        if cpf_para_buscar:
            cliente_encontrado = RespostaForm.query.filter_by(
                cpf=cpf_para_buscar
            ).first()
            if cliente_encontrado:
                form.cliente_id.data = cliente_encontrado.id
                form.cliente_primeiro_nome.data = cliente_encontrado.primeiro_nome
                form.cliente_sobrenome.data = cliente_encontrado.sobrenome
                form.cliente_email.data = cliente_encontrado.email
                form.cliente_telefone_celular.data = cliente_encontrado.telefone_celular
                form.cliente_endereco_logradouro.data = (
                    cliente_encontrado.endereco_logradouro
                )
                form.cliente_endereco_numero.data = cliente_encontrado.endereco_numero
                form.cliente_endereco_complemento.data = (
                    cliente_encontrado.endereco_complemento
                )
                form.cliente_endereco_bairro.data = cliente_encontrado.endereco_bairro
                form.cliente_endereco_cidade.data = cliente_encontrado.endereco_cidade
                form.cliente_endereco_estado.data = cliente_encontrado.endereco_estado
                form.cliente_endereco_cep.data = cliente_encontrado.endereco_cep
                form.cliente_cpf.data = cliente_encontrado.cpf
                form.cliente_rg_numero.data = cliente_encontrado.rg_numero
                form.cliente_cnh_numero.data = cliente_encontrado.cnh_numero
                # Adicionar outros campos conforme necessário
                flash("Cliente encontrado e dados carregados no formulário.", "info")
            else:
                flash(
                    f"Nenhum cliente encontrado com o CPF {cpf_para_buscar}. "
                    f"Você pode preencher os dados para um novo cliente se desejar "
                    f"(funcionalidade futura) ou tentar outro CPF.",
                    "warning",
                )
                form.cpf_busca.data = cpf_para_buscar  # Mantém o CPF buscado no campo

    if request.method == "POST":
        action = request.form.get("action")

        if action == "buscar_cliente_cpf":
            # Validação do campo cpf_busca já é feita pelo WTForms ao instanciar com request.form
            # Mas podemos verificar se o campo foi preenchido antes de redirecionar
            if form.cpf_busca.data and form.cpf_busca.validate(form):
                return redirect(
                    url_for(
                        ".gerar_suspensao_peticao_dados_form",
                        cpf_buscado=form.cpf_busca.data,
                    )
                )
            else:
                # Se o CPF de busca for inválido ou vazio, exibe o erro no campo e recarrega
                flash("CPF para busca inválido ou não fornecido.", "warning")
                # Não precisa fazer nada aqui, o template será renderizado no final da função com os erros do form.cpf_busca

        elif action == "gerar_documento_final":
            if form.validate_on_submit():
                cliente_id = form.cliente_id.data
                cliente_para_documento = None

                if cliente_id:
                    cliente_para_documento = Cliente.query.get(cliente_id)
                    if cliente_para_documento:
                        # Atualizar dados do cliente com base no formulário
                        cliente_para_documento.primeiro_nome = (
                            form.cliente_primeiro_nome.data
                        )
                        cliente_para_documento.sobrenome = form.cliente_sobrenome.data
                        cliente_para_documento.email = form.cliente_email.data
                        cliente_para_documento.telefone_celular = (
                            form.cliente_telefone_celular.data
                        )
                        cliente_para_documento.endereco_logradouro = (
                            form.cliente_endereco_logradouro.data
                        )
                        cliente_para_documento.endereco_numero = (
                            form.cliente_endereco_numero.data
                        )
                        cliente_para_documento.endereco_complemento = (
                            form.cliente_endereco_complemento.data
                        )
                        cliente_para_documento.endereco_bairro = (
                            form.cliente_endereco_bairro.data
                        )
                        cliente_para_documento.endereco_cidade = (
                            form.cliente_endereco_cidade.data
                        )
                        cliente_para_documento.endereco_estado = (
                            form.cliente_endereco_estado.data
                        )
                        cliente_para_documento.endereco_cep = (
                            form.cliente_endereco_cep.data
                        )
                        cliente_para_documento.cpf = (
                            form.cliente_cpf.data
                        )  # Permitir edição do CPF
                        cliente_para_documento.rg_numero = form.cliente_rg_numero.data
                        cliente_para_documento.cnh_numero = form.cliente_cnh_numero.data
                        # Adicionar outros campos conforme necessário
                        try:
                            db.session.commit()
                            flash(
                                "Dados do cliente atualizados com sucesso.", "success"
                            )
                        except Exception as e:
                            db.session.rollback()
                            current_app.logger.error(f"Erro ao atualizar cliente: {e}")
                            flash("Erro ao atualizar dados do cliente.", "danger")
                            return render_template(
                                "peticionador/form_suspensao_dados.html",
                                title="Gerar Defesa de Suspensão",
                                form=form,
                            )
                    else:
                        flash(
                            "Cliente ID fornecido mas não encontrado no banco de dados. Por favor, busque o cliente novamente.",
                            "danger",
                        )
                        return render_template(
                            "peticionador/form_suspensao_dados.html",
                            title="Gerar Defesa de Suspensão",
                            form=form,
                        )
                else:
                    # Lógica para criar novo cliente se cliente_id não existir (pode ser implementada depois)
                    # Por agora, vamos exigir que um cliente seja buscado/selecionado
                    flash(
                        "Nenhum cliente selecionado. Por favor, busque um cliente pelo CPF.",
                        "danger",
                    )
                    return render_template(
                        "peticionador/form_suspensao_dados.html",
                        title="Gerar Defesa de Suspensão",
                        form=form,
                    )

                # Coleta dados da petição do formulário
                dados_peticao = {
                    "numero_processo_adm": form.numero_processo_adm.data,
                    "auto_infracao": form.auto_infracao.data,
                    "autoridade_transito_nome": (
                        form.autoridade_transito.data.nome
                        if form.autoridade_transito.data
                        else ""
                    ),
                    "data_notificacao": (
                        form.data_notificacao.data.strftime("%d/%m/%Y")
                        if form.data_notificacao.data
                        else ""
                    ),
                    "pontos_cnh": (
                        str(form.pontos_cnh.data)
                        if form.pontos_cnh.data is not None
                        else ""
                    ),
                    "observacoes_adicionais": form.observacoes_adicionais.data,
                }

                try:
                    # Preparar dados completos para o template do documento
                    cliente_data_para_template = {
                        "nome_completo": f"{cliente_para_documento.primeiro_nome or ''} {cliente_para_documento.sobrenome or ''}".strip(),
                        "razao_social": cliente_para_documento.razao_social
                        or "",  # Assumindo que pode ser PJ, mas o form atual foca em PF
                        "tipo_pessoa": get_enum_display_name(
                            cliente_para_documento.tipo_pessoa, TipoPessoaEnum
                        ),
                        "cpf": cliente_para_documento.cpf or "",
                        "cnpj": cliente_para_documento.cnpj or "",
                        "rg_numero": cliente_para_documento.rg_numero or "",
                        "cnh_numero": cliente_para_documento.cnh_numero or "",
                        "endereco_completo": (
                            f"{cliente_para_documento.endereco_logradouro or ''}, "
                            f"{cliente_para_documento.endereco_numero or ''} "
                            f"{cliente_para_documento.endereco_complemento or ''} - "
                            f"{cliente_para_documento.endereco_bairro or ''}, "
                            f"{cliente_para_documento.endereco_cidade or ''}/"
                            f"{cliente_para_documento.endereco_estado or ''} - "
                            f"CEP: {cliente_para_documento.endereco_cep or ''}"
                        ).strip(", - CEP: "),
                        "email": cliente_para_documento.email or "",
                        "telefone_celular": cliente_para_documento.telefone_celular
                        or "",
                        "data_atual": datetime.datetime.now().strftime(
                            "%d de %B de %Y"
                        ),
                        **dados_peticao,  # Adiciona os dados específicos da petição
                    }

                    template_id = current_app.config.get(
                        "TEMPLATE_PET_SUSPENSAO_DIREITO_DIRIGIR"
                    )
                    parent_folder_id = current_app.config.get(
                        "PETICIONADOR_PARENT_FOLDER_ID"
                    )

                    if not template_id or not parent_folder_id:
                        flash(
                            "IDs de template ou pasta pai não configurados.", "danger"
                        )
                        return render_template(
                            "peticionador/form_suspensao_dados.html",
                            title="Gerar Defesa de Suspensão",
                            form=form,
                        )

                    cliente_folder_name = (
                        f"{cliente_para_documento.primeiro_nome or ''} {cliente_para_documento.sobrenome or ''}".strip()
                        or cliente_para_documento.razao_social
                        or "Cliente Desconhecido"
                    )
                    year = datetime.datetime.now().year
                    file_name = f"{year}-{cliente_folder_name}-Suspensão Direito Dirigir-{dados_peticao['numero_processo_adm']}"

                    drive_service = google_services.create_drive_service()
                    docs_service = google_services.create_docs_service()
                    target_folder_id = google_services.create_folder_if_not_exists(
                        drive_service, parent_folder_id, cliente_folder_name
                    )

                    if not target_folder_id:
                        flash(
                            "Erro ao criar ou encontrar a pasta do cliente no Google Drive.",
                            "danger",
                        )
                        return render_template(
                            "peticionador/form_suspensao_dados.html",
                            title="Gerar Defesa de Suspensão",
                            form=form,
                        )

                    document_id, link = (
                        google_services.generate_google_docs_from_template_peticionador(
                            docs_service,
                            drive_service,
                            template_id,
                            target_folder_id,
                            file_name,
                            cliente_data_para_template,
                        )
                    )

                    if document_id:
                        flash("Documento gerado com sucesso!", "success")
                        pet = PeticaoGerada(
                            cliente_id=None,
                            modelo="Suspensao_Direito_Dirigir",
                            google_id=document_id,
                            link=link,
                        )
                        db.session.add(pet)
                        db.session.commit()
                        # Retornar JSON para o frontend abrir em nova aba
                        return jsonify({"success": True, "link": link})
                    else:
                        flash("Erro ao gerar o documento.", "danger")

                except Exception as e:
                    current_app.logger.error(
                        f"Erro ao gerar documento de suspensão: {e}"
                    )
                    current_app.logger.error(traceback.format_exc())
                    flash(
                        f"Ocorreu um erro inesperado ao gerar o documento: {e}",
                        "danger",
                    )
            # Se o form não for válido (após clicar em Gerar Petição), ele será renderizado abaixo com os erros

    return render_template(
        "peticionador/form_suspensao_dados.html",
        title="Gerar Defesa de Suspensão",
        form=form,
    )


@peticionador_bp.route("/autoridades")
@login_required
def listar_autoridades():
    autoridades = AutoridadeTransito.query.order_by(AutoridadeTransito.nome).all()
    return render_template(
        "peticionador/autoridades_listar.html",
        title="Autoridades de Trânsito",
        autoridades=autoridades,
    )


@peticionador_bp.route("/autoridades/nova", methods=["GET", "POST"])
@login_required
def adicionar_autoridade():
    form = AutoridadeTransitoForm()
    if form.validate_on_submit():
        nova_autoridade = AutoridadeTransito(
            nome=form.nome.data,
            cnpj=form.cnpj.data or None,  # Salva None se o campo estiver vazio
            logradouro=form.logradouro.data or None,
            numero=form.numero.data or None,
            complemento=form.complemento.data or None,
            cidade=form.cidade.data or None,
            estado=(
                form.estado.data.upper() if form.estado.data else None
            ),  # Salva em maiúsculas
            cep=form.cep.data or None,
        )
        try:
            db.session.add(nova_autoridade)
            db.session.commit()
            flash("Autoridade de trânsito adicionada com sucesso!", "success")
            return redirect(url_for("peticionador.listar_autoridades"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao adicionar autoridade: {str(e)}", "danger")
    return render_template(
        "peticionador/autoridade_form.html",
        title="Adicionar Autoridade de Trânsito",
        form=form,
        form_action=url_for("peticionador.adicionar_autoridade"),
    )


@peticionador_bp.route(
    "/autoridades/editar/<int:autoridade_id>", methods=["GET", "POST"]
)
@login_required
def editar_autoridade(autoridade_id):
    autoridade = AutoridadeTransito.query.get_or_404(autoridade_id)
    form = AutoridadeTransitoForm(
        obj=autoridade
    )  # Popula o formulário com dados do objeto

    if form.validate_on_submit():
        # Atualiza os campos do objeto 'autoridade' com os dados do formulário
        form.populate_obj(autoridade)
        try:
            db.session.commit()
            flash("Autoridade atualizada com sucesso.", "success")
            return redirect(url_for("peticionador.listar_autoridades"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar autoridade: {e}", "danger")

    # Para GET, ou se o formulário não for válido no POST, renderiza o template
    # com os dados atuais (ou com erros de validação)
    return render_template(
        "autoridade_form.html",
        title="Editar Autoridade de Trânsito",
        form=form,
        form_action=url_for(
            "peticionador.editar_autoridade", autoridade_id=autoridade.id
        ),
    )


@peticionador_bp.route("/autoridades/excluir/<int:autoridade_id>", methods=["GET"])
@login_required
def excluir_autoridade(autoridade_id):
    autoridade = AutoridadeTransito.query.get_or_404(autoridade_id)
    try:
        db.session.delete(autoridade)
        db.session.commit()
        flash("Autoridade excluída com sucesso.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir autoridade: {e}", "danger")
    return redirect(url_for("peticionador.listar_autoridades"))


@peticionador_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("peticionador.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            flash("Login bem-sucedido!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("peticionador.index"))
        elif user and not user.is_active:
            flash("Esta conta está desativada.", "danger")
        else:
            flash("Login falhou. Verifique seu email e senha.", "danger")
    return render_template(
        "peticionador/login.html", title="Login Peticionador", form=form
    )


@peticionador_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Você foi desconectado.", "info")
    return redirect(url_for("peticionador.login"))


# Rota exclusiva para desenvolvimento. Avalie removê-la em produção.
# Caso seja mantida, o acesso é restrito a usuários autenticados e
# bloqueado em ambiente de produção.
@peticionador_bp.route("/setup_admin_dev")
@login_required
def setup_admin_dev():
    """Cria usuário admin para testes. Não habilitar em produção."""
    if current_app.config.get("ENV") == "production":
        abort(404)

    email_admin = "fabricionext@gmail.com"
    # Verifica se o usuário admin já existe
    admin_user = User.query.filter_by(email=email_admin).first()
    if not admin_user:
        admin_user = User(email=email_admin, name="Admin Peticionador", is_active=True)
        admin_user.set_password("fea71868")  # Defina uma senha forte
        db.session.add(admin_user)
        try:
            db.session.commit()
            flash(f"Usuário admin {email_admin} criado com senha admin123.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao criar usuário admin: {str(e)}", "danger")
    else:
        flash(f"Usuário admin {email_admin} já existe.", "info")
    return redirect(url_for("peticionador.login"))


# --- Rotas para Modelos de Petição ---
@peticionador_bp.route("/modelos")
@login_required
def listar_modelos():
    from .models import PeticaoModelo

    modelos = PeticaoModelo.query.order_by(PeticaoModelo.criado_em.desc()).all()
    return render_template(
        "peticionador/modelos_listar.html", title="Modelos de Petição", modelos=modelos
    )


@peticionador_bp.route("/modelos/novo", methods=["GET", "POST"])
@login_required
def adicionar_modelo():
    from .forms import PeticaoModeloForm
    from .models import PeticaoModelo

    form = PeticaoModeloForm()
    if form.validate_on_submit():
        novo_modelo = PeticaoModelo(
            nome=form.nome.data,
            doc_template_id=form.doc_template_id.data,
            pasta_destino_id=form.pasta_destino_id.data,
            descricao=form.descricao.data,
            ativo=form.ativo.data,
        )
        try:
            db.session.add(novo_modelo)
            db.session.commit()
            flash("Modelo adicionado com sucesso!", "success")
            return redirect(
                url_for("peticionador.placeholders_modelo", modelo_id=novo_modelo.id)
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao adicionar modelo: {str(e)}", "danger")
    return render_template(
        "peticionador/modelo_form.html",
        title="Adicionar Modelo",
        form=form,
        form_action=url_for("peticionador.adicionar_modelo"),
    )


@peticionador_bp.route("/modelos/<int:modelo_id>/editar", methods=["GET", "POST"])
@login_required
def editar_modelo(modelo_id):
    from .forms import PeticaoModeloForm
    from .models import PeticaoModelo

    modelo = PeticaoModelo.query.get_or_404(modelo_id)
    form = PeticaoModeloForm(obj=modelo)
    if form.validate_on_submit():
        modelo.nome = form.nome.data
        modelo.doc_template_id = form.doc_template_id.data
        modelo.pasta_destino_id = form.pasta_destino_id.data
        modelo.descricao = form.descricao.data
        modelo.ativo = form.ativo.data
        try:
            db.session.commit()
            flash("Modelo atualizado com sucesso!", "success")
            return redirect(
                url_for("peticionador.placeholders_modelo", modelo_id=modelo.id)
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar modelo: {str(e)}", "danger")
    return render_template(
        "peticionador/modelo_form.html",
        title="Editar Modelo",
        form=form,
        form_action=url_for("peticionador.editar_modelo", modelo_id=modelo.id),
    )


# --- Rotas para Placeholders ---


@peticionador_bp.route(
    "/modelos/<int:modelo_id>/placeholders/<int:ph_id>/mover/<string:direcao>",
    methods=["GET", "POST"],
)
@login_required
def mover_placeholder(modelo_id, ph_id, direcao):
    ph = PeticaoPlaceholder.query.get_or_404(ph_id)
    if ph.modelo_id != modelo_id:
        if request.method == "POST":
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Modelo não corresponde ao placeholder.",
                    }
                ),
                400,
            )
        abort(404)

    if direcao not in ("cima", "baixo"):
        if request.method == "POST":
            return jsonify({"success": False, "error": "Direção inválida."}), 400
        abort(400)

    placeholders = (
        PeticaoPlaceholder.query.filter_by(modelo_id=modelo_id)
        .order_by(PeticaoPlaceholder.ordem)
        .all()
    )
    idx = next((i for i, p in enumerate(placeholders) if p.id == ph_id), None)
    if idx is None:
        if request.method == "POST":
            return (
                jsonify({"success": False, "error": "Placeholder não encontrado."}),
                404,
            )
        abort(404)

    if direcao == "cima" and idx == 0:
        if request.method == "POST":
            return jsonify({"success": False, "error": "Já é o primeiro."}), 400
        flash("Já é o primeiro.", "info")
    elif direcao == "baixo" and idx == len(placeholders) - 1:
        if request.method == "POST":
            return jsonify({"success": False, "error": "Já é o último."}), 400
        flash("Já é o último.", "info")
    else:
        swap_idx = idx - 1 if direcao == "cima" else idx + 1
        other = placeholders[swap_idx]
        ph.ordem, other.ordem = other.ordem, ph.ordem
        db.session.commit()
        if request.method == "POST":
            return jsonify({"success": True})
        flash("Ordem atualizada.", "success")
    if request.method == "POST":
        return jsonify({"success": True})
    return redirect(url_for("peticionador.placeholders_modelo", modelo_id=modelo_id))


@peticionador_bp.route(
    "/modelos/<int:modelo_id>/placeholders/<int:ph_id>/toggle_obrigatorio",
    methods=["POST"],
)
@login_required
def toggle_placeholder_obrigatorio(modelo_id, ph_id):
    ph = PeticaoPlaceholder.query.get_or_404(ph_id)
    if ph.modelo_id != modelo_id:
        return (
            jsonify(
                {"success": False, "error": "Modelo não corresponde ao placeholder."}
            ),
            400,
        )

    data = request.get_json() or {}
    if "obrigatorio" in data:
        ph.obrigatorio = bool(data["obrigatorio"])
    else:
        ph.obrigatorio = not ph.obrigatorio
    db.session.commit()
    return jsonify({"success": True, "obrigatorio": ph.obrigatorio})


@peticionador_bp.route("/modelos/<int:modelo_id>/placeholders")
@login_required
def placeholders_modelo(modelo_id):
    modelo = PeticaoModelo.query.get_or_404(modelo_id)
    placeholders = (
        PeticaoPlaceholder.query.filter_by(modelo_id=modelo_id)
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
    modelo = PeticaoModelo.query.get_or_404(modelo_id)
    docs_service = google_services.get_docs_service()
    chaves = google_services.extract_placeholders(docs_service, modelo.doc_template_id)
    if not chaves:
        flash(
            "Nenhum placeholder encontrado no documento ou erro ao ler o template.",
            "warning",
        )
        return redirect(
            url_for("peticionador.placeholders_modelo", modelo_id=modelo_id)
        )
    criados = 0
    for idx, chave in enumerate(chaves, start=1):
        existente = PeticaoPlaceholder.query.filter_by(
            modelo_id=modelo_id, chave=chave
        ).first()
        if not existente:
            ph = PeticaoPlaceholder(
                modelo_id=modelo_id,
                chave=chave,
                tipo_campo="string",
                label_form=chave.replace("_", " ").title(),
                ordem=idx,
            )
            db.session.add(ph)
            criados += 1
    db.session.commit()
    flash(
        f"Sincronização concluída. {criados} novos placeholders adicionados.", "success"
    )
    return redirect(url_for("peticionador.placeholders_modelo", modelo_id=modelo_id))


@peticionador_bp.route(
    "/modelos/<int:modelo_id>/placeholders/reordenar", methods=["POST"]
)
@login_required
def reordenar_placeholders(modelo_id):
    data = request.get_json()
    ordem = data.get("ordem", [])
    if not ordem or not isinstance(ordem, list):
        return jsonify({"success": False, "error": "Ordem inválida."}), 400
    try:
        for idx, ph_id in enumerate(ordem, start=1):
            ph = PeticaoPlaceholder.query.filter_by(
                id=ph_id, modelo_id=modelo_id
            ).first()
            if ph:
                ph.ordem = idx
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# --- API utilitária ---


@peticionador_bp.route("/api/clientes/busca_cpf", methods=["GET"], strict_slashes=False)
@login_required
def api_busca_cliente_cpf():
    """Retorna dados do cliente em JSON, padronizados e com tratamento de erros."""
    try:
        cpf = request.args.get("cpf", "").strip()
        cpf_digits = re.sub(r"\D", "", cpf)
        current_app.logger.info(f"API: Buscando CPF '{cpf_digits}'")
        if not cpf_digits:
            return jsonify({"success": False, "error": "CPF inválido"}), 400
        cliente = RespostaForm.query.filter_by(cpf=cpf_digits).first()
        if not cliente:
            current_app.logger.warning(
                f"API: CPF '{cpf_digits}' não encontrado no modelo RespostaForm."
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
            "rg": cliente.rg,
            "estado_emissor_rg": cliente.estado_emissor_rg,
            "cnh": cliente.cnh,
            "razao_social": getattr(cliente, "razao_social", None),
            "cnpj": getattr(cliente, "cnpj", None),
            "endereco_cep": cliente.cep,
            "endereco_logradouro": cliente.logradouro,
            "endereco_numero": cliente.numero,
            "endereco_complemento": cliente.complemento,
            "endereco_bairro": cliente.bairro,
            "endereco_cidade": cliente.cidade,
            "endereco_estado": cliente.uf_endereco,
            "email": cliente.email,
            "telefone_celular": cliente.telefone_celular,
            "telefone_outro": getattr(cliente, "outro_telefone", None),
            "nome_completo": f"{cliente.primeiro_nome or ''} {cliente.sobrenome or ''}".strip(),
            "data_nascimento": data_nascimento_str,
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


# --- Rota para Gerar Petição Dinâmica ---


def build_dynamic_form(placeholders):
    """Gera dinamicamente uma classe WTForm com campos conforme placeholders."""
    attrs = {"csrf_enabled": True}
    for ph in placeholders:
        validators = []
        if getattr(ph, "obrigatorio", True):
            validators.append(DataRequired())

        field_kwargs = {
            "label": ph.label_form or ph.chave.replace("_", " ").title(),
            "validators": validators,
        }
        if ph.tipo_campo == "date":
            attrs[ph.chave] = DateField(**field_kwargs, format="%Y-%m-%d")
        elif ph.tipo_campo == "select":
            import json

            opcoes = []
            if ph.opcoes_json:
                try:
                    opcoes = [(o, o) for o in json.loads(ph.opcoes_json)]
                except Exception:
                    pass
            attrs[ph.chave] = SelectField(choices=opcoes, **field_kwargs)
        else:
            attrs[ph.chave] = StringField(**field_kwargs)
    return type("DynamicPeticaoForm", (FlaskForm,), attrs)


@peticionador_bp.route("/modelos/<int:modelo_id>/gerar", methods=["GET", "POST"])
@login_required
def gerar_peticao_dinamica(modelo_id):
    modelo = PeticaoModelo.query.get_or_404(modelo_id)
    placeholders = (
        PeticaoPlaceholder.query.filter_by(modelo_id=modelo_id)
        .order_by(PeticaoPlaceholder.ordem)
        .all()
    )
    if not placeholders:
        flash("Nenhum placeholder configurado para este modelo.", "warning")
        return redirect(
            url_for("peticionador.placeholders_modelo", modelo_id=modelo_id)
        )

    DynamicForm = build_dynamic_form(placeholders)
    form = DynamicForm()
    if form.validate_on_submit():
        replacements = {ph.chave: form.data.get(ph.chave) for ph in placeholders}
        drive_service = google_services.get_drive_service()
        docs_service = google_services.get_docs_service()

        nome_arquivo = (
            f"{modelo.nome} - {datetime.datetime.now().strftime('%Y-%m-%d %H%M')}"
        )
        novo_id, link = google_services.copy_template_and_fill(
            drive_service,
            docs_service,
            modelo.doc_template_id,
            nome_arquivo,
            modelo.pasta_destino_id,
            replacements,
        )
        if novo_id:
            current_app.logger.info(f"Documento gerado com sucesso! ID: {novo_id}")
            # Salvar no banco - cliente_id pode ser None para formulários dinâmicos
            pet = PeticaoGerada(
                cliente_id=None, modelo=modelo.nome, google_id=novo_id, link=link
            )
            db.session.add(pet)
            db.session.commit()
            # Retorna a resposta JSON que o JavaScript espera
            return jsonify({"success": True, "link": link})
        else:
            flash("Falha ao gerar documento.", "danger")
    return render_template(
        "peticionador/peticao_form_generico.html",
        title=f"Gerar {modelo.nome}",
        form=form,
        modelo=modelo,
    )


@peticionador_bp.route(
    "/modelos/<int:modelo_id>/novo-formulario", methods=["GET", "POST"]
)
@login_required
def criar_formulario_dinamico(modelo_id):
    from models import FormularioGerado

    try:
        modelo = PeticaoModelo.query.get_or_404(modelo_id)

        if request.method == "POST":
            # Log dos dados recebidos para debug
            current_app.logger.info(f"Dados POST recebidos: {request.form}")
            current_app.logger.info(f"Headers: {dict(request.headers)}")

            nome = request.form.get("nome")
            if not nome:
                flash("Informe um nome para o formulário.", "warning")
                return render_template(
                    "peticionador/formulario_nome.html", modelo=modelo
                )

            # Verificar se já existe um formulário com este nome
            formulario_existente = FormularioGerado.query.filter_by(nome=nome).first()
            if formulario_existente:
                flash(
                    "Já existe um formulário com este nome. Escolha outro nome.",
                    "warning",
                )
                return render_template(
                    "peticionador/formulario_nome.html", modelo=modelo
                )

            # Gerar slug único
            import re
            import uuid

            slug = re.sub(r"[^a-zA-Z0-9_-]", "-", nome.lower()).strip("-")
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"

            # Verificar se o slug já existe
            while FormularioGerado.query.filter_by(slug=slug).first():
                slug = f"{slug}-{uuid.uuid4().hex[:4]}"

            try:
                # Criar entrada
                form_gerado = FormularioGerado(
                    modelo_id=modelo.id, nome=nome, slug=slug
                )
                db.session.add(form_gerado)
                db.session.commit()

                flash(f'Formulário "{nome}" criado com sucesso!', "success")
                return redirect(
                    url_for("peticionador.preencher_formulario_dinamico", slug=slug)
                )

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erro ao criar formulário: {str(e)}")
                flash(f"Erro ao criar formulário: {str(e)}", "danger")
                return render_template(
                    "peticionador/formulario_nome.html", modelo=modelo
                )

        return render_template("peticionador/formulario_nome.html", modelo=modelo)

    except Exception as e:
        current_app.logger.error(f"Erro na rota criar_formulario_dinamico: {str(e)}")
        flash(f"Erro inesperado: {str(e)}", "danger")
        return redirect(url_for("peticionador.listar_modelos"))


@peticionador_bp.route("/formularios/<slug>", methods=["GET", "POST"])
@login_required
def preencher_formulario_dinamico(slug):
    import datetime
    import re

    from app.peticionador import (  # Garanta que a importação está correta
        google_services,
    )
    from app.peticionador.models import PeticaoGerada, PeticaoModelo, PeticaoPlaceholder
    from models import FormularioGerado

    form_gerado = FormularioGerado.query.filter_by(slug=slug).first_or_404()
    modelo = PeticaoModelo.query.get_or_404(form_gerado.modelo_id)
    placeholders = (
        PeticaoPlaceholder.query.filter_by(modelo_id=modelo.id)
        .order_by(PeticaoPlaceholder.ordem)
        .all()
    )

    # Gera a classe do formulário dinamicamente
    DynamicForm = build_dynamic_form(placeholders)
    form = DynamicForm()  # Instancia o formulário

    # --- LÓGICA DE SUBMISSÃO (POST) CORRIGIDA ---
    if request.method == "POST":
        current_app.logger.error(
            "DEBUG: Entrou no POST de preencher_formulario_dinamico!"
        )
        try:
            current_app.logger.info(
                f"Recebida submissão POST para o formulário '{form_gerado.nome}'."
            )

            # 1. Coleta dos dados do formulário para o dicionário de substituições
            replacements = {
                ph.chave: request.form.get(ph.chave, "") for ph in placeholders
            }
            current_app.logger.debug(f"Dados para substituição: {replacements}")

            # 2. Construção do nome do arquivo no formato desejado
            data_atual_str = datetime.datetime.now().strftime("%d-%m-%Y")
            primeiro_nome = replacements.get("primeiro_nome", "Cliente")
            sobrenome = replacements.get("sobrenome", "")

            nome_arquivo = f"{data_atual_str} - {primeiro_nome} {sobrenome} - {form_gerado.nome}".strip()
            nome_arquivo = re.sub(r'[\\/*?:"<>|]', "", nome_arquivo)
            current_app.logger.info(f"Nome do arquivo final: '{nome_arquivo}'")

            # 3. Lógica de geração do documento (orquestração)
            drive_service = google_services.get_drive_service()
            docs_service = google_services.get_docs_service()

            novo_id, link = google_services.copy_template_and_fill(
                drive_service,
                docs_service,
                modelo.doc_template_id,
                nome_arquivo,
                modelo.pasta_destino_id,
                replacements,
            )

            if novo_id:
                current_app.logger.info(f"Documento gerado com sucesso! ID: {novo_id}")
                # Salvar no banco - cliente_id pode ser None para formulários dinâmicos
                pet = PeticaoGerada(
                    cliente_id=None, modelo=modelo.nome, google_id=novo_id, link=link
                )
                db.session.add(pet)
                db.session.commit()
                # Retorna a resposta JSON que o JavaScript espera
                return jsonify({"success": True, "link": link})
            else:
                raise Exception(
                    "A função copy_template_and_fill não retornou um ID de documento."
                )

        except Exception as e:
            current_app.logger.error(
                f"Erro crítico ao processar o formulário '{form_gerado.nome}': {e}",
                exc_info=True,
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Ocorreu um erro interno no servidor: {e}",
                    }
                ),
                500,
            )

    # --- LÓGICA PARA EXIBIÇÃO INICIAL (GET) ---
    # Instancia um formulário limpo para a renderização inicial da página
    form = DynamicForm()
    return render_template(
        "peticionador/formulario_dinamico.html",
        form=form,
        modelo=modelo,
        form_gerado=form_gerado,
    )


@peticionador_bp.route("/formularios/<slug>/excluir", methods=["POST"])
@login_required
def excluir_formulario_dinamico(slug):
    from models import FormularioGerado

    form_gerado = FormularioGerado.query.filter_by(slug=slug).first_or_404()
    db.session.delete(form_gerado)
    db.session.commit()
    flash("Formulário excluído com sucesso.", "success")
    return redirect(url_for("peticionador.listar_modelos"))


# --- Rotas para Clientes ---
@peticionador_bp.route("/clientes")
@login_required
def listar_clientes():
    """Lista todos os clientes cadastrados."""
    # Ordena por data de criação, mais recentes primeiro
    clientes = Cliente.query.order_by(Cliente.data_criacao.desc()).all()
    return render_template(
        "peticionador/clientes_listar.html",
        title="Clientes Cadastrados",
        clientes=clientes,
    )


@peticionador_bp.route("/clientes/novo", methods=["GET", "POST"])
@login_required
def adicionar_cliente():
    """Adiciona um novo cliente (PF ou PJ)."""
    form = ClienteForm()
    if form.validate_on_submit():
        try:
            novo_cliente = Cliente(
                tipo_pessoa=form.tipo_pessoa.data,
                # Dados Comuns
                email=form.email.data or None,
                telefone_celular=form.telefone_celular.data or None,
                telefone_outro=form.telefone_outro.data or None,
                endereco_logradouro=form.endereco_logradouro.data or None,
                endereco_numero=form.endereco_numero.data or None,
                endereco_complemento=form.endereco_complemento.data or None,
                endereco_bairro=form.endereco_bairro.data or None,
                endereco_cidade=form.endereco_cidade.data or None,
                endereco_estado=form.endereco_estado.data or None,
                endereco_cep=form.endereco_cep.data or None,
            )

            if form.tipo_pessoa.data == "FISICA":
                novo_cliente.primeiro_nome = form.primeiro_nome.data or None
                novo_cliente.sobrenome = form.sobrenome.data or None
                novo_cliente.nacionalidade = form.nacionalidade.data or None
                novo_cliente.rg_numero = form.rg_numero.data or None
                novo_cliente.rg_orgao_emissor = form.rg_orgao_emissor.data or None
                novo_cliente.rg_uf_emissor = form.rg_uf_emissor.data or None
                novo_cliente.estado_civil = form.estado_civil.data or None
                novo_cliente.cpf = form.cpf.data or None
                novo_cliente.profissao = form.profissao.data or None
                novo_cliente.cnh_numero = form.cnh_numero.data or None
                novo_cliente.data_nascimento = form.data_nascimento.data
            elif form.tipo_pessoa.data == "JURIDICA":
                novo_cliente.razao_social = form.razao_social.data or None
                novo_cliente.cnpj = form.cnpj.data or None
                novo_cliente.representante_nome = form.representante_nome.data or None
                novo_cliente.representante_cpf = form.representante_cpf.data or None
                novo_cliente.representante_rg_numero = (
                    form.representante_rg_numero.data or None
                )
                novo_cliente.representante_rg_orgao_emissor = (
                    form.representante_rg_orgao_emissor.data or None
                )
                novo_cliente.representante_rg_uf_emissor = (
                    form.representante_rg_uf_emissor.data or None
                )
                novo_cliente.representante_cargo = form.representante_cargo.data or None

            db.session.add(novo_cliente)
            db.session.commit()
            flash("Cliente adicionado com sucesso!", "success")
            return redirect(url_for("peticionador.listar_clientes"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao adicionar cliente: {str(e)}", "danger")
            current_app.logger.error(
                f"Erro ao adicionar cliente: {str(e)}\n{traceback.format_exc()}"
            )  # Adiciona log detalhado

    return render_template(
        "peticionador/cliente_form.html",
        title="Adicionar Novo Cliente",
        form=form,
        form_action=url_for("peticionador.adicionar_cliente"),
    )


# --- Rota para Geração de Documento de Suspensão ---
@peticionador_bp.route(
    "/cliente/<int:cliente_id>/gerar_suspensao", methods=["GET", "POST"]
)
@login_required
def gerar_documento_suspensao(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    form = GerarDocumentoSuspensaoForm()

    if form.validate_on_submit():
        try:
            processo_numero = form.processo_numero.data
            total_pontos = form.total_pontos.data

            # Obter serviços do Google (agora usam conta de serviço, sem creds explícitas)
            drive_service = google_services.get_drive_service()
            docs_service = google_services.get_docs_service()

            if not drive_service or not docs_service:
                flash(
                    "Não foi possível conectar aos serviços do Google. "
                    "Verifique a configuração da conta de serviço ou tente novamente mais tarde.",
                    "danger",
                )
                return render_template(
                    "peticionador/gerar_suspensao_form.html",
                    title="Gerar Suspensão do Direito de Dirigir",
                    form=form,
                    cliente=cliente,
                    TipoPessoaEnum=TipoPessoaEnum,
                )

            # Definir o nome da pasta do cliente (ANO-NOME)
            current_year = datetime.datetime.now().year
            client_folder_name = f"{current_year}-{cliente.nome_completo}"  # Mantendo espaços no nome da pasta, google_services tratará

            # Obter ID do template de suspensão do config.py
            try:
                template_id = CONFIG["TEMPLATES"]["pet"]["Suspensao Direito Dirigir"]
                if not template_id:
                    raise KeyError(
                        "ID do template de suspensão não encontrado nas configurações."
                    )
            except KeyError as e:
                current_app.logger.error(
                    f"Erro ao obter ID do template de suspensão: {e}"
                )
                flash(
                    "Erro de configuração: ID do template de suspensão não definido. Contate o administrador.",
                    "danger",
                )
                return render_template(
                    "peticionador/gerar_suspensao_form.html",
                    title="Gerar Suspensão do Direito de Dirigir",
                    form=form,
                    cliente=cliente,
                    TipoPessoaEnum=TipoPessoaEnum,
                )

            target_folder_id = google_services.find_or_create_client_folder(
                drive_service, client_folder_name
            )  # PARENT_FOLDER_ID é gerenciado internamente por find_or_create_client_folder
            if not target_folder_id:
                flash(
                    "Erro ao encontrar ou criar a pasta do cliente no Google Drive.",
                    "danger",
                )
                return render_template(
                    "peticionador/gerar_suspensao_form.html",
                    title="Gerar Suspensão do Direito de Dirigir",
                    form=form,
                    cliente=cliente,
                    TipoPessoaEnum=TipoPessoaEnum,
                )

            # Definir nome do arquivo final
            # Formato: [ANO]-[Nome Cliente]-Suspensão do Direito de Dirigir-[Número Processo]
            file_name = f"{client_folder_name}-Suspensão do Direito de Dirigir-{processo_numero}"

            # Preparar substituições (placeholders SEM chaves duplas aqui)
            replacements = {
                "proprietario.nome_completo": (
                    f"{cliente.primeiro_nome or ''} {cliente.sobrenome or ''}".strip()
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    else cliente.razao_social or ""
                ),
                "proprietario.primeiro_nome": (
                    cliente.primeiro_nome or ""
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    else ""
                ),
                "proprietario.sobrenome": (
                    cliente.sobrenome or ""
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    else ""
                ),
                "proprietario.nacionalidade": (
                    cliente.nacionalidade or ""
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    else ""
                ),
                "proprietario.estado_civil": (
                    get_enum_display_name(cliente.estado_civil)
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    and cliente.estado_civil
                    else ""
                ),
                "proprietario.profissao": (
                    cliente.profissao or ""
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    else ""
                ),
                "proprietario.rg": (
                    cliente.rg_numero or ""
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    else ""
                ),
                "proprietario.rg_emissor": (
                    f"{cliente.rg_orgao_emissor or ''}/{cliente.rg_uf_emissor or ''}".strip(
                        "/"
                    )
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    and (cliente.rg_orgao_emissor or cliente.rg_uf_emissor)
                    else ""
                ),
                "proprietario.cpf": (
                    cliente.cpf or ""
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    else ""
                ),
                "proprietario.cnpj": (
                    cliente.cnpj or ""
                    if cliente.tipo_pessoa == TipoPessoaEnum.JURIDICA
                    else ""
                ),
                "proprietario.razao_social": (
                    cliente.razao_social or ""
                    if cliente.tipo_pessoa == TipoPessoaEnum.JURIDICA
                    else ""
                ),
                "proprietario.endereco_completo": (
                    f"{cliente.endereco_logradouro or ''}, "
                    f"{cliente.endereco_numero or ''} "
                    f"{cliente.endereco_complemento or ''} - "
                    f"{cliente.endereco_bairro or ''}, "
                    f"{cliente.endereco_cidade or ''}/"
                    f"{cliente.endereco_estado or ''} - "
                    f"CEP: {cliente.endereco_cep or ''}"
                ).strip(", - CEP: "),
                "proprietario.endereco_logradouro": cliente.endereco_logradouro or "",
                "proprietario.endereco_numero": cliente.endereco_numero or "",
                "proprietario.endereco_complemento": cliente.endereco_complemento or "",
                "proprietario.endereco_bairro": cliente.endereco_bairro or "",
                "proprietario.endereco_cidade": cliente.endereco_cidade or "",
                "proprietario.endereco_estado": cliente.endereco_estado or "",
                "proprietario.endereco_cep": cliente.endereco_cep or "",
                "proprietario.cnh": (
                    cliente.cnh_numero or ""
                    if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
                    else ""
                ),
                # Dados do processo (do formulário)
                "processo.numero": processo_numero,
                "processo.total_pontos_cnh": total_pontos,
                # Outros placeholders
                "data.atual_extenso": google_services.get_current_date_extenso(),
            }

            new_document_id, new_document_url = google_services.copy_template_and_fill(
                drive_service,
                docs_service,
                template_id,
                file_name,
                target_folder_id,
                replacements,
            )

            if new_document_id:
                # Registra histórico da petição
                try:
                    nova_peticao = PeticaoGerada(
                        cliente_id=cliente.id,
                        modelo="Suspensao_Direito_Dirigir",
                        google_id=new_document_id,
                        link=new_document_url,
                    )
                    db.session.add(nova_peticao)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Erro ao registrar PeticaoGerada: {e}")
                flash(
                    f'Documento "{file_name}" gerado com sucesso! '
                    f'<a href="{new_document_url}" target="_blank">Abrir documento</a>',
                    "success",
                )
                return jsonify({"success": True, "link": new_document_url})
            else:
                flash(
                    "Erro ao gerar o documento no Google Docs. "
                    "Verifique os logs para mais detalhes.",
                    "danger",
                )

        except Exception as e:
            current_app.logger.error(
                f"Erro ao gerar documento de suspensão para cliente {cliente_id}: {str(e)}\n{traceback.format_exc()}"
            )
            flash(
                f"Ocorreu um erro inesperado ao gerar o documento: {str(e)}", "danger"
            )

    return render_template(
        "peticionador/gerar_suspensao_form.html",
        title="Gerar Suspensão do Direito de Dirigir",
        form=form,
        cliente=cliente,
        TipoPessoaEnum=TipoPessoaEnum,
    )


@peticionador_bp.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
@login_required
def editar_cliente(cliente_id):
    """Edita um cliente existente (PF ou PJ)."""
    cliente = Cliente.query.get_or_404(cliente_id)
    form = ClienteForm(obj=cliente)  # Popula o formulário com dados do cliente

    if form.validate_on_submit():
        try:
            cliente.tipo_pessoa = form.tipo_pessoa.data
            # Dados Comuns
            cliente.email = form.email.data or None
            cliente.telefone_celular = form.telefone_celular.data or None
            cliente.telefone_outro = form.telefone_outro.data or None
            cliente.endereco_logradouro = form.endereco_logradouro.data or None
            cliente.endereco_numero = form.endereco_numero.data or None
            cliente.endereco_complemento = form.endereco_complemento.data or None
            cliente.endereco_bairro = form.endereco_bairro.data or None
            cliente.endereco_cidade = form.endereco_cidade.data or None
            cliente.endereco_estado = form.endereco_estado.data or None
            cliente.endereco_cep = form.endereco_cep.data or None

            if form.tipo_pessoa.data == "FISICA":
                cliente.primeiro_nome = form.primeiro_nome.data or None
                cliente.sobrenome = form.sobrenome.data or None
                cliente.nacionalidade = form.nacionalidade.data or None
                cliente.rg_numero = form.rg_numero.data or None
                cliente.rg_orgao_emissor = form.rg_orgao_emissor.data or None
                cliente.rg_uf_emissor = form.rg_uf_emissor.data or None
                cliente.estado_civil = form.estado_civil.data or None
                cliente.cpf = form.cpf.data or None
                cliente.profissao = form.profissao.data or None
                cliente.cnh_numero = form.cnh_numero.data or None
                cliente.data_nascimento = form.data_nascimento.data
                # Limpar campos de PJ se mudou de PJ para PF
                cliente.razao_social = None
                cliente.cnpj = None
                cliente.representante_nome = None
                cliente.representante_cpf = None
                cliente.representante_rg_numero = None
                cliente.representante_rg_orgao_emissor = None
                cliente.representante_rg_uf_emissor = None
                cliente.representante_cargo = None
            elif form.tipo_pessoa.data == "JURIDICA":
                cliente.razao_social = form.razao_social.data or None
                cliente.cnpj = form.cnpj.data or None
                cliente.representante_nome = form.representante_nome.data or None
                cliente.representante_cpf = form.representante_cpf.data or None
                cliente.representante_rg_numero = (
                    form.representante_rg_numero.data or None
                )
                cliente.representante_rg_orgao_emissor = (
                    form.representante_rg_orgao_emissor.data or None
                )
                cliente.representante_rg_uf_emissor = (
                    form.representante_rg_uf_emissor.data or None
                )
                cliente.representante_cargo = form.representante_cargo.data or None
                # Limpar campos de PF se mudou de PF para PJ
                cliente.primeiro_nome = None
                cliente.sobrenome = None
                cliente.nacionalidade = None
                cliente.rg_numero = None
                cliente.rg_orgao_emissor = None
                cliente.rg_uf_emissor = None
                cliente.estado_civil = None
                cliente.cpf = None
                cliente.profissao = None
                cliente.cnh_numero = None
                cliente.data_nascimento = None

            db.session.commit()
            flash("Cliente atualizado com sucesso!", "success")
            return redirect(url_for("peticionador.listar_clientes"))
        except Exception as e:
            db.session.rollback()
            flash(f"Erro ao atualizar cliente: {str(e)}", "danger")
            current_app.logger.error(
                f"Erro ao atualizar cliente {cliente_id}: {str(e)}\n{traceback.format_exc()}"
            )
    elif request.method == "GET":
        # Garante que o campo tipo_pessoa (RadioField) seja corretamente selecionado ao carregar
        form.tipo_pessoa.data = cliente.tipo_pessoa

    return render_template(
        "peticionador/cliente_form.html",
        title=f"Editar Cliente: {cliente.primeiro_nome or cliente.razao_social}",
        form=form,
        form_action=url_for("peticionador.editar_cliente", cliente_id=cliente.id),
    )


@peticionador_bp.route("/clientes/<int:cliente_id>")
@login_required
def visualizar_cliente(cliente_id):
    """Visualiza os detalhes de um cliente específico."""
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template(
        "peticionador/cliente_detalhes.html",
        title="Detalhes do Cliente",
        cliente=cliente,
    )


@peticionador_bp.route(
    "/clientes/<int:cliente_id>/excluir", methods=["GET", "POST"]
)  # Permitir POST para futura melhoria
@login_required
def excluir_cliente(cliente_id):
    """Exclui um cliente do banco de dados."""
    cliente = Cliente.query.get_or_404(cliente_id)
    try:
        nome_cliente = (
            f"{cliente.primeiro_nome or ''} {cliente.sobrenome or ''}"
            if cliente.tipo_pessoa == TipoPessoaEnum.FISICA
            else cliente.razao_social
        )
        db.session.delete(cliente)
        db.session.commit()
        flash(f'Cliente "{nome_cliente}" excluído com sucesso!', "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao excluir cliente: {str(e)}", "danger")
        current_app.logger.error(
            f"Erro ao excluir cliente {cliente_id}: {str(e)}\n{traceback.format_exc()}"
        )
    return redirect(url_for("peticionador.listar_clientes"))


@peticionador_bp.route("/api/autoridades/busca", methods=["GET"])
@login_required
def api_busca_autoridade():
    nome = request.args.get("nome", "").strip()
    autocomplete = request.args.get("autocomplete", "0") == "1"
    if not nome:
        return jsonify({"success": False, "error": "Nome não informado."}), 400
    if autocomplete:
        autoridades = (
            AutoridadeTransito.query.filter(AutoridadeTransito.nome.ilike(f"%{nome}%"))
            .limit(10)
            .all()
        )
        return jsonify(
            {
                "success": True,
                "sugestoes": [
                    {
                        "id": a.id,
                        "nome": a.nome,
                        "cnpj": a.cnpj,
                        "logradouro": a.logradouro,
                        "cidade": a.cidade,
                        "cep": a.cep,
                        "estado": a.estado,
                    }
                    for a in autoridades
                ],
            }
        )
    else:
        autoridade = AutoridadeTransito.query.filter(
            AutoridadeTransito.nome.ilike(f"%{nome}%")
        ).first()
        if not autoridade:
            return (
                jsonify({"success": False, "error": "Autoridade não encontrada."}),
                404,
            )
        return jsonify(
            {
                "success": True,
                "autoridade": {
                    "nome": autoridade.nome,
                    "cnpj": autoridade.cnpj,
                    "logradouro": autoridade.logradouro,
                    "cidade": autoridade.cidade,
                    "cep": autoridade.cep,
                    "estado": autoridade.estado,
                },
            }
        )


@peticionador_bp.route("/api/autoridades", methods=["POST"])
@login_required
def api_cadastrar_autoridade():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "JSON não enviado."}), 400
    nome = data.get("nome", "").strip()
    cnpj = data.get("cnpj", "").strip()
    logradouro = data.get("logradouro", "").strip()
    cidade = data.get("cidade", "").strip()
    cep = data.get("cep", "").strip()
    estado = data.get("estado", "").strip()
    if not nome:
        return jsonify({"success": False, "error": "Nome é obrigatório."}), 400
    # Verifica se já existe autoridade com o mesmo nome
    if AutoridadeTransito.query.filter_by(nome=nome).first():
        return (
            jsonify(
                {"success": False, "error": "Já existe uma autoridade com esse nome."}
            ),
            409,
        )
    autoridade = AutoridadeTransito(
        nome=nome,
        cnpj=cnpj,
        logradouro=logradouro,
        cidade=cidade,
        cep=cep,
        estado=estado,
    )
    db.session.add(autoridade)
    db.session.commit()
    return (
        jsonify(
            {
                "success": True,
                "autoridade": {
                    "id": autoridade.id,
                    "nome": autoridade.nome,
                    "cnpj": autoridade.cnpj,
                    "logradouro": autoridade.logradouro,
                    "cidade": autoridade.cidade,
                    "cep": autoridade.cep,
                    "estado": autoridade.estado,
                },
            }
        ),
        201,
    )
