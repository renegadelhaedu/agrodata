from dao.banco import db
from datetime import datetime

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(200))
    aprovado = db.Column(db.Integer, default=0)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

class ColetaFruto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer)
    nome_fruto = db.Column(db.String(60))
    frutose = db.Column(db.Float)
    peso = db.Column(db.Float)
    tamanho = db.Column(db.Float)
    acidez = db.Column(db.Float)

    timestamp = db.Column(db.DateTime, nullable=False)