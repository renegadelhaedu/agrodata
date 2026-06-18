from flask import Blueprint, request,  render_template,  redirect, url_for, flash, current_app
from dao.leituraDAO import LeituraDAO
from werkzeug.security import check_password_hash
from modelo.leitura import Leitura
from modelo.admin import Admin
from banco import db
from decorators import admin_required
from dao.usuarioDAO import UsuarioDAO
from flask_login import login_user, logout_user, login_required
from datetime import datetime
from utils import lista_sensores
from grafico import grafico
from dao.coletaFrutoDao import ColetaFrutoDAO
import pandas as pd
from flask_login import current_user
import plotly.express as px
from analise.associacao_regras import (
    gerar_regras_clima,
    gerar_regras_risco,
    gerar_regras_qualidade,
    gerar_regras_frutos
)

from analise.regressor import *





admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/admin", methods=["GET"])
@login_required
@admin_required
def admin_page():
    leituras = LeituraDAO.listar_todas()
    # transforma em dicionários simples para o template
    leituras_data = [{
        "id": l.id,
        "sensor_id": l.sensor_id,
        "tipo": l.tipo,
        "valor": getattr(l, "valor", None),
        "timestamp": str(l.timestamp)
    } for l in leituras]
    return render_template(
        "admin/admin_panel.html",
        leituras=leituras_data,
        sensores=lista_sensores
    )



@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin/admin_login.html")

    usuario = request.form.get("usuario")
    senha = request.form.get("senha")

    user_hash = current_app.config.get("ADMIN_USER_HASH")
    pass_hash = current_app.config.get("ADMIN_PASSWORD_HASH")

    ok_user = check_password_hash(user_hash, usuario)
    ok_pass = check_password_hash(pass_hash, senha)

    if ok_user and ok_pass:
        login_user(Admin())
        return redirect(url_for("admin_bp.admin_page"))

    flash("Usuário ou senha inválidos.", "danger")
    return redirect(url_for("admin_bp.admin_login"))


# Logout
@admin_bp.route("/admin/logout")
@login_required
@admin_required
def admin_logout():
    logout_user()
    flash("Logout efetuado.", "info")
    return redirect(url_for("home"))

@admin_bp.route("/admin/delete", methods=["POST"])
@login_required
@admin_required
def admin_delete():
    sensor = request.form.get("sensor")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not sensor or not data_inicio or not data_fim:
        flash("Preencha todos os campos!", "danger")
        return redirect(url_for("admin_bp.admin_page"))

    from datetime import datetime
    try:
        d1 = datetime.strptime(data_inicio, "%Y-%m-%d")
        d2 = datetime.strptime(data_fim, "%Y-%m-%d")
    except:
        flash("Datas inválidas!", "danger")
        return redirect(url_for("admin_bp.admin_page"))

    # Buscar leituras do tipo escolhido no intervalo solicitado
    leituras = (
        Leitura.query
        .filter(Leitura.tipo == sensor)
        .filter(Leitura.timestamp >= d1)
        .filter(Leitura.timestamp <= d2)
        .all()
    )

    if not leituras:
        flash("Nenhuma leitura encontrada nesse intervalo!", "warning")
        return redirect(url_for("admin_bp.admin_page"))

    # Apagar tudo
    for l in leituras:
        db.session.delete(l)

    db.session.commit()

    flash(f"{len(leituras)} leituras do sensor '{sensor}' foram removidas.", "success")
    return redirect(url_for("admin_bp.admin_page"))

@admin_bp.route("/admin/delete/<int:id>", methods=["POST"])
@login_required
@admin_required
def admin_delete_by_id(id):
    leitura = Leitura.query.get(id)

    if not leitura:
        flash("Leitura não encontrada", "danger")
        return redirect(url_for("admin_bp.admin_page"))

    db.session.delete(leitura)
    db.session.commit()

    flash("Leitura excluída", "success")
    return redirect(url_for("admin_bp.admin_page"))


@admin_bp.route("/admin/delete_by_date", methods=["GET", "POST"])
@login_required
@admin_required
def delete_by_date_page():

    if request.method == "POST":

        sensor = request.form.get("sensor")
        data_inicio = request.form.get("data_inicio")
        data_fim = request.form.get("data_fim")

        LeituraDAO.deletar_por_data(
            sensor,
            data_inicio,
            data_fim
        )

        flash("Leituras removidas com sucesso.")

        return redirect(
            url_for("admin_bp.delete_by_date_page")
        )

    return render_template(
        "admin/admin_delete_by_date_page.html"
    )


