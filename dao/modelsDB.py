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
    __tablename__ = "coletas_frutos"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))

    peso = db.Column(db.Float)
    diametro = db.Column(db.Float)
    ph = db.Column(db.Float)
    glicose = db.Column(db.Float)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)