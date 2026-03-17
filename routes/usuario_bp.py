from flask import *
from dao.modelsDAO import *

from routes.leitura_routes import leitura_bp

user_bp = Blueprint("user_bp", __name__)

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

# =========================
# LOGIN
# =========================
@user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        user = UsuarioDAO.autenticar(email, senha)

        if not user:
            return "Credenciais inválidas"

        if user.aprovado == 0:
            return "Aguardando aprovação do admin"

        return "Login autorizado"

    return render_template("login_user.html")

if __name__ == "__main__":
    app.run(debug=True)