@admin_bp.route("/admin/usuarios/delete/<int:id>", methods=["POST"])
@login_required
@admin_required
def admin_delete_usuario(id):
    UsuarioDAO.deletar(id)
    return redirect(url_for("admin_bp.admin_usuarios"))

@admin_bp.route("/admin/usuarios")
@login_required
@admin_required
def admin_usuarios():
    usuarios = UsuarioDAO.listar_aprovados()  # 🔥 aqui
    return render_template("admin/admin_usuarios.html", usuarios=usuarios)

@admin_bp.route("/admin/usuarios/pendentes")
@login_required
@admin_required
def usuarios_pendentes():
    usuarios = UsuarioDAO.listar_pendentes()
    return render_template("admin/admin_pendentes.html", usuarios=usuarios)

@admin_bp.route("/admin/usuarios/aprovar/<int:id>", methods=["POST"])
@login_required
@admin_required
def aprovar_usuario(id):
    UsuarioDAO.aprovar_usuario(id)
    return redirect(url_for("admin_bp.usuarios_pendentes"))

@admin_bp.route("/admin/usuarios/recusar/<int:id>", methods=["POST"])
@login_required
@admin_required
def recusar_usuario(id):
    UsuarioDAO.deletar(id)
    return redirect(url_for("admin_bp.usuarios_pendentes"))

