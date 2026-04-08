from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash, current_app
from dao.modelsDAO import LeituraDAO
from werkzeug.security import check_password_hash
from modelo.leitura import Leitura
from grafico import grafico
from dao.banco import db
import pandas as pd
from dao.modelsDAO import UsuarioDAO

leitura_bp = Blueprint("leitura_bp", __name__)


@leitura_bp.route("/api/leituras", methods=["POST"])
def receber_leitura():
    dados = request.get_json()
    if not dados or not all(k in dados for k in ("sensor_id", "tipo", "valor")):
        print('NAO - ', dados)
        return jsonify({"erro": "JSON inválido ou incompleto"}), 400
    print('SIM - ', dados)
    leitura = LeituraDAO.salvar(
        sensor_id=dados["sensor_id"],
        tipo=dados["tipo"],
        valor=dados["valor"]
    )
    return jsonify(leitura.to_dict()), 201



@leitura_bp.route("/api/leituras", methods=["GET"])
def listar_leituras_api():
    leituras = LeituraDAO.listar_todas()
    return jsonify([l.to_dict() for l in leituras])



@leitura_bp.route("/", methods=["GET"])
def listar_leituras_view():
    leituras = LeituraDAO.listar_todas()
    return jsonify([l.to_dict() for l in leituras])


# ===========================
# GRAFICO ÚNICO
# ===========================
@leitura_bp.route("/grafico/<string:tipo>")
def view_grafico(tipo):
    leituras = LeituraDAO.get_dados_sensor(tipo) or []

    if not leituras:
        return render_template("grafico.html", aviso=f"⚠ Nenhum dado para '{tipo}'", graphHTML=None)

    fig = grafico.gerar_graf(leituras, tipo)
    graph_html = fig.to_html(full_html=False)

    return render_template("grafico.html", graphHTML=graph_html)


# ===========================
# CORRELAÇÃO — ROTA PRINCIPAL
# ===========================
@leitura_bp.route("/correlacao", methods=["GET", "POST"])
def pagina_correlacao():

    from analise.analisador import gerar_correlacao_sensor

    # pega intervalo total de datas do banco
    leituras = LeituraDAO.listar_todas()
    datas = [l.getTimestamp() for l in leituras if l.getTimestamp()]
    data_min = min(datas).strftime("%Y-%m-%d") if datas else None
    data_max = max(datas).strftime("%Y-%m-%d") if datas else None

    # quem define a página é o "mode"
    mode = request.args.get("mode") or request.form.get("mode") or "clima"

    template_map = {
        "clima": "correlacao_clima.html",
        "frutos": "correlacao_frutos.html",
        "clima_fruto": "correlacao_clima_fruto.html"
    }

    template = template_map.get(mode, "correlacao_clima.html")

    # GET → só abre a página
    if request.method == "GET":
        return render_template(
            template,
            data_min=data_min,
            data_max=data_max,
            mode=mode
        )

    # POST → calcular correlação
    tipo1 = request.form.get("sensor1")
    tipo2 = request.form.get("sensor2")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not tipo1 or not tipo2:
        return render_template(
            template,
            aviso="Selecione os dois sensores.",
            data_min=data_min,
            data_max=data_max,
            mode=mode
        )

    leituras1 = LeituraDAO.get_dados_sensor(tipo1)
    leituras2 = LeituraDAO.get_dados_sensor(tipo2)

    if not leituras1 or not leituras2:
        return render_template(
            template,
            aviso="⚠ Sensores sem dados suficientes.",
            data_min=data_min,
            data_max=data_max,
            mode=mode
        )

    df1 = pd.DataFrame([{"valor": l.getValor(), "timestamp": l.getTimestamp()} for l in leituras1])
    df2 = pd.DataFrame([{"valor": l.getValor(), "timestamp": l.getTimestamp()} for l in leituras2])

    df1["timestamp"] = pd.to_datetime(df1["timestamp"])
    df2["timestamp"] = pd.to_datetime(df2["timestamp"])

    if data_inicio and data_fim:
        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim)

        df1 = df1[(df1["timestamp"] >= data_inicio) & (df1["timestamp"] <= data_fim)]
        df2 = df2[(df2["timestamp"] >= data_inicio) & (df2["timestamp"] <= data_fim)]

    corre, _, _ = gerar_correlacao_sensor(tipo1, tipo2)
    fig = grafico.grafico_correlacao(df1, df2)
    graph_html = fig.to_html(full_html=False)

    return render_template(
        template,
        graphHTML=graph_html,
        correlacao=corre,
        data_min=data_min,
        data_max=data_max,
        mode=mode
    )



