from flask import *
from dao.usuarioDAO import *
from dao.leituraDAO import *
from dao.coletaFrutoDao import ColetaFrutoDAO
from utils import lista_frutos
from routes.leitura_routes import leitura_bp
from flask_login import login_user, logout_user, login_required, current_user

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        user = UsuarioDAO.autenticar(email, senha)

        if not user:
            flash("Email ou senha inválidos")
            return redirect(url_for("user_bp.login"))

        if not user.aprovado:
            flash("Usuário aguardando aprovação do administrador")
            return redirect(url_for("user_bp.login"))

        login_user(user)

        flash("Login com sucesso")
        return redirect(url_for("user_bp.painel_usuario"))

    return render_template("login_user.html")

@login_required
@user_bp.route("/painel")
def painel_usuario():
    leituras = LeituraDAO.listar_todas()
    return render_template("painel.html", leituras=leituras)



@user_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        if UsuarioDAO.buscar_por_email(email):
            flash("Email já cadastrado")
            return redirect("/")

        UsuarioDAO.cadastrar(nome, email, senha)
        flash("Cadastro realizado. Aguarde aprovação.")
        return redirect("/login")

    return render_template("cadastro.html")

@login_required
@user_bp.route("/user", methods=["GET"])
def user_list():
    leituras = LeituraDAO.listar_todas()
    # transforma em dicionários simples para o template
    leituras_data = [{
        "id": l.id,
        "sensor_id": l.sensor_id,
        "tipo": l.tipo,
        "valor": getattr(l, "valor", None),
        "timestamp": str(l.timestamp)
    } for l in leituras]
    return render_template("user_list.html", leituras=leituras_data)


@user_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@login_required
@user_bp.route("/coleta", methods=["GET", "POST"])
def cadastrar_coleta():

    if request.method == "POST":
        print('id do usuario:', current_user.get_id())
        try:
            nome_fruto = request.form["nome_fruto"]
            frutose = float(request.form["frutose"])
            peso = float(request.form["peso"])
            tamanho = float(request.form["tamanho"])
            acidez = float(request.form["acidez"])
            data_str = request.form["data"]
            timestamp = datetime.strptime(data_str, "%Y-%m-%dT%H:%M")
            print(timestamp)
        except Exception as e:
            print(e)
            flash("Dados inválidos")
            return redirect(url_for("user_bp.cadastrar_coleta"))

        ColetaFrutoDAO.criar(
            usuario_id=current_user.get_id(),
            nome_fruto=nome_fruto,
            frutose=frutose,
            peso=peso,
            tamanho=tamanho,
            acidez=acidez,
            timestamp=timestamp
        )

        flash("Coleta registrada com sucesso")
        return redirect(url_for("user_bp.listar_coletas"))

    return render_template("coleta_form.html", frutas=lista_frutos)

@login_required
@user_bp.route("/minhascoletas")
def listar_coletas():
    coletas = ColetaFrutoDAO.listar_por_usuario(current_user.get_id())

    print("COLETAS DO USUARIO:", coletas)  # DEBUG

    return render_template("coletas_usuario.html", coletas=coletas)


@user_bp.route("/debug/coletas")
def debug_coletas():
    coletas = ColetaFrutoDAO.listar_todas()
    return "<br>".join([
        f"ID:{c.id} | USER:{c.usuario_id} | DATA:{c.timestamp}"
        for c in coletas
    ])