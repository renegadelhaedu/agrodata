from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from flask_login import login_required
from dao.leituraDAO import LeituraDAO
from dao.coletaFrutoDao import ColetaFrutoDAO
from grafico import grafico
from flask_login import current_user
import plotly.express as px
import pandas as pd



leitura_bp = Blueprint("leitura_bp", __name__)

@leitura_bp.route('/receber')
def receber_dados_sensores():
    umidade_ar = request.args.get('umidade_ar')
    temperatura_ar = request.args.get('temperatura_ar')
    umidade_solo = request.args.get('umidade_solo')
    uv = request.args.get('uv')
    print(umidade_ar)
    print(temperatura_ar)
    print(umidade_solo)
    print(uv)

    LeituraDAO.salvar(sensor_id=1, tipo='temperatura_ar', valor=temperatura_ar)
    LeituraDAO.salvar(sensor_id=2,tipo='umidade_ar', valor=umidade_ar)
    LeituraDAO.salvar(sensor_id=3, tipo='umidade_solo', valor=umidade_solo)
    LeituraDAO.salvar(sensor_id=4, tipo='radiacao_uv', valor=uv)

    return jsonify("deu certo"), 201





# ===========================
# GRAFICO ÚNICO
# ===========================
@leitura_bp.route("/grafico/<string:tipo>")
@login_required
def view_grafico(tipo):
    leituras = LeituraDAO.get_dados_sensor(tipo) or []

    if not leituras:
        return render_template(
            "usuario/grafico.html",
            aviso=f"⚠ Nenhum dado para '{tipo}'",
            graphHTML=None
        )

    fig = grafico.gerar_graf(leituras, tipo)
    graph_html = fig.to_html(full_html=False)

    return render_template("usuario/grafico.html", graphHTML=graph_html)




# ===========================
# CORRELAÇÃO CLIMA x CLIMA — ROTA PRINCIPAL
# ===========================
@leitura_bp.route("/correlacaoclima", methods=["GET", "POST"])
@login_required
def pagina_correlacao_clima():

    from analise.analisador import gerar_correlacao_sensor

    # pega intervalo total de datas do banco
    leituras = LeituraDAO.listar_todas()
    datas = [l.getTimestamp() for l in leituras if l.getTimestamp()]
    data_min = min(datas).strftime("%Y-%m-%d") if datas else None
    data_max = max(datas).strftime("%Y-%m-%d") if datas else None

    if request.method == "GET":
        return render_template(
            "correlacao/usuario/correlacao_clima.html",
            data_min=data_min,
            data_max=data_max,
        )

    # POST → calcular correlação
    tipo1 = request.form.get("sensor1")
    tipo2 = request.form.get("sensor2")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")
    data_inicio_form = data_inicio
    data_fim_form = data_fim

    if not tipo1 or not tipo2:
        return render_template(
            "correlacao/usuario/correlacao_clima.html",
            aviso="Selecione os dois sensores.",
            data_min=data_min,
            data_max=data_max,
            tipo1=tipo1,
            tipo2=tipo2,
            data_inicio=data_inicio_form,
            data_fim=data_fim_form,

        )

    leituras1 = LeituraDAO.get_dados_sensor(tipo1)
    leituras2 = LeituraDAO.get_dados_sensor(tipo2)

    if not leituras1 or not leituras2:
        return render_template(
            "correlacao/usuario/correlacao_clima.html",
            aviso="⚠ Sensores sem dados suficientes.",
            data_min=data_min,
            data_max=data_max,
            tipo1=tipo1,
            tipo2=tipo2,
            data_inicio=data_inicio_form,
            data_fim=data_fim_form
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
        "correlacao/usuario/correlacao_clima.html",
        graphHTML=graph_html,
        correlacao=corre,
        data_min=data_min,
        data_max=data_max,
        tipo1=tipo1,
        tipo2=tipo2,
        data_inicio=data_inicio_form,
        data_fim=data_fim_form,

    )


