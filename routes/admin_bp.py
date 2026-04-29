from flask import Blueprint, request,  render_template,  redirect, url_for, flash, current_app
from dao.leituraDAO import LeituraDAO
from werkzeug.security import check_password_hash
from modelo.leitura import Leitura
from modelo.admin import Admin
from banco import db
from decorators import admin_required
from dao.usuarioDAO import UsuarioDAO
from flask_login import login_user, logout_user, login_required
from datetime import datetime
from utils import lista_sensores
from grafico import grafico



admin_bp = Blueprint("admin_bp", __name__)

@login_required
@admin_required
@admin_bp.route("/admin", methods=["GET"])
def admin_page():
    leituras = LeituraDAO.listar_todas()
    # transforma em dicionários simples para o template
    leituras_data = [{
        "id": l.id,
        "sensor_id": l.sensor_id,
        "tipo": l.tipo,
        "valor": getattr(l, "valor", None),
        "timestamp": str(l.timestamp)
    } for l in leituras]
    return render_template("admin/admin_panel.html", leituras=leituras_data)



@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin/admin_login.html")

    usuario = request.form.get("usuario")
    senha = request.form.get("senha")

    user_hash = current_app.config.get("ADMIN_USER_HASH")
    pass_hash = current_app.config.get("ADMIN_PASSWORD_HASH")

    ok_user = check_password_hash(user_hash, usuario)
    ok_pass = check_password_hash(pass_hash, senha)

    if ok_user and ok_pass:
        login_user(Admin())
        return redirect(url_for("admin_bp.admin_page"))

    flash("Usuário ou senha inválidos.", "danger")
    return redirect(url_for("admin_bp.admin_login"))


# Logout
@admin_bp.route("/admin/logout")
def admin_logout():
    logout_user()
    flash("Logout efetuado.", "info")
    return redirect(url_for("home"))

@login_required
@admin_required
@admin_bp.route("/admin/delete", methods=["POST"])
def admin_delete():
    sensor = request.form.get("sensor")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not sensor or not data_inicio or not data_fim:
        flash("Preencha todos os campos!", "danger")
        return redirect(url_for("admin_bp.admin_page"))

    from datetime import datetime
    try:
        d1 = datetime.strptime(data_inicio, "%Y-%m-%d")
        d2 = datetime.strptime(data_fim, "%Y-%m-%d")
    except:
        flash("Datas inválidas!", "danger")
        return redirect(url_for("admin_bp.admin_page"))

    # Buscar leituras do tipo escolhido no intervalo solicitado
    leituras = (
        Leitura.query
        .filter(Leitura.tipo == sensor)
        .filter(Leitura.timestamp >= d1)
        .filter(Leitura.timestamp <= d2)
        .all()
    )

    if not leituras:
        flash("Nenhuma leitura encontrada nesse intervalo!", "warning")
        return redirect(url_for("admin_bp.admin_page"))

    # Apagar tudo
    for l in leituras:
        db.session.delete(l)

    db.session.commit()

    flash(f"{len(leituras)} leituras do sensor '{sensor}' foram removidas.", "success")
    return redirect(url_for("admin_bp.admin_page"))

@login_required
@admin_required
@admin_bp.route("/admin/delete/<int:id>", methods=["POST"])
def admin_delete_by_id(id):
    leitura = Leitura.query.get(id)

    if not leitura:
        flash("Leitura não encontrada", "danger")
        return redirect(url_for("admin_bp.admin_page"))

    db.session.delete(leitura)
    db.session.commit()

    flash("Leitura excluída", "success")
    return redirect(url_for("admin_bp.admin_page"))

@login_required
@admin_required
@admin_bp.route("/admin/delete_by_date", methods=["GET"])
def delete_by_date_page():
    return render_template("admin/admin_delete_by_date_page.html")


@login_required
@admin_required
@admin_bp.route("/admin/usuarios/delete/<int:id>", methods=["POST"])
def admin_delete_usuario(id):
    UsuarioDAO.deletar(id)
    return redirect(url_for("admin_bp.admin_usuarios"))

@login_required
@admin_required
@admin_bp.route("/admin/usuarios")
def admin_usuarios():
    usuarios = UsuarioDAO.listar_aprovados()  # 🔥 aqui
    return render_template("admin/admin_usuarios.html", usuarios=usuarios)

@login_required
@admin_required
@admin_bp.route("/admin/usuarios/pendentes")
def usuarios_pendentes():
    usuarios = UsuarioDAO.listar_pendentes()
    return render_template("admin/admin_pendentes.html", usuarios=usuarios)

@login_required
@admin_required
@admin_bp.route("/admin/usuarios/aprovar/<int:id>")
def aprovar_usuario(id):
    UsuarioDAO.aprovar_usuario(id)
    return redirect(url_for("admin_bp.usuarios_pendentes"))

@login_required
@admin_required
@admin_bp.route("/admin/usuarios/recusar/<int:id>")
def recusar_usuario(id):
    UsuarioDAO.deletar(id)
    return redirect(url_for("admin_bp.usuarios_pendentes"))

@login_required
@admin_required
@admin_bp.route("/filtrar", methods=["GET"])
def filtrar_leituras():

    sensor_id = request.args.get("sensor_id")
    tipo = request.args.get("tipo")
    valor_min = request.args.get("valor_min")
    valor_max = request.args.get("valor_max")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    # Conversão de datas (ISO esperado)
    try:
        data_inicio = datetime.fromisoformat(data_inicio) if data_inicio else None
    except Exception:
        data_inicio = None

    try:
        data_fim = datetime.fromisoformat(data_fim) if data_fim else None
    except Exception:
        data_fim = None

    if data_fim:
        data_fim = data_fim.replace(second=59, microsecond=999999)

    # Conversão numérica segura
    try:
        valor_min = float(valor_min) if valor_min else None
    except Exception:
        valor_min = None

    try:
        valor_max = float(valor_max) if valor_max else None
    except Exception:
        valor_max = None



    try:
        leituras = LeituraDAO.filtrar(
            sensor_id=sensor_id,
            tipo=tipo,
            valor_min=valor_min,
            valor_max=valor_max,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
    except ValueError:
        # fallback seguro se tipo for inválido
        leituras = []

    return render_template(
        "admin/admin_panel.html",
        leituras=leituras,
        sensores=lista_sensores
    )


@login_required
@admin_required
@admin_bp.route("/grafico-filtrado", methods=["GET"])
def grafico_filtrado():

    from datetime import datetime

    sensores = ["temperatura_ar", "umidade_ar", "umidade_solo", "rad_solar"]

    tipo = request.args.get("tipo")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    graphHTML = None
    aviso = None

    if tipo:

        query = Leitura.query.filter(Leitura.tipo == tipo)

        # 🔹 filtro por data direto no banco (correto)
        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio)
            query = query.filter(Leitura.timestamp >= data_inicio)

        if data_fim:
            data_fim = datetime.fromisoformat(data_fim)
            query = query.filter(Leitura.timestamp <= data_fim)

        leituras = query.order_by(Leitura.timestamp.asc()).all()

        if not leituras:
            aviso = "⚠ Nenhum dado encontrado para esse filtro."
        else:
            fig = grafico.gerar_graf(leituras, tipo)
            graphHTML = fig.to_html(full_html=False)

    return render_template(
        "admin/graficoc.html",
        sensores=sensores,
        graphHTML=graphHTML,
        aviso=aviso
    )