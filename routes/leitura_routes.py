from flask import Blueprint, request, jsonify, render_template
from dao.leitura_dao import LeituraDAO
from grafico import grafico
import pandas as pd

leitura_bp = Blueprint("leitura_bp", __name__)


# ============================================
# ROTAS PRINCIPAIS DE LEITURAS
# ============================================

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


# ============================================
# EXIBIR GRÁFICOS INDIVIDUAIS
# ============================================

@leitura_bp.route("/grafico/<string:tipo>")
def view_grafico(tipo):
    leituras = LeituraDAO.get_dados_sensor(tipo)
    graphJSON = grafico.gerar_graf(leituras, tipo)
    return render_template("grafico.html", graphJSON=graphJSON.to_html())


# ============================================
# FUNÇÃO DE UTILIDADE PARA NORMALIZAR DADOS
# ============================================

def preparar_dataframe(leituras, data_inicio=None, data_fim=None):
    df = pd.DataFrame([{"valor": l.getValor(), "timestamp": l.getTimestamp()} for l in leituras])
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    if data_inicio and data_fim:
        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim) + pd.Timedelta(days=1)
        df = df[(df["timestamp"] >= data_inicio) & (df["timestamp"] <= data_fim)]

    return df


# ============================================
# 1️⃣ CORRELAÇÃO ENTRE SENSORES CLIMÁTICOS
# ============================================

@leitura_bp.route("/correlacao/clima", methods=["GET", "POST"])
def corre_clima():
    from analise.analisador import gerar_correlacao_sensor

    if request.method == "POST":
        s1 = request.form.get("sensor1")
        s2 = request.form.get("sensor2")
        di = request.form.get("data_inicio")
        df = request.form.get("data_fim")

        df1 = preparar_dataframe(LeituraDAO.get_dados_sensor(s1), di, df)
        df2 = preparar_dataframe(LeituraDAO.get_dados_sensor(s2), di, df)

        if df1.empty or df2.empty:
            return render_template("correlacao_clima.html", aviso="⚠️ Sem dados no intervalo selecionado.")

        correlacao, _, _ = gerar_correlacao_sensor(s1, s2)
        fig = grafico.grafico_correlacao(df1, df2)

        return render_template("correlacao_clima.html",
                               correlacao=correlacao,
                               graphJSON=fig.to_html(),
                               tipo1=s1, tipo2=s2)

    return render_template("correlacao_clima.html")



# ============================================
# 2️⃣ CORRELAÇÃO CLIMA × FRUTO
# ============================================

@leitura_bp.route("/correlacao/clima-fruto", methods=["GET", "POST"])
def corre_clima_fruto():
    from analise.analisador import gerar_correlacao_sensor

    if request.method == "POST":
        clima = request.form.get("sensor1")
        fruto = request.form.get("sensor2")
        di = request.form.get("data_inicio")
        df = request.form.get("data_fim")

        df1 = preparar_dataframe(LeituraDAO.get_dados_sensor(clima), di, df)
        df2 = preparar_dataframe(LeituraDAO.get_dados_sensor(fruto), di, df)

        if df1.empty or df2.empty:
            return render_template("correlacao_clima_fruto.html", aviso="⚠️ Sem dados no período.")

        correlacao, _, _ = gerar_correlacao_sensor(clima, fruto)
        fig = grafico.grafico_correlacao(df1, df2)

        return render_template("correlacao_clima_fruto.html",
                               correlacao=correlacao,
                               graphJSON=fig.to_html(),
                               tipo1=clima, tipo2=fruto)

    return render_template("correlacao_clima_fruto.html")



# ============================================
# 3️⃣ CORRELAÇÃO ENTRE SENSORES DE FRUTOS
# ============================================

@leitura_bp.route("/correlacao/frutos", methods=["GET", "POST"])
def corre_frutos():
    from analise.analisador import gerar_correlacao_sensor

    if request.method == "POST":
        s1 = request.form.get("sensor1")
        s2 = request.form.get("sensor2")
        di = request.form.get("data_inicio")
        df = request.form.get("data_fim")

        df1 = preparar_dataframe(LeituraDAO.get_dados_sensor(s1), di, df)
        df2 = preparar_dataframe(LeituraDAO.get_dados_sensor(s2), di, df)

        if df1.empty or df2.empty:
            return render_template("correlacao_frutos.html", aviso="⚠️ Sem dados suficientes.")

        correlacao, _, _ = gerar_correlacao_sensor(s1, s2)
        fig = grafico.grafico_correlacao(df1, df2)

        return render_template("correlacao_frutos.html",
                               correlacao=correlacao,
                               graphJSON=fig.to_html(),
                               tipo1=s1, tipo2=s2)

    return render_template("correlacao_frutos.html")


# ============================================
# ROTA EXTRA – LISTAR TODAS AS DATAS
# ============================================

@leitura_bp.route("/datas")
def listar_datas():
    leituras = LeituraDAO.listar_todas()
    datas = sorted({str(l.getTimestamp()) for l in leituras if l.getTimestamp()})
    return "<br>".join(datas)
