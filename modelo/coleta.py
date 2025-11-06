from dao.banco import db
from datetime import datetime


class Leitura(db.Model):
    __tablename__ = "leituras"

    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.String(50), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, sensor_id, tipo, valor):
        self.sensor_id = sensor_id
        self.tipo = tipo
        self.valor = valor

    def to_dict(self):
        return {
            "id": self.id,
            "sensor_id": self.sensor_id,
            "tipo": self.tipo,
            "valor": self.valor,
            "timestamp": self.timestamp.isoformat()
        }

    def getValor(self):
        return self.valor

    def setValor(self, valor):
        self.valor = valor

    def getTimestamp(self):
        return self.timestamp

    def setTimestamp(self, tempo):
        self.timestamp = tempo
