from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash, current_app
from dao.leituraDAO import LeituraDAO
from werkzeug.security import check_password_hash
from modelo.leitura import Leitura
from grafico import grafico
from dao.banco import db
import pandas as pd
from dao.usuarioDAO import UsuarioDAO


admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/admin", methods=["GET"])
def admin_page():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))
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
        session["is_admin"] = True
        return redirect(url_for("admin_bp.admin_page"))

    flash("Usuário ou senha inválidos.", "danger")
    return redirect(url_for("admin_bp.admin_login"))


# Logout
@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logout efetuado.", "info")
    return redirect(url_for("home"))


@admin_bp.route("/admin/delete", methods=["POST"])
def admin_delete():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

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

@admin_bp.route("/admin/delete/<int:id>", methods=["POST"])
def admin_delete_by_id(id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    leitura = Leitura.query.get(id)

    if not leitura:
        flash("Leitura não encontrada", "danger")
        return redirect(url_for("admin_bp.admin_page"))

    db.session.delete(leitura)
    db.session.commit()

    flash("Leitura excluída", "success")
    return redirect(url_for("admin_bp.admin_page"))

@admin_bp.route("/admin/delete_by_date", methods=["GET"])
def delete_by_date_page():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))
    return render_template("admin/admin_delete_by_date_page.html")




@admin_bp.route("/admin/usuarios/delete/<int:id>", methods=["POST"])
def admin_delete_usuario(id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    UsuarioDAO.deletar(id)
    return redirect(url_for("admin_bp.admin_usuarios"))


@admin_bp.route("/admin/usuarios")
def admin_usuarios():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    usuarios = UsuarioDAO.listar_aprovados()  # 🔥 aqui
    return render_template("admin/admin_usuarios.html", usuarios=usuarios)


@admin_bp.route("/admin/usuarios/pendentes")
def usuarios_pendentes():
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    usuarios = UsuarioDAO.listar_pendentes()
    return render_template("admin/admin_pendentes.html", usuarios=usuarios)

@admin_bp.route("/admin/usuarios/aprovar/<int:id>")
def aprovar_usuario(id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    UsuarioDAO.aprovar_usuario(id)
    return redirect(url_for("admin_bp.usuarios_pendentes"))

@admin_bp.route("/admin/usuarios/recusar/<int:id>")
def recusar_usuario(id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_bp.admin_login"))

    UsuarioDAO.deletar(id)
    return redirect(url_for("admin_bp.usuarios_pendentes"))


