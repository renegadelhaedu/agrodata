from flask import *
from dao.usuarioDAO import *
from dao.leituraDAO import *
from dao.coletaFrutoDao import ColetaFrutoDAO

from routes.leitura_routes import leitura_bp

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        user = UsuarioDAO.autenticar(email, senha)

        # 🔴 1. usuário inválido
        if not user:
            flash("Email ou senha inválidos")
            return redirect(url_for("user_bp.login"))

        # 🔴 2. usuário não aprovado
        if not user.aprovado:
            flash("Usuário aguardando aprovação do administrador")
            return redirect(url_for("user_bp.login"))

        # ✅ login válido
        session["usuario_logado"] = True
        session["user_id"] = user.id

        flash("voce solicitou o acesso")
        return redirect(url_for("user_bp.painel_usuario"))


    return render_template("login_user.html")


@user_bp.route("/painel")
def painel_usuario():
    if not session.get("usuario_logado"):
        return redirect(url_for("user_bp.login"))

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

@user_bp.route("/user", methods=["GET"])
def user_list():
    if not session.get("usuario_logado"):
        return redirect(url_for("user_bp.login"))
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

@user_bp.route("/coleta", methods=["GET", "POST"])
def cadastrar_coleta():

    if not session.get("usuario_logado"):
        return redirect(url_for("user_bp.login"))

    if request.method == "POST":
        try:
            frutose = float(request.form["frutose"])
            peso = float(request.form["peso"])
            tamanho = float(request.form["tamanho"])
            acidez = float(request.form["acidez"])
        except:
            flash("Dados inválidos")
            return redirect(url_for("user_bp.cadastrar_coleta"))

        ColetaFrutoDAO.criar(
            usuario_id=session["user_id"],
            frutose=frutose,
            peso=peso,
            tamanho=tamanho,
            acidez=acidez
        )

        flash("Coleta registrada com sucesso")
        return redirect(url_for("user_bp.listar_coletas"))

    return render_template("coleta_form.html")

@user_bp.route("/coletas")
def listar_coletas():

    if not session.get("usuario_logado"):
        return redirect(url_for("user_bp.login"))

    coletas = ColetaFrutoDAO.listar_por_usuario(session["user_id"])

    return render_template("coletas_usuario.html", coletas=coletas)



