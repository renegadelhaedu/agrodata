from dao.banco import db
from modelo.leitura import Leitura
from dao.modelsDB import *
from datetime import datetime


from dao.banco import db
from dao.modelsDB import Usuario


class UsuarioDAO:

    # =========================
    # CADASTRO
    # =========================
    @staticmethod
    def cadastrar(nome, email, senha):
        usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha,
            aprovado=False
        )
        db.session.add(usuario)
        db.session.commit()
        return usuario

    # =========================
    # BUSCAR
    # =========================
    @staticmethod
    def buscar_por_email(email):
        return Usuario.query.filter_by(email=email).first()

    @staticmethod
    def buscar_por_id(id_usuario):
        return Usuario.query.get(id_usuario)

    # =========================
    # LOGIN
    # =========================
    @staticmethod
    def autenticar(email, senha):
        return Usuario.query.filter_by(email=email, senha=senha).first()

    # =========================
    # LISTAGENS
    # =========================
    @staticmethod
    def listar_todos():
        return Usuario.query.order_by(Usuario.id.desc()).all()

    @staticmethod
    def listar_pendentes():
        return Usuario.query.filter_by(aprovado=False).all()

    @staticmethod
    def listar_aprovados():
        return Usuario.query.filter_by(aprovado=True).all()

    # =========================
    # APROVAR
    # =========================
    @staticmethod
    def aprovar_usuario(id_usuario):
        user = Usuario.query.get(id_usuario)
        if not user:
            return False

        user.aprovado = True
        db.session.commit()
        return True

    # =========================
    # RECUSAR (DELETE)
    # =========================
    @staticmethod
    def deletar(id_usuario):
        user = Usuario.query.get(id_usuario)

        if not user:
            return False

        db.session.delete(user)
        db.session.commit()
        return True