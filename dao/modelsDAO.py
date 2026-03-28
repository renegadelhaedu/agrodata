from dao.banco import db
from modelo.coleta import Leitura
from dao.modelsDB import *
from datetime import datetime

class LeituraDAO:
    @staticmethod
    def salvar(sensor_id, tipo, valor):
        leitura = Leitura(sensor_id=sensor_id, tipo=tipo, valor=valor)
        db.session.add(leitura)
        db.session.commit()
        return leitura

    @staticmethod
    def listar_todas():
        return Leitura.query.order_by(Leitura.timestamp.desc()).all()

    @staticmethod
    def get_dados_sensor(tipo_sensor):
        return Leitura.query.filter_by(tipo=tipo_sensor).all()

    # --------------------------
    # Novos métodos: atualizar / deletar
    # --------------------------
    @staticmethod
    def atualizar(id_leitura, sensor_id=None, tipo=None, valor=None, timestamp=None):
        """
        Atualiza a leitura com os campos não-nulos passados.
        Retorna a leitura atualizada ou None se não existir.
        """
        leitura = Leitura.query.get(id_leitura)
        if not leitura:
            return None

        # Atualiza campos somente se foram enviados (não None)
        if sensor_id is not None:
            leitura.sensor_id = sensor_id
        if tipo is not None:
            leitura.tipo = tipo
        if valor is not None:
            # tenta converter para float se apropriado
            try:
                leitura.valor = float(valor)
            except Exception:
                leitura.valor = valor
        if timestamp is not None:
            # tenta converter string para datetime se necessário
            if isinstance(timestamp, str):
                try:
                    leitura.timestamp = datetime.fromisoformat(timestamp)
                except Exception:
                    # se falhar, tenta deixar string (ou ignore)
                    pass
            else:
                leitura.timestamp = timestamp

        db.session.commit()
        return leitura

    @staticmethod
    def deletar(id_leitura):
        leitura = Leitura.query.get(id_leitura)
        if not leitura:
            return False
        db.session.delete(leitura)
        db.session.commit()
        return True




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

    @staticmethod
    def listar_pendentes():
        return Usuario.query.filter_by(aprovado=False).all()

    @staticmethod
    def listar_aprovados():
        return Usuario.query.filter_by(aprovado=True).all()

    @staticmethod
    def deletar(id_usuario):
        user = Usuario.query.get(id_usuario)
        if not user:
            return False
        db.session.delete(user)
        db.session.commit()
        return True

class ColetaFrutoDAO:

    @staticmethod
    def criar(usuario_id, peso, diametro, ph, glicose):
        coleta = ColetaFruto(
            usuario_id=usuario_id,
            peso=peso,
            diametro=diametro,
            ph=ph,
            glicose=glicose
        )
        db.session.add(coleta)
        db.session.commit()
        return coleta

    @staticmethod
    def listar():
        return ColetaFruto.query.all()

    @staticmethod
    def deletar(id):
        c = ColetaFruto.query.get(id)
        if not c:
            return False
        db.session.delete(c)
        db.session.commit()
        return True