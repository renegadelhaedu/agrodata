from modelo.leitura import Leitura
from modelo.usuario import *
from datetime import datetime
from utils import TipoSensor


class LeituraDAO:
    @staticmethod
    def salvar(sensor_id, tipo, valor):

        tipos_validos = [t.value for t in TipoSensor]

        if tipo not in tipos_validos:
            raise ValueError("Tipo inválido")

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

    @staticmethod
    def filtrar(sensor_id=None, tipo=None, valor_min=None, valor_max=None, data_inicio=None, data_fim=None):
        query = Leitura.query

        if sensor_id:
            query = query.filter(Leitura.sensor_id == sensor_id)

        if tipo:
            query = query.filter(Leitura.tipo == tipo)

        if valor_min is not None:
            query = query.filter(Leitura.valor >= valor_min)

        if valor_max is not None:
            query = query.filter(Leitura.valor <= valor_max)

        if data_inicio:
            query = query.filter(Leitura.timestamp >= data_inicio)

        if data_fim:
            query = query.filter(Leitura.timestamp <= data_fim)

        return query.order_by(Leitura.timestamp.desc()).all()

    @staticmethod
    def filtrar_por_periodo(data_inicio, data_fim, tipo):

        query = Leitura.query

        if tipo:
            query = query.filter(Leitura.tipo == tipo)

        if data_inicio:
            query = query.filter(Leitura.timestamp >= data_inicio)

        if data_fim:
            query = query.filter(Leitura.timestamp <= data_fim)

        return query.order_by(Leitura.timestamp.asc()).all()