@admin_bp.route("/filtrar", methods=["GET"])
@login_required
@admin_required
def filtrar_leituras():

    sensor_id = request.args.get("sensor_id")
    tipo = request.args.get("tipo")
    valor_min = request.args.get("valor_min")
    valor_max = request.args.get("valor_max")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    # Conversão de datas (ISO esperado)
    try:
        data_inicio = datetime.fromisoformat(data_inicio) if data_inicio else None
    except Exception:
        data_inicio = None

    try:
        data_fim = datetime.fromisoformat(data_fim) if data_fim else None
    except Exception:
        data_fim = None

    if data_fim:
        data_fim = data_fim.replace(second=59, microsecond=999999)

    # Conversão numérica segura
    try:
        valor_min = float(valor_min) if valor_min else None
    except Exception:
        valor_min = None

    try:
        valor_max = float(valor_max) if valor_max else None
    except Exception:
        valor_max = None



    try:
        leituras = LeituraDAO.filtrar(
            sensor_id=sensor_id,
            tipo=tipo,
            valor_min=valor_min,
            valor_max=valor_max,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
    except ValueError:
        # fallback seguro se tipo for inválido
        leituras = []

    return render_template(
        "admin/admin_panel.html",
        leituras=leituras,
        sensores=lista_sensores
    )


@admin_bp.route("/grafico-filtrado", methods=["GET"])
@login_required
@admin_required
def grafico_filtrado():

    from datetime import datetime

    sensores = lista_sensores

    tipo = request.args.get("tipo")
    data_inicio = request.args.get("data_inicio")
    data_fim = request.args.get("data_fim")

    graphHTML = None
    aviso = None

    if tipo:

        query = Leitura.query.filter(Leitura.tipo == tipo)

        # 🔹 filtro por data direto no banco (correto)
        if data_inicio:
            data_inicio = datetime.fromisoformat(data_inicio)
            query = query.filter(Leitura.timestamp >= data_inicio)

        if data_fim:
            data_fim = datetime.fromisoformat(data_fim)
            query = query.filter(Leitura.timestamp <= data_fim)

        leituras = query.order_by(Leitura.timestamp.asc()).all()

        if not leituras:
            aviso = "⚠ Nenhum dado encontrado para esse filtro."
        else:
            fig = grafico.gerar_graf(leituras, tipo)
            graphHTML = fig.to_html(full_html=False)

    return render_template(
        "admin/graficoc.html",
        sensores=sensores,
        graphHTML=graphHTML,
        aviso=aviso
    )

@admin_bp.route("/correlacaoclimaadmin", methods=["GET", "POST"])
@login_required
@admin_required
def pagina_correlacao_clima():

    from analise.analisador import gerar_correlacao_sensor

    # pega intervalo total de datas do banco
    leituras = LeituraDAO.listar_todas()
    datas = [l.getTimestamp() for l in leituras if l.getTimestamp()]
    data_min = min(datas).strftime("%Y-%m-%d") if datas else None
    data_max = max(datas).strftime("%Y-%m-%d") if datas else None

    if request.method == "GET":
        return render_template(
            "correlacao/admin/correlacao_clima_admin.html",
            data_min=data_min,
            data_max=data_max,
        )

    # POST → calcular correlação
    tipo1 = request.form.get("sensor1")
    tipo2 = request.form.get("sensor2")
    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")
    data_inicio_form = data_inicio
    data_fim_form = data_fim

    if not tipo1 or not tipo2:
        return render_template(
            "correlacao/admin/correlacao_clima_admin.html",
            aviso="Selecione os dois sensores.",
            data_min=data_min,
            data_max=data_max,
            tipo1=tipo1,
            tipo2=tipo2,
            data_inicio=data_inicio_form,
            data_fim=data_fim_form,

        )

    leituras1 = LeituraDAO.get_dados_sensor(tipo1)
    leituras2 = LeituraDAO.get_dados_sensor(tipo2)

    if not leituras1 or not leituras2:
        return render_template(
            "correlacao/admin/correlacao_clima_admin.html",
            aviso="⚠ Sensores sem dados suficientes.",
            data_min=data_min,
            data_max=data_max,
            tipo1=tipo1,
            tipo2=tipo2,
            data_inicio=data_inicio_form,
            data_fim=data_fim_form
        )

    df1 = pd.DataFrame([{"valor": l.getValor(), "timestamp": l.getTimestamp()} for l in leituras1])
    df2 = pd.DataFrame([{"valor": l.getValor(), "timestamp": l.getTimestamp()} for l in leituras2])

    df1["timestamp"] = pd.to_datetime(df1["timestamp"])
    df2["timestamp"] = pd.to_datetime(df2["timestamp"])

    if data_inicio and data_fim:
        data_inicio = pd.to_datetime(data_inicio)
        data_fim = pd.to_datetime(data_fim)

        df1 = df1[(df1["timestamp"] >= data_inicio) & (df1["timestamp"] <= data_fim)]
        df2 = df2[(df2["timestamp"] >= data_inicio) & (df2["timestamp"] <= data_fim)]

    corre, _, _ = gerar_correlacao_sensor(tipo1, tipo2)
    fig = grafico.grafico_correlacao(df1, df2)
    graph_html = fig.to_html(full_html=False)

    return render_template(
        "correlacao/admin/correlacao_clima_admin.html",
        graphHTML=graph_html,
        correlacao=corre,
        data_min=data_min,
        data_max=data_max,
        tipo1=tipo1,
        tipo2=tipo2,
        data_inicio=data_inicio_form,
        data_fim=data_fim_form,

    )

@admin_bp.route("/correlacao-fruto-admin", methods=["GET", "POST"])
@login_required
@admin_required
def pagina_correlacao_fruto():

    frutos = ColetaFrutoDAO.listar_frutos_unicos(current_user.id)

    print("USUARIO LOGADO:", current_user.id)
    print("FRUTOS:", frutos)

    coletas = ColetaFrutoDAO.listar_por_usuario(current_user.id)

    for c in coletas:
        print(
            c.id,
            c.usuario_id,
            c.nome_fruto
        )
    # ============================================
    # GET
    # ============================================

    if request.method == "GET":
        return render_template(
            "correlacao/admin/correlacao_clima_fruto_admin.html",
            frutos=frutos
        )

    # ============================================
    # FORM
    # ============================================

    sensor = request.form.get("sensor")
    atributo = request.form.get("atributo")
    nome_fruto = request.form.get("nome_fruto")

    data_inicio = request.form.get("data_inicio")
    data_fim = request.form.get("data_fim")

    if not sensor or not atributo or not nome_fruto:

        return render_template(
            "correlacao/admin/correlacao_clima_fruto_admin.html",
            frutos=frutos,
            aviso="Preencha todos os campos."
        )

    # ============================================
    # COLETAS DO FRUTO
    # ============================================

    coletas = [
        c for c in ColetaFrutoDAO.listar_por_usuario(current_user.id)
        if c.nome_fruto == nome_fruto
    ]

    if not coletas:

        return render_template(
            "correlacao/admin/correlacao_clima_fruto_admin.html",
            frutos=frutos,
            aviso="Nenhuma coleta encontrada."
        )

    # ============================================
    # DATAFRAME FRUTO
    # ============================================

    dados_fruto = []

    for c in coletas:

        valor = getattr(c, atributo)

        if valor is None:
            continue

        dados_fruto.append({
            "data": c.timestamp.date(),
            "valor_fruto": float(valor)
        })

    df_fruto = pd.DataFrame(dados_fruto)

    if df_fruto.empty:

        return render_template(
            "correlacao/admin/correlacao_clima_fruto_admin.html",
            frutos=frutos,
            aviso="Sem dados do fruto."
        )

    # ============================================
    # LEITURAS SENSOR
    # ============================================

    leituras = LeituraDAO.get_dados_sensor(sensor)

    if not leituras:

        return render_template(
            "correlacao/admin/correlacao_clima_fruto_admin.html",
            frutos=frutos,
            aviso="Sensor sem leituras."
        )

    dados_sensor = []

    for l in leituras:

        timestamp = l.getTimestamp()

        if not timestamp:
            continue

        dados_sensor.append({
            "data": timestamp.date(),
            "valor_sensor": float(l.getValor())
        })

    df_sensor = pd.DataFrame(dados_sensor)

    if df_sensor.empty:

        return render_template(
            "correlacao/admin/correlacao_clima_fruto_admin.html",
            frutos=frutos,
            aviso="Sem dados do sensor."
        )

    # ============================================
    # FILTRO DE DATA
    # ============================================

    if data_inicio:

        data_inicio = pd.to_datetime(data_inicio).date()

        df_fruto = df_fruto[
            df_fruto["data"] >= data_inicio
        ]

        df_sensor = df_sensor[
            df_sensor["data"] >= data_inicio
        ]

    if data_fim:

        data_fim = pd.to_datetime(data_fim).date()

        df_fruto = df_fruto[
            df_fruto["data"] <= data_fim
        ]

        df_sensor = df_sensor[
            df_sensor["data"] <= data_fim
        ]

    # ============================================
    # MÉDIA DO SENSOR POR DIA
    # ============================================

    df_sensor = (
        df_sensor
        .groupby("data")["valor_sensor"]
        .mean()
        .reset_index()
    )

    # ============================================
    # MÉDIA DO FRUTO POR DIA
    # ============================================

    df_fruto = (
        df_fruto
        .groupby("data")["valor_fruto"]
        .mean()
        .reset_index()
    )

    # ============================================
    # JUNÇÃO POR DIA
    # ============================================

    df = pd.merge(
        df_fruto,
        df_sensor,
        on="data",
        how="inner"
    )

    if df.empty:

        return render_template(
            "correlacao/admin/correlacao_clima_fruto_admin.html",
            frutos=frutos,
            aviso="Não existem datas compatíveis."
        )

    # ============================================
    # CORRELAÇÃO
    # ============================================

    correlacao = df["valor_fruto"].corr(
        df["valor_sensor"]
    )

    # ============================================
    # GRÁFICO
    # ============================================

    # ============================================
    # GRÁFICO TEMPORAL
    # ============================================

    fig = px.line(
        df,
        x="data",
        y=["valor_sensor", "valor_fruto"],
        markers=True,
        title=f"{sensor} × {atributo}"
    )

    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Valor",
        legend_title="Séries",
        template="plotly_white"
    )

    fig.update_traces(
        mode="lines+markers"
    )

    graphHTML = fig.to_html(full_html=False)
    # ============================================
    # RENDER
    # ============================================

    return render_template(
        "correlacao/admin/correlacao_clima_fruto_admin.html",
        frutos=frutos,
        correlacao=round(correlacao, 4),
        graphHTML=graphHTML
    )

