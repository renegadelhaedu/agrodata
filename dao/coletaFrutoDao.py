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
        coletas = ColetaFrutoDAO.listar_por_usuario(usuario_id)

        return sorted(list(set(
            c.nome_fruto.strip().lower()
            for c in coletas
            if c.nome_fruto
        )))