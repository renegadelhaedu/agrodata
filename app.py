from flask import Flask, render_template
from dao.banco import db
from routes.leitura_routes import leitura_bp
from config import Config
from grafico import grafico
from dao.leitura_dao import *
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
    valor = 30
    for i in range(10):
        LeituraDAO.salvar('1', utils.TipoSensor.UMIDADE_AR.value, valor)
        valor = valor * 1.02
        time.sleep(20)

@app.route("/")
def home():
    return render_template('painel.html')



@app.route('/testar')
def testar():
    threading.Thread(preencher()).start()
    return 'ok', 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