#associacoes de regras

@admin_bp.route("/regras/frutos")
@login_required
@admin_required
def regras_frutos():

    regras = gerar_regras_frutos()

    return render_template(
        "associacao/associacao_frutos.html",
        regras=regras
    )


@admin_bp.route("/regras/clima")
@login_required
@admin_required
def regras_clima():

    regras = gerar_regras_clima()

    return render_template(
        "associacao/associacao_clima.html",
        regras=regras
    )


@admin_bp.route("/regras/qualidade")
@login_required
@admin_required
def regras_qualidade():

    regras = gerar_regras_qualidade()

    return render_template(
        "associacao/associacao_qualidade.html",
        regras=regras
    )


@admin_bp.route("/regras/riscos")
@login_required
@admin_required
def regras_risco():

    regras = gerar_regras_risco()

    return render_template(
        "associacao/associacao_risco.html",
        regras=regras
    )



#regressao

@admin_bp.route("/regressor/linear")
@login_required
@admin_required
def regressor_linear():

    resultado = regressao_linear_simples()

    return render_template(
        "regressor/linear.html",
        resultado=resultado
    )


@admin_bp.route("/regressor/multipla")
@login_required
@admin_required
def regressor_multipla():

    resultado = regressao_linear_multipla()

    return render_template(
        "regressor/multipla.html",
        resultado=resultado
    )


@admin_bp.route("/regressor/arvore")
@login_required
@admin_required
def regressor_arvore():

    resultado = regressao_arvore()

    return render_template(
        "regressor/arvore.html",
        resultado=resultado
    )


@admin_bp.route("/regressor/polinomial")
@login_required
@admin_required
def regressor_polinomial():

    resultado = regressao_polinomial()

    return render_template(
        "regressor/polinomial.html",
        resultado=resultado
    )
