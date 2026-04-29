from flask import Flask, render_template
from dao.leituraDAO import LeituraDAO
from routes.admin_bp import *
from routes.leitura_bp import leitura_bp
from config import Config
from grafico import grafico
from analise.analisador import *
import time
import utils
import threading
import random
from datetime import datetime, timedelta
from routes.usuario_bp import user_bp
from config import login_manager
from utils import TipoSensor
from banco import db


app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


login_manager.init_app(app)
login_manager.login_view = 'home'

with app.app_context():
    db.create_all()

app.register_blueprint(leitura_bp, url_prefix="/leituras")
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)




@app.route("/preencher")
def preencher_via_url():

    sensor_id = request.args.get("id")
    tipo = request.args.get("tipo")
    valor = request.args.get("valor")


    if not sensor_id or not tipo or not valor:
        return "Parâmetros obrigatórios: id, tipo, valor", 400

    tipos_validos = [t.value for t in TipoSensor]
    if tipo not in tipos_validos:
        return "Tipo inválido", 400

    try:
        valor = float(valor)
    except:
        return "Valor inválido", 400

    LeituraDAO.salvar(sensor_id, tipo, valor)

    return f"Inserido: {tipo} | {sensor_id} | {valor}", 200


def preencher():
    valor = 27
    for i in range(10):
        LeituraDAO.salvar('1', utils.TipoSensor.TEMPERATURA_AR.value, valor)
        valor = valor * 1.2
        time.sleep(20)

@app.route("/")
def home():
    return render_template('homepage.html')


@app.route('/testar')
def testar():
    threading.Thread(target=preencher).start()
    return 'ok', 200


@app.route('/ok')
def analisar():
    corre, df1, df2 = gerar_correlacao_sensor('umidade_ar','umidade_solo')
    fig = grafico.grafico_correlacao(df1, df2)

    return render_template('grafico.html',correlacao = corre, graphJSON = fig.to_html())

@app.route("/debug/leituras")
def debug_leituras():
    from dao.leituraDAO import LeituraDAO
    leituras = LeituraDAO.listar_todas()
    return "<br>".join([f"{l.tipo} - {l.getTimestamp()} - {l.getValor()}" for l in leituras])



#rota para gerar um monte de dados

@app.route("/popular")
def popular():

    sensores = [
        ("1", TipoSensor.TEMPERATURA_AR),
        ("1", TipoSensor.UMIDADE_AR),
        ("2", TipoSensor.UMIDADE_SOLO)
    ]

    agora = datetime.now()

    for i in range(100):
        for sensor_id, tipo_enum in sensores:

            # valores coerentes por tipo
            if tipo_enum == TipoSensor.TEMPERATURA_AR:
                valor = random.uniform(20, 35)

            elif tipo_enum == TipoSensor.UMIDADE_AR:
                valor = random.uniform(40, 90)

            elif tipo_enum == TipoSensor.UMIDADE_SOLO:
                valor = random.uniform(20, 80)

            leitura = Leitura(
                sensor_id=sensor_id,
                tipo=tipo_enum.value,
                valor=round(valor, 2)
            )

            # 🔥 AQUI está a correção
            leitura.timestamp = agora - timedelta(minutes=i * 10)

            db.session.add(leitura)

    db.session.commit()

    return "Banco populado com sucesso", 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
