from flask import Blueprint, request, jsonify, render_template
from dao.leitura_dao import LeituraDAO
from grafico import grafico

leitura_bp = Blueprint("leitura_bp", __name__)

@leitura_bp.route("/", methods=["POST"])
def receber_leitura():
    dados = request.get_json()
    if not dados or not all(k in dados for k in ("sensor_id", "tipo", "valor")):
        return jsonify({"erro": "JSON inválido ou incompleto"}), 400

    leitura = LeituraDAO.salvar(
        sensor_id=dados["sensor_id"],
        tipo=dados["tipo"],
        valor=dados["valor"]
    )
    return jsonify(leitura.to_dict()), 201


@leitura_bp.route("/", methods=["GET"])
def listar_leituras():
    leituras = LeituraDAO.listar_todas()
    return jsonify([l.to_dict() for l in leituras])


@leitura_bp.route("/grafico/<string:tipo>")
def view_grafico(tipo):
    leituras = LeituraDAO.get_dados_sensor(tipo)
    graphJSON = grafico.gerar_graf(leituras, tipo)

    return render_template('grafico.html', graphJSON=graphJSON.to_html())
    #return 'ok'



