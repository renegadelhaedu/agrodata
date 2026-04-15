from modelo.modelsDB import *


class ColetaFrutoDAO:

    @staticmethod
    def criar(usuario_id,nome_fruto, frutose, peso, tamanho, acidez, timestamp):
        coleta = ColetaFruto(
            usuario_id=usuario_id,
            nome_fruto=nome_fruto,
            frutose=frutose,
            peso=peso,
            tamanho=tamanho,
            acidez=acidez,
            timestamp=timestamp
        )
        db.session.add(coleta)
        db.session.commit()
        return coleta

    @staticmethod
    def listar_por_usuario(usuario_id):
        return ColetaFruto.query.filter_by(usuario_id=usuario_id).all()

    @staticmethod
    def listar_por_fruto(nome_fruto):
        return ColetaFruto.query.filter_by(nome_fruto=nome_fruto).all()

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