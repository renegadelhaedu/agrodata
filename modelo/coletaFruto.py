from banco import db

class ColetaFruto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer)
    nome_fruto = db.Column(db.String(60))
    frutose = db.Column(db.Float)
    peso = db.Column(db.Float)
    tamanho = db.Column(db.Float)
    acidez = db.Column(db.Float)

    timestamp = db.Column(db.DateTime, nullable=False)

