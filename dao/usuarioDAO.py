from dao.banco import db
from modelo.leitura import Leitura
from dao.modelsDB import *
from datetime import datetime


class UsuarioDAO:

    @staticmethod
    def cadastrar(nome, email, senha):
        usuario = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(usuario)
        db.session.commit()
        return usuario

    @staticmethod
    def buscar_por_email(email):
        return Usuario.query.filter_by(email=email).first()

    @staticmethod
    def autenticar(email, senha):
        return Usuario.query.filter_by(email=email, senha=senha).first()

    @staticmethod
    def listar_todos():
        return Usuario.query.all()

    @staticmethod
    def aprovar_usuario(id_usuario):
        user = Usuario.query.get(id_usuario)
        if not user:
            return False
        user.aprovado = 1
        db.session.commit()
        return True