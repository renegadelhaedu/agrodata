from banco import db
from datetime import datetime
from flask_login import UserMixin



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