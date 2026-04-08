from dao.banco import db
from modelo.leitura import Leitura
from dao.modelsDB import *
from datetime import datetime


class ColetaFrutoDAO:

    @staticmethod
    def criar(usuario_id, frutose, peso, tamanho, acidez):
        coleta = ColetaFruto(
            usuario_id=usuario_id,
            frutose=frutose,
            peso=peso,
            tamanho=tamanho,
            acidez=acidez
        )
        db.session.add(coleta)
        db.session.commit()
        return coleta

    @staticmethod
    def listar_por_usuario(usuario_id):
        return ColetaFruto.query.filter_by(usuario_id=usuario_id).all()

    @staticmethod
    def listar_todas():
        return ColetaFruto.query.all()

    @staticmethod
    def deletar(id):
        coleta = ColetaFruto.query.get(id)
        if not coleta:
            return False
        db.session.delete(coleta)
        db.session.commit()
        return True