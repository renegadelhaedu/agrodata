from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from flask_login import login_required

from dao.leituraDAO import LeituraDAO
from dao.coletaFrutoDao import ColetaFrutoDAO
from decorators import admin_required
from grafico import grafico
import pandas as pd


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


@login_required
@admin_required
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
@login_required
@admin_required
@leitura_bp.route("/grafico/<string:tipo>")
def view_grafico(tipo):
    leituras = LeituraDAO.get_dados_sensor(tipo) or []

    if not leituras:
        return render_template("grafico.html", aviso=f"⚠ Nenhum dado para '{tipo}'", graphHTML=None)

    fig = grafico.gerar_graf(leituras, tipo)
    graph_html = fig.to_html(full_html=False)

    return render_template("grafico.html", graphHTML=graph_html)


# ===========================
# CORRELAÇÃO CLIMA x CLIMA — ROTA PRINCIPAL
# ===========================
@leitura_bp.route("/correlacaoclima", methods=["GET", "POST"])
def pagina_correlacao_clima():

    from analise.analisador import gerar_correlacao_sensor

    # pega intervalo total de datas do banco
    leituras = LeituraDAO.listar_todas()
    datas = [l.getTimestamp() for l in leituras if l.getTimestamp()]
    data_min = min(datas).strftime("%Y-%m-%d") if datas else None
    data_max = max(datas).strftime("%Y-%m-%d") if datas else None

    if request.method == "GET":
        return render_template(
            "correlacao/correlacao_clima.html",
            data_min=data_min,
            data_max=data_max,
        )

    # POST → calcular correlação
    tipo1 = request.form.get("sensor1")
    tipo2 = request.form.get("sensor2")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not tipo1 or not tipo2:
        return render_template(
            "correlacao/correlacao_clima.html",
            aviso="Selecione os dois sensores.",
            data_min=data_min,
            data_max=data_max,

        )

    leituras1 = LeituraDAO.get_dados_sensor(tipo1)
    leituras2 = LeituraDAO.get_dados_sensor(tipo2)

    if not leituras1 or not leituras2:
        return render_template(
            "correlacao/correlacao_clima.html",
            aviso="⚠ Sensores sem dados suficientes.",
            data_min=data_min,
            data_max=data_max
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
        "correlacao/correlacao_clima.html",
        graphHTML=graph_html,
        correlacao=corre,
        data_min=data_min,
        data_max=data_max,

    )



@leitura_bp.route("/correlacao-fruto-usuario", methods=["GET", "POST"])
def pagina_correlacao_fruto():



    if request.method == "GET":
        return render_template("correlacao/correlacao_clima_fruto.html")

    sensor = request.form.get("sensor")
    atributo = request.form.get("atributo")
    nome_fruto = request.form.get("nome_fruto")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not sensor or not atributo:
        return render_template(
            "correlacao_fruto_usuario.html",
            aviso="Selecione sensor e atributo."
        )

    # 🔹 COLETAS
    coletas = ColetaFrutoDAO.listar_por_usuario(id)

    if nome_fruto:
        coletas = [c for c in coletas if c.nome_fruto == nome_fruto]

    if not coletas:
        return render_template(
            "correlacao_fruto_usuario.html",
            aviso="Sem coletas encontradas."
        )

    df_fruto = pd.DataFrame([
        {
            "timestamp": c.timestamp,
            "valor_fruto": getattr(c, atributo)
        }
        for c in coletas if getattr(c, atributo) is not None
    ])

    if df_fruto.empty:
        return render_template(
            "correlacao_fruto_usuario.html",
            aviso="Sem dados válidos de fruto."
        )

    df_fruto["timestamp"] = pd.to_datetime(df_fruto["timestamp"])

    # 🔹 SENSOR
    leituras = LeituraDAO.get_dados_sensor(sensor)

    df_sensor = pd.DataFrame([
        {
            "timestamp": l.getTimestamp(),
            "valor_sensor": l.getValor()
        }
        for l in leituras
    ])

    df_sensor["timestamp"] = pd.to_datetime(df_sensor["timestamp"])

    # 🔹 FILTRO DATA
    if data_inicio and data_fim:
        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim)

        df_fruto = df_fruto[
            (df_fruto["timestamp"] >= data_inicio) &
            (df_fruto["timestamp"] <= data_fim)
        ]

        df_sensor = df_sensor[
            (df_sensor["timestamp"] >= data_inicio) &
            (df_sensor["timestamp"] <= data_fim)
        ]

    # 🔹 ALINHAMENTO TEMPORAL (CRÍTICO)
    df_merged = pd.merge_asof(
        df_fruto.sort_values("timestamp"),
        df_sensor.sort_values("timestamp"),
        on="timestamp",
        direction="nearest"
    )

    df_merged = df_merged.dropna()

    if df_merged.empty:
        return render_template(
            "correlacao_fruto_usuario.html",
            aviso="Sem dados compatíveis para correlação."
        )

    # 🔹 CORRELAÇÃO
    correlacao = df_merged["valor_fruto"].corr(df_merged["valor_sensor"])

    # 🔹 GRÁFICO
    import plotly.express as px

    fig = px.scatter(
        df_merged,
        x="valor_sensor",
        y="valor_fruto",
        title="Correlação Sensor × Fruto"
    )

    graphHTML = fig.to_html(full_html=False)

    return render_template(
        "correlacao_fruto_usuario.html",
        correlacao=round(correlacao, 4),
        graphHTML=graphHTML
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


@leitura_bp.route("/correlacao/climaFruto", methods=["GET"])
def corre_clima_fruto_page():
    return render_template("correlacao_clima_fruto.html")


@leitura_bp.route("/correlacao/user", methods=["GET", "POST"])
def correlacao_usuario():

    from modelo.coletaFruto import ColetaFruto
    import pandas as pd

    # 🔒 segurança
    if not session.get("usuario_logado"):
        return redirect(url_for("user_bp.login"))

    if request.method == "GET":
        return render_template("correlacao/correlacao_user.html")

    # =========================
    # PEGAR DADOS DO FORM
    # =========================
    sensor = request.form.get("sensor")
    atributo = request.form.get("atributo")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not sensor or not atributo:
        return render_template("correcorrelacao_user.html", aviso="Preencha todos os campos")

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
