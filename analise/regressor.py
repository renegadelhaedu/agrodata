from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import r2_score

import pandas as pd

from dao.leituraDAO import LeituraDAO


def obter_dataframe_sensores():

    leituras = LeituraDAO.listar_todas()

    if not leituras:
        return pd.DataFrame()

    dados = {}

    for leitura in leituras:

        chave = leitura.timestamp.strftime(
            "%Y-%m-%d %H:%M"
        )

        if chave not in dados:
            dados[chave] = {}

        dados[chave][leitura.tipo] = leitura.valor

    df = pd.DataFrame(
        list(dados.values())
    )

    colunas_necessarias = [
        "temperatura_ar",
        "umidade_ar",
        "umidade_solo",
        "radiacao_uv"
    ]

    for coluna in colunas_necessarias:

        if coluna not in df.columns:
            df[coluna] = pd.NA

    df = df[colunas_necessarias]

    df = df.dropna()

    print("\n===== DATAFRAME REGRESSÃO =====")
    print("Colunas:", df.columns.tolist())
    print("Shape:", df.shape)

    if not df.empty:
        print(df.head())

    print("==============================\n")

    return df


def validar_dataframe(df, colunas):

    if df.empty:
        return False

    if len(df) < 2:
        return False

    for coluna in colunas:

        if coluna not in df.columns:
            return False

        if df[coluna].isnull().all():
            return False

    return True


def regressao_linear_simples():

    try:

        df = obter_dataframe_sensores()

        if not validar_dataframe(
            df,
            [
                "temperatura_ar",
                "umidade_solo"
            ]
        ):
            return {
                "erro": "Dados insuficientes para regressão linear simples."
            }

        X = df[["temperatura_ar"]]

        y = df["umidade_solo"]

        modelo = LinearRegression()

        modelo.fit(X, y)

        y_pred = modelo.predict(X)

        return {

            "coeficiente":
                round(float(modelo.coef_[0]), 4),

            "intercepto":
                round(float(modelo.intercept_), 4),

            "r2":
                round(float(r2_score(y, y_pred)), 4)

        }

    except Exception as e:

        return {"erro": str(e)}


def regressao_linear_multipla():

    try:

        df = obter_dataframe_sensores()

        if not validar_dataframe(
            df,
            [
                "temperatura_ar",
                "umidade_ar",
                "radiacao_uv",
                "umidade_solo"
            ]
        ):
            return {
                "erro": "Dados insuficientes para regressão múltipla."
            }

        X = df[
            [
                "temperatura_ar",
                "umidade_ar",
                "radiacao_uv"
            ]
        ]

        y = df["umidade_solo"]

        modelo = LinearRegression()

        modelo.fit(X, y)

        y_pred = modelo.predict(X)

        return {

            "coeficientes": {

                "temperatura":
                    round(float(modelo.coef_[0]), 4),

                "umidade_ar":
                    round(float(modelo.coef_[1]), 4),

                "radiacao_uv":
                    round(float(modelo.coef_[2]), 4)

            },

            "intercepto":
                round(float(modelo.intercept_), 4),

            "r2":
                round(float(r2_score(y, y_pred)), 4)

        }

    except Exception as e:

        return {"erro": str(e)}


def regressao_arvore():

    try:

        df = obter_dataframe_sensores()

        if not validar_dataframe(
            df,
            [
                "temperatura_ar",
                "umidade_ar",
                "radiacao_uv",
                "umidade_solo"
            ]
        ):
            return {
                "erro": "Dados insuficientes para árvore de decisão."
            }

        X = df[
            [
                "temperatura_ar",
                "umidade_ar",
                "radiacao_uv"
            ]
        ]

        y = df["umidade_solo"]

        modelo = DecisionTreeRegressor(
            max_depth=5,
            random_state=42
        )

        modelo.fit(X, y)

        y_pred = modelo.predict(X)

        return {

            "r2":
                round(float(r2_score(y, y_pred)), 4),

            "profundidade":
                modelo.get_depth(),

            "folhas":
                modelo.get_n_leaves()

        }

    except Exception as e:

        return {"erro": str(e)}


def regressao_polinomial():

    try:

        df = obter_dataframe_sensores()

        if not validar_dataframe(
            df,
            [
                "temperatura_ar",
                "umidade_solo"
            ]
        ):
            return {
                "erro": "Dados insuficientes para regressão polinomial."
            }

        X = df[
            [
                "temperatura_ar"
            ]
        ]

        y = df["umidade_solo"]

        poly = PolynomialFeatures(
            degree=2
        )

        X_poly = poly.fit_transform(X)

        modelo = LinearRegression()

        modelo.fit(
            X_poly,
            y
        )

        y_pred = modelo.predict(
            X_poly
        )

        return {

            "coeficientes":
                [
                    round(float(v), 4)
                    for v in modelo.coef_
                ],

            "intercepto":
                round(float(modelo.intercept_), 4),

            "r2":
                round(float(r2_score(y, y_pred)), 4)

        }

    except Exception as e:

        return {"erro": str(e)}