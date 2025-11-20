from flask import Blueprint, request, jsonify, render_template
from dao.leitura_dao import LeituraDAO
from grafico import grafico
import pandas as pd

leitura_bp = Blueprint("leitura_bp", __name__)

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


@leitura_bp.route("/grafico/<string:tipo>")
def view_grafico(tipo):
    leituras = LeituraDAO.get_dados_sensor(tipo)
    graphJSON = grafico.gerar_graf(leituras, tipo)

    return render_template('grafico.html', graphJSON=graphJSON.to_html())


@leitura_bp.route("/correlacao/<string:tipo1>/<string:tipo2>")
def view_correlacao(tipo1, tipo2):
    from analise.analisador import gerar_correlacao_sensor

    corre, df1, df2 = gerar_correlacao_sensor(tipo1, tipo2)
    fig = grafico.grafico_correlacao(df1, df2)

    return render_template('grafico.html', correlacao=corre, graphJSON=fig.to_html())

@leitura_bp.route("/correlacao", methods=["GET", "POST"])
def pagina_correlacao():
    from analise.analisador import gerar_correlacao_sensor

    leituras = LeituraDAO.listar_todas()
    datas = [l.getTimestamp() for l in leituras if l.getTimestamp()]
    data_min = min(datas).strftime("%Y-%m-%d") if datas else None
    data_max = max(datas).strftime("%Y-%m-%d") if datas else None

    if request.method == "POST":
        tipo1 = request.form.get("sensor1")
        tipo2 = request.form.get("sensor2")
        data_inicio = request.form.get("data_inicio")
        data_fim = request.form.get("data_fim")

        leituras1 = LeituraDAO.get_dados_sensor(tipo1)
        leituras2 = LeituraDAO.get_dados_sensor(tipo2)

        df1 = pd.DataFrame([{"valor": l.getValor(), "timestamp": l.getTimestamp()} for l in leituras1])
        df2 = pd.DataFrame([{"valor": l.getValor(), "timestamp": l.getTimestamp()} for l in leituras2])

        df1["timestamp"] = pd.to_datetime(df1["timestamp"])
        df2["timestamp"] = pd.to_datetime(df2["timestamp"])

        if data_inicio and data_fim:
            data_inicio = pd.to_datetime(data_inicio)
            data_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=1)  # inclui fim do dia
            df1 = df1[(df1["timestamp"] >= data_inicio) & (df1["timestamp"] <= data_fim)]
            df2 = df2[(df2["timestamp"] >= data_inicio) & (df2["timestamp"] <= data_fim)]

        # Se após o filtro estiver vazio, evita erro
        if df1.empty or df2.empty:
            return render_template(
                "correlacao.html",
                aviso="⚠️ Nenhum dado encontrado no intervalo selecionado.",
                data_min=data_min,
                data_max=data_max,
                tipo1=tipo1,
                tipo2=tipo2
            )

        # Calcular correlação e gráfico
        corre, _, _ = gerar_correlacao_sensor(tipo1, tipo2)
        fig = grafico.grafico_correlacao(df1, df2)
        graph_html = fig.to_html(full_html=False)

        return render_template(
            "correlacao.html",
            graphJSON=graph_html,
            correlacao=corre,
            tipo1=tipo1,
            tipo2=tipo2,
            data_inicio=data_inicio.strftime("%Y-%m-%d"),
            data_fim=(data_fim - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
            data_min=data_min,
            data_max=data_max
        )
    return render_template("correlacao.html", data_min=data_min, data_max=data_max)


@leitura_bp.route("/datas")
def listar_datas():
    leituras = LeituraDAO.listar_todas()
    datas = sorted({str(l.getTimestamp()) for l in leituras if l.getTimestamp()})
    return "<br>".join(datas)
