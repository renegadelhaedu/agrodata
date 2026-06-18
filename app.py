import os
from flask import Flask
from routes.admin_bp import *
from routes.leitura_bp import leitura_bp
from config import Config
from grafico import grafico
from analise.analisador import *
import random
from datetime import datetime, timedelta
from routes.usuario_bp import user_bp
from config import login_manager
from utils import TipoSensor, TipoFruta
from banco import db
from modelo.coletaFruto import ColetaFruto

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




@app.route("/")
def home():
    return render_template('homepage.html')




#rota para gerar um monte de dados


@app.route("/popular")
def popular():


    sensores = [
        ("1", TipoSensor.TEMPERATURA_AR),
        ("2", TipoSensor.UMIDADE_AR),
        ("3", TipoSensor.UMIDADE_SOLO),
        ("4", TipoSensor.RADIACAO)
    ]

    frutos = [
        TipoFruta.ACEROLA,
        TipoFruta.MANGA,
        TipoFruta.COCO,
        TipoFruta.CAJU
    ]

    agora = datetime.now()

    # =========================================
    # SENSORES
    # =========================================

    # =========================================
    # SENSORES
    # =========================================

    # =========================================
    # SENSORES
    # =========================================

    for i in range(200):

        base = agora - timedelta(days=i)

        hora = random.randint(0, 23)
        minuto = random.randint(0, 59)

        data_sensor = base.replace(
            hour=hora,
            minute=minuto,
            second=0,
            microsecond=0
        )

        for sensor_id, tipo_enum in sensores:

            if tipo_enum == TipoSensor.TEMPERATURA_AR:
                valor = random.uniform(20, 35)

            elif tipo_enum == TipoSensor.UMIDADE_AR:
                valor = random.uniform(40, 90)

            elif tipo_enum == TipoSensor.UMIDADE_SOLO:
                valor = random.uniform(20, 80)

            elif tipo_enum == TipoSensor.RADIACAO:
                valor = random.uniform(15, 87)

            leitura = Leitura(
                sensor_id=sensor_id,
                tipo=tipo_enum.value,
                valor=round(valor, 2)
            )

            leitura.timestamp = data_sensor

            db.session.add(leitura)

    # =========================================
    # FRUTOS
    # =========================================

    for i in range(200):

        base = agora - timedelta(days=i)

        for fruto in frutos:

            # horário diferente do sensor
            hora = random.randint(0, 23)
            minuto = random.randint(0, 59)

            data_fruto = base.replace(
                hour=hora,
                minute=minuto,
                second=0,
                microsecond=0
            )

            coleta = ColetaFruto(
                usuario_id=1,
                nome_fruto=fruto.value,

                frutose=round(random.uniform(5, 20), 2),

                peso=round(random.uniform(100, 900), 2),

                tamanho=round(random.uniform(4, 20), 2),

                acidez=round(random.uniform(2, 7), 2)
            )

            coleta.timestamp = data_fruto

            db.session.add(coleta)

    db.session.commit()

    return "Banco populado com sucesso", 200



@app.errorhandler(404)
def pagina_nao_encontrada(error):
    print("pagina nao encontrada", error)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