@leitura_bp.route("/correlacao-fruto-usuario", methods=["GET", "POST"])
@login_required
def pagina_correlacao_fruto():

    frutos = ColetaFrutoDAO.listar_frutos_unicos(current_user.id)

    print("USUARIO LOGADO:", current_user.id)
    print("FRUTOS:", frutos)

    coletas = ColetaFrutoDAO.listar_por_usuario(current_user.id)

    for c in coletas:
        print(
            c.id,
            c.usuario_id,
            c.nome_fruto
        )
    # ============================================
    # GET
    # ============================================

    if request.method == "GET":
        return render_template(
            "correlacao/usuario/correlacao_clima_fruto.html",
            frutos=frutos
        )

    # ============================================
    # FORM
    # ============================================

    sensor = request.form.get("sensor")
    atributo = request.form.get("atributo")
    nome_fruto = request.form.get("nome_fruto")

    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not sensor or not atributo or not nome_fruto:

        return render_template(
            "correlacao/usuario/correlacao_clima_fruto.html",
            frutos=frutos,
            aviso="Preencha todos os campos."
        )

    # ============================================
    # COLETAS DO FRUTO
    # ============================================

    coletas = [
        c for c in ColetaFrutoDAO.listar_por_usuario(current_user.id)
        if c.nome_fruto == nome_fruto
    ]

    if not coletas:

        return render_template(
            "correlacao/usuario/correlacao_clima_fruto.html",
            frutos=frutos,
            aviso="Nenhuma coleta encontrada."
        )

    # ============================================
    # DATAFRAME FRUTO
    # ============================================

    dados_fruto = []

    for c in coletas:

        valor = getattr(c, atributo)

        if valor is None:
            continue

        dados_fruto.append({
            "data": c.timestamp.date(),
            "valor_fruto": float(valor)
        })

    df_fruto = pd.DataFrame(dados_fruto)

    if df_fruto.empty:

        return render_template(
            "correlacao/usuario/correlacao_clima_fruto.html",
            frutos=frutos,
            aviso="Sem dados do fruto."
        )

    # ============================================
    # LEITURAS SENSOR
    # ============================================

    leituras = LeituraDAO.get_dados_sensor(sensor)

    if not leituras:

        return render_template(
            "correlacao/usuario/correlacao_clima_fruto.html",
            frutos=frutos,
            aviso="Sensor sem leituras."
        )

    dados_sensor = []

    for l in leituras:

        timestamp = l.getTimestamp()

        if not timestamp:
            continue

        dados_sensor.append({
            "data": timestamp.date(),
            "valor_sensor": float(l.getValor())
        })

    df_sensor = pd.DataFrame(dados_sensor)

    if df_sensor.empty:

        return render_template(
            "correlacao/usuario/correlacao_clima_fruto.html",
            frutos=frutos,
            aviso="Sem dados do sensor."
        )

    # ============================================
    # FILTRO DE DATA
    # ============================================

    if data_inicio:

        data_inicio = pd.to_datetime(data_inicio).date()

        df_fruto = df_fruto[
            df_fruto["data"] >= data_inicio
        ]

        df_sensor = df_sensor[
            df_sensor["data"] >= data_inicio
        ]

    if data_fim:

        data_fim = pd.to_datetime(data_fim).date()

        df_fruto = df_fruto[
            df_fruto["data"] <= data_fim
        ]

        df_sensor = df_sensor[
            df_sensor["data"] <= data_fim
        ]

    # ============================================
    # MÉDIA DO SENSOR POR DIA
    # ============================================

    df_sensor = (
        df_sensor
        .groupby("data")["valor_sensor"]
        .mean()
        .reset_index()
    )

    # ============================================
    # MÉDIA DO FRUTO POR DIA
    # ============================================

    df_fruto = (
        df_fruto
        .groupby("data")["valor_fruto"]
        .mean()
        .reset_index()
    )

    # ============================================
    # JUNÇÃO POR DIA
    # ============================================

    df = pd.merge(
        df_fruto,
        df_sensor,
        on="data",
        how="inner"
    )

    if df.empty:

        return render_template(
            "correlacao/usuario/correlacao_clima_fruto.html",
            frutos=frutos,
            aviso="Não existem datas compatíveis."
        )

    # ============================================
    # CORRELAÇÃO
    # ============================================

    correlacao = df["valor_fruto"].corr(
        df["valor_sensor"]
    )

    # ============================================
    # GRÁFICO
    # ============================================

    # ============================================
    # GRÁFICO TEMPORAL
    # ============================================

    fig = px.line(
        df,
        x="data",
        y=["valor_sensor", "valor_fruto"],
        markers=True,
        title=f"{sensor} × {atributo}"
    )

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Valor",
        legend_title="Séries",
        template="plotly_white"
    )

    fig.update_traces(
        mode="lines+markers"
    )

    graphHTML = fig.to_html(full_html=False)
    # ============================================
    # RENDER
    # ============================================

    return render_template(
        "correlacao/usuario/correlacao_clima_fruto.html",
        frutos=frutos,
        correlacao=round(correlacao, 4),
        graphHTML=graphHTML
    )