# ===========================
# DEBUG
# ===========================
@leitura_bp.route("/datas")
def listar_datas():
    leituras = LeituraDAO.listar_todas()
    datas = sorted({str(l.getTimestamp()) for l in leituras})
    return "<br>".join(datas)


@leitura_bp.route("/correlacao/clima", methods=["GET"])
def corre_clima_page():
    return render_template("correlacao_clima.html")


@leitura_bp.route("/correlacao/frutos", methods=["GET"])
def corre_frutos_page():
    return render_template("correlacao_frutos.html")


@leitura_bp.route("/correlacao/user", methods=["GET", "POST"])
def correlacao_usuario():

    from modelo.leitura import ColetaFruto
    from analise.analisador import gerar_correlacao_sensor
    import pandas as pd

    # 🔒 segurança
    if not session.get("usuario_logado"):
        return redirect(url_for("user_bp.login"))

    if request.method == "GET":
        return render_template("correlacao_user.html")

    # =========================
    # PEGAR DADOS DO FORM
    # =========================
    sensor = request.form.get("sensor")
    atributo = request.form.get("atributo")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not sensor or not atributo:
        return render_template("correlacao_user.html", aviso="Preencha todos os campos")

    # =========================
    # BUSCAR DADOS DO USUÁRIO
    # =========================
    coletas = ColetaFruto.query.filter_by(usuario_id=session["user_id"]).all()

    if not coletas:
        return render_template("correlacao_user.html", aviso="Você não possui coletas")

    # =========================
    # DATAFRAME FRUTO
    # =========================
    try:
        df_fruto = pd.DataFrame([
            {
                "valor_fruto": getattr(c, atributo),
                "timestamp": c.timestamp
            }
            for c in coletas if getattr(c, atributo) is not None
        ])
    except AttributeError:
        return render_template("correlacao_user.html", aviso="Atributo inválido")

    if df_fruto.empty:
        return render_template("correlacao_user.html", aviso="Sem dados válidos de fruto")

    df_fruto["timestamp"] = pd.to_datetime(df_fruto["timestamp"])

    # =========================
    # BUSCAR SENSOR
    # =========================
    leituras = LeituraDAO.get_dados_sensor(sensor)

    if not leituras:
        return render_template("correlacao_user.html", aviso="Sensor sem dados")

    df_sensor = pd.DataFrame([
        {
            "valor_sensor": l.getValor(),
            "timestamp": l.getTimestamp()
        }
        for l in leituras if l.getTimestamp() is not None
    ])

    if df_sensor.empty:
        return render_template("correlacao_user.html", aviso="Sem dados do sensor")

    df_sensor["timestamp"] = pd.to_datetime(df_sensor["timestamp"])

    # =========================
    # FILTRO POR DATA
    # =========================
    if data_inicio and data_fim:
        try:
            d1 = pd.to_datetime(data_inicio)
            d2 = pd.to_datetime(data_fim)

            df_fruto = df_fruto[(df_fruto["timestamp"] >= d1) & (df_fruto["timestamp"] <= d2)]
            df_sensor = df_sensor[(df_sensor["timestamp"] >= d1) & (df_sensor["timestamp"] <= d2)]

        except Exception:
            return render_template("correlacao_user.html", aviso="Datas inválidas")

    # =========================
    # 🔥 ALINHAMENTO TEMPORAL (CRÍTICO)
    # =========================
    df_fruto = df_fruto.sort_values("timestamp")
    df_sensor = df_sensor.sort_values("timestamp")

    df = pd.merge_asof(
        df_fruto,
        df_sensor,
        on="timestamp",
        direction="nearest"
    )

    # =========================
    # VALIDAÇÃO
    # =========================
    if len(df) < 5:
        return render_template("correlacao_user.html", aviso="Poucos dados para correlação")

    # =========================
    # CÁLCULO
    # =========================
    correlacao = df["valor_fruto"].corr(df["valor_sensor"])

    # =========================
    # GRÁFICO
    # =========================
    from grafico import grafico
    fig = grafico.grafico_correlacao(
        df[["valor_fruto", "timestamp"]],
        df[["valor_sensor", "timestamp"]]
    )

    graph_html = fig.to_html(full_html=False)

    return render_template(
        "correlacao_user.html",
        correlacao=round(correlacao, 4),
        graphHTML=graph_html
    )



