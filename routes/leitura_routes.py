from flask import Blueprint, request, jsonify, render_template
from dao.leitura_dao import LeituraDAO
from grafico import grafico
from analise.analisador import gerar_correlacao_sensor
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
    return render_template("grafico.html", graphJSON=graphJSON.to_html())


@leitura_bp.route("/correlacao", methods=["GET", "POST"])
def pagina_correlacao():
    sensores_clima = [
        ("temperatura_ar", "🌡️ Temperatura do Ar"),
        ("umidade_ar", "💧 Umidade do Ar"),
        ("umidade_solo", "🌱 Umidade do Solo"),
        ("rad_solar", "☀️ Radiação Solar")
    ]
    sensores_fruto = [
        ("medida_glicose", "🍈 Medida de Glicose"),
        ("ph_suco", "⚗️ pH do Suco"),
        ("peso_fruto", "⚖️ Peso do Fruto"),
        ("diametro_fruto", "📏 Diâmetro do Fruto")
    ]

    leituras = LeituraDAO.listar_todas()
    datas = [l.getTimestamp() for l in leituras if l.getTimestamp()]
    data_min = min(datas).strftime("%Y-%m-%d") if datas else None
    data_max = max(datas).strftime("%Y-%m-%d") if datas else None

    if request.method == "POST":
        sensor_clima = request.form.get("sensor1")
        sensor_fruto = request.form.get("sensor2")
        data_inicio = request.form.get("data_inicio")
        data_fim = request.form.get("data_fim")

        if not all([sensor_clima, sensor_fruto, data_inicio, data_fim]):
            return render_template(
                "correlacao.html",
                aviso="⚠️ Preencha todos os campos antes de continuar.",
                sensores_clima=sensores_clima,
                sensores_fruto=sensores_fruto,
                data_min=data_min,
                data_max=data_max
            )

        leituras1 = LeituraDAO.get_dados_sensor(sensor_clima)
        leituras2 = LeituraDAO.get_dados_sensor(sensor_fruto)

        df1 = pd.DataFrame([{"valor": l.getValor(), "timestamp": l.getTimestamp()} for l in leituras1])
        df2 = pd.DataFrame([{"valor": l.getValor(), "timestamp": l.getTimestamp()} for l in leituras2])

        if df1.empty or df2.empty:
            return render_template(
                "correlacao.html",
                aviso="⚠️ Não há dados suficientes para realizar a correlação.",
                sensores_clima=sensores_clima,
                sensores_fruto=sensores_fruto,
                data_min=data_min,
                data_max=data_max
            )

        df1["timestamp"] = pd.to_datetime(df1["timestamp"])
        df2["timestamp"] = pd.to_datetime(df2["timestamp"])
        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=1)

        df1 = df1[(df1["timestamp"] >= data_inicio) & (df1["timestamp"] <= data_fim)]
        df2 = df2[(df2["timestamp"] >= data_inicio) & (df2["timestamp"] <= data_fim)]

        if df1.empty or df2.empty:
            return render_template(
                "correlacao.html",
                aviso="⚠️ Nenhum dado encontrado no intervalo selecionado.",
                sensores_clima=sensores_clima,
                sensores_fruto=sensores_fruto,
                data_min=data_min,
                data_max=data_max
            )

        corre, _, _ = gerar_correlacao_sensor(sensor_clima, sensor_fruto)
        fig = grafico.grafico_correlacao(df1, df2)
        graph_html = fig.to_html(full_html=False)

        return render_template(
            "correlacao.html",
            graphJSON=graph_html,
            correlacao=corre,
            sensores_clima=sensores_clima,
            sensores_fruto=sensores_fruto,
            data_inicio=data_inicio.strftime("%d/%m/%Y"),
            data_fim=(data_fim - pd.Timedelta(days=1)).strftime("%d/%m/%Y"),
            data_min=data_min,
            data_max=data_max,
            sensor_clima=sensor_clima,
            sensor_fruto=sensor_fruto
        )

    return render_template(
        "correlacao.html",
        sensores_clima=sensores_clima,
        sensores_fruto=sensores_fruto,
        data_min=data_min,
        data_max=data_max
    )


@leitura_bp.route("/datas")
def listar_datas():
    leituras = LeituraDAO.listar_todas()
    datas = sorted({str(l.getTimestamp()) for l in leituras if l.getTimestamp()})
    return "<br>".join(datas)
