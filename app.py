from flask import Flask, render_template
from dao.banco import db
from routes.leitura_routes import leitura_bp
from config import Config
from grafico import grafico
from dao.leitura_dao import *
from analise.analisador import *
import time
import utils
import threading

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

app.register_blueprint(leitura_bp, url_prefix="/leituras")

def preencher():
    valor = 27
    for i in range(10):
        LeituraDAO.salvar('1', utils.TipoSensor.TEMPERATURA_AR.value, valor)
        valor = valor * 1.2
        time.sleep(20)

@app.route("/")
def home():
    return render_template('painel.html')


@app.route('/testar')
def testar():
    threading.Thread(preencher()).start()
    return 'ok', 200


@app.route('/ok')
def analisar():
    corre, df1, df2 = gerar_correlacao_sensor('umidade_ar','umidade_solo')
    fig = grafico.grafico_correlacao(df1, df2)

    return render_template('grafico.html',correlacao = corre, graphJSON = fig.to_html())

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