# Rota do painel admin (exige login)
@leitura_bp.route("/admin", methods=["GET"])
def admin_page():
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))
    leituras = LeituraDAO.listar_todas()
    # transforma em dicionários simples para o template
    leituras_data = [{
        "id": l.id,
        "sensor_id": l.sensor_id,
        "tipo": l.tipo,
        "valor": getattr(l, "valor", None),
        "timestamp": str(l.timestamp)
    } for l in leituras]
    return render_template("admin_panel.html", leituras=leituras_data)



@leitura_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    usuario = request.form.get("usuario")
    senha = request.form.get("senha")

    user_hash = current_app.config.get("ADMIN_USER_HASH")
    pass_hash = current_app.config.get("ADMIN_PASSWORD_HASH")

    ok_user = check_password_hash(user_hash, usuario)
    ok_pass = check_password_hash(pass_hash, senha)

    if ok_user and ok_pass:
        session["is_admin"] = True
        return redirect(url_for("leitura_bp.admin_page"))

    flash("Usuário ou senha inválidos.", "danger")
    return redirect(url_for("leitura_bp.admin_login"))


# Logout
@leitura_bp.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logout efetuado.", "info")
    return redirect(url_for("home"))


@leitura_bp.route("/admin/delete", methods=["POST"])
def admin_delete():
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))

    sensor = request.form.get("sensor")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not sensor or not data_inicio or not data_fim:
        flash("Preencha todos os campos!", "danger")
        return redirect(url_for("leitura_bp.admin_page"))

    from datetime import datetime
    try:
        d1 = datetime.strptime(data_inicio, "%Y-%m-%d")
        d2 = datetime.strptime(data_fim, "%Y-%m-%d")
    except:
        flash("Datas inválidas!", "danger")
        return redirect(url_for("leitura_bp.admin_page"))

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
        return redirect(url_for("leitura_bp.admin_page"))

    # Apagar tudo
    for l in leituras:
        db.session.delete(l)

    db.session.commit()

    flash(f"{len(leituras)} leituras do sensor '{sensor}' foram removidas.", "success")
    return redirect(url_for("leitura_bp.admin_page"))

@leitura_bp.route("/admin/delete/<int:id>", methods=["POST"])
def admin_delete_by_id(id):
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))

    leitura = Leitura.query.get(id)

    if not leitura:
        flash("Leitura não encontrada", "danger")
        return redirect(url_for("leitura_bp.admin_page"))

    db.session.delete(leitura)
    db.session.commit()

    flash("Leitura excluída", "success")
    return redirect(url_for("leitura_bp.admin_page"))

@leitura_bp.route("/admin/delete_by_date", methods=["GET"])
def delete_by_date_page():
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))
    return render_template("admin_delete_by_date_page.html")




@leitura_bp.route("/admin/usuarios/delete/<int:id>", methods=["POST"])
def admin_delete_usuario(id):
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))

    UsuarioDAO.deletar(id)
    return redirect(url_for("leitura_bp.admin_usuarios"))


@leitura_bp.route("/admin/usuarios")
def admin_usuarios():
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))

    usuarios = UsuarioDAO.listar_aprovados()  # 🔥 aqui
    return render_template("admin_usuarios.html", usuarios=usuarios)


@leitura_bp.route("/admin/usuarios/pendentes")
def usuarios_pendentes():
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))

    usuarios = UsuarioDAO.listar_pendentes()
    return render_template("admin_pendentes.html", usuarios=usuarios)

@leitura_bp.route("/admin/usuarios/aprovar/<int:id>")
def aprovar_usuario(id):
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))

    UsuarioDAO.aprovar_usuario(id)
    return redirect(url_for("leitura_bp.usuarios_pendentes"))

@leitura_bp.route("/admin/usuarios/recusar/<int:id>")
def recusar_usuario(id):
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))

    UsuarioDAO.deletar(id)
    return redirect(url_for("leitura_bp.usuarios_pendentes"))


