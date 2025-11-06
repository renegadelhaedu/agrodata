from dao.banco import db
from modelo.coleta import Leitura

class LeituraDAO:
    @staticmethod
    def salvar(sensor_id, tipo, valor):
        leitura = Leitura(sensor_id=sensor_id, tipo=tipo, valor=valor)
        db.session.add(leitura)
        db.session.commit()
        return leitura

    @staticmethod
    def listar_todas():
        return Leitura.query.order_by(Leitura.timestamp.desc()).all()

    @staticmethod
    def get_dados_sensor(tipo_sensor):
        return Leitura.query.filter_by(tipo=tipo_sensor).all()