from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash, current_app
from dao.leitura_dao import LeituraDAO
from grafico import grafico
import pandas as pd

leitura_bp = Blueprint("leitura_bp", __name__)

# ===========================
# API LEITURAS BÁSICA
# ===========================
@leitura_bp.route("/", methods=["POST"])
def receber_leitura():
    dados = request.get_json()
    if not dados or not all(k in dados for k in ("sensor_id", "tipo", "valor")):
        return jsonify({"erro": "JSON inválido ou incompleto"}), 400

    leitura = LeituraDAO.salvar(
        sensor_id=dados["sensor_id"],
        tipo=dados["tipo"],
        valor=dados["valor"]
    )
    return jsonify(leitura.to_dict()), 201


@leitura_bp.route("/", methods=["GET"])
def listar_leituras():
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


@leitura_bp.route("/correlacao/clima_fruto", methods=["GET"])
def corre_clima_fruto_page():
    return render_template("correlacao_clima_fruto.html")



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


# Login admin (GET mostra form, POST valida)
@leitura_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")
    senha = request.form.get("senha")
    if senha and senha == current_app.config.get("ADMIN_PASSWORD"):
        session["is_admin"] = True
        flash("Autenticado como admin.", "success")
        return redirect(url_for("leitura_bp.admin_page"))
    flash("Senha inválida.", "danger")
    return redirect(url_for("leitura_bp.admin_login"))


# Logout
@leitura_bp.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    flash("Logout efetuado.", "info")
    return redirect(url_for("home"))


# Delete (POST)
@leitura_bp.route("/admin/delete/<int:id>", methods=["POST"])
def admin_delete(id):
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))
    success = LeituraDAO.deletar(id)
    if success:
        flash("Leitura removida.", "success")
    else:
        flash("Não foi possível remover (id não encontrado).", "danger")
    return redirect(url_for("leitura_bp.admin_page"))


# Edit (GET mostra form, POST aplica)
@leitura_bp.route("/admin/edit/<int:id>", methods=["GET", "POST"])
def admin_edit(id):
    if not session.get("is_admin"):
        return redirect(url_for("leitura_bp.admin_login"))

    # buscar leitura via DAO
    leituras = LeituraDAO.listar_todas()
    leitura = next((l for l in leituras if l.id == id), None)
    if not leitura:
        flash("Leitura não encontrada.", "danger")
        return redirect(url_for("leitura_bp.admin_page"))

    if request.method == "GET":
        return render_template("admin_edit.html", leitura={
            "id": leitura.id,
            "sensor_id": leitura.sensor_id,
            "tipo": leitura.tipo,
            "valor": getattr(leitura, "valor", ""),
            "timestamp": str(leitura.timestamp)
        })

    # POST -> aplica atualização
    sensor_id = request.form.get("sensor_id")
    tipo = request.form.get("tipo")
    valor = request.form.get("valor")
    timestamp = request.form.get("timestamp")

    updated = LeituraDAO.atualizar(id, sensor_id=sensor_id, tipo=tipo, valor=valor, timestamp=timestamp)
    if updated:
        flash("Leitura atualizada.", "success")
    else:
        flash("Falha ao atualizar.", "danger")
    return redirect(url_for("leitura_bp.admin_page"))
