from dao.banco import db
from datetime import datetime
from flask_login import UserMixin

class Admin(UserMixin):
    def __init__(self):
        self.id = 1
        self.login = 'admin'
        self.senha = '1234'

    @property
    def is_admin(self):
        return True

    def get_id(self):
        return f"admin_{self.id}"



class Usuario(db.Model, UserMixin):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    senha = db.Column(db.String(200))
    aprovado = db.Column(db.Integer, default=0)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_admin(self):
        return False

    def get_id(self):
        return f"user_{self.id}"

class ColetaFruto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer)
    nome_fruto = db.Column(db.String(60))
    frutose = db.Column(db.Float)
    peso = db.Column(db.Float)
    tamanho = db.Column(db.Float)
    acidez = db.Column(db.Float)

    timestamp = db.Column(db.DateTime, nullable=False)

