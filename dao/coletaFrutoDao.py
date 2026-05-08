from modelo.coletaFruto import *


class ColetaFrutoDAO:

    @staticmethod
    def criar(usuario_id, nome_fruto, frutose, peso, tamanho, acidez, timestamp):
        coleta = ColetaFruto(
            usuario_id=usuario_id,
            nome_fruto=nome_fruto.strip().lower(),
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
    def listar_frutos_unicos(usuario_id):
        resultados = (
            db.session.query(ColetaFruto.nome_fruto)
            .filter(ColetaFruto.usuario_id == usuario_id)
            .distinct()
            .all()
        )

        return [r[0] for r in resultados]

    @staticmethod
    def deletar(id_coleta, usuario_id):

        coleta = ColetaFruto.query.filter_by(
            id=id_coleta,
            usuario_id=usuario_id
        ).first()

        if not coleta:
            return False

        db.session.delete(coleta)
        db.session.commit()

        return True