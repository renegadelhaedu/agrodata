from collections import defaultdict

import pandas as pd

from mlxtend.frequent_patterns import apriori
from mlxtend.frequent_patterns import association_rules
from mlxtend.preprocessing import TransactionEncoder

from dao.leituraDAO import LeituraDAO
from dao.coletaFrutoDao import ColetaFrutoDAO


# ==================================================
# FAIXAS
# ==================================================

def faixa_frutose(v):

    if v < 5:
        return "Frutose_Baixa"

    elif v < 10:
        return "Frutose_Media"

    return "Frutose_Alta"


def faixa_peso(v):

    if v < 100:
        return "Peso_Baixo"

    elif v < 300:
        return "Peso_Medio"

    return "Peso_Alto"


def faixa_tamanho(v):

    if v < 5:
        return "Tam_Pequeno"

    elif v < 10:
        return "Tam_Medio"

    return "Tam_Grande"


def faixa_acidez(v):

    if v < 4:
        return "Acidez_Baixa"

    elif v < 7:
        return "Acidez_Media"

    return "Acidez_Alta"


def faixa_temperatura(v):

    if v < 20:
        return "Temp_Baixa"

    elif v < 30:
        return "Temp_Media"

    return "Temp_Alta"


def faixa_umidade(v):

    if v < 30:
        return "Umidade_Baixa"

    elif v < 70:
        return "Umidade_Media"

    return "Umidade_Alta"


def faixa_solo(v):

    if v < 30:
        return "Solo_Baixo"

    elif v < 70:
        return "Solo_Medio"

    return "Solo_Alto"


# ==================================================
# APRIORI GENÉRICO
# ==================================================

def executar_apriori(
        transacoes,
        suporte=0.02,
        confianca=0.50
):

    if not transacoes:
        return []

    te = TransactionEncoder()

    te_array = te.fit(
        transacoes
    ).transform(transacoes)

    df = pd.DataFrame(
        te_array,
        columns=te.columns_
    )

    freq = apriori(
        df,
        min_support=suporte,
        use_colnames=True
    )

    if freq.empty:
        return []

    regras = association_rules(
        freq,
        metric="confidence",
        min_threshold=confianca
    )

    if regras.empty:
        return []

    regras = regras.sort_values(
        by="lift",
        ascending=False
    )

    resultado = []

    for _, row in regras.iterrows():

        resultado.append({

            "antecedente":
                ", ".join(
                    sorted(list(row["antecedents"]))
                ),

            "consequente":
                ", ".join(
                    sorted(list(row["consequents"]))
                ),

            "support":
                round(float(row["support"]), 4),

            "confidence":
                round(float(row["confidence"]), 4),

            "lift":
                round(float(row["lift"]), 4)

        })

    return resultado


# ==================================================
# CLIMA
# ==================================================

def gerar_transacoes_clima():

    leituras = LeituraDAO.listar_todas()

    grupos = defaultdict(set)

    for leitura in leituras:

        chave = leitura.timestamp.strftime(
            "%Y-%m-%d"
        )

        if leitura.tipo == "temperatura_ar":

            grupos[chave].add(
                faixa_temperatura(
                    leitura.valor
                )
            )

        elif leitura.tipo == "umidade_ar":

            grupos[chave].add(
                faixa_umidade(
                    leitura.valor
                )
            )

        elif leitura.tipo == "umidade_solo":

            grupos[chave].add(
                faixa_solo(
                    leitura.valor
                )
            )

    return [
        list(v)
        for v in grupos.values()
        if len(v) >= 2
    ]


def gerar_regras_clima():

    return executar_apriori(
        gerar_transacoes_clima()
    )


# ==================================================
# FRUTOS
# ==================================================

def gerar_transacoes_frutos():

    frutos = ColetaFrutoDAO.listar_todas()

    transacoes = []

    for f in frutos:

        transacoes.append([

            f.nome_fruto,

            faixa_frutose(f.frutose),

            faixa_peso(f.peso),

            faixa_tamanho(f.tamanho),

            faixa_acidez(f.acidez)

        ])

    return transacoes


def gerar_regras_frutos():

    return executar_apriori(
        gerar_transacoes_frutos()
    )


# ==================================================
# QUALIDADE
# ==================================================

def gerar_transacoes_qualidade():

    frutos = ColetaFrutoDAO.listar_todas()

    transacoes = []

    for f in frutos:

        transacoes.append([

            faixa_frutose(f.frutose),

            faixa_peso(f.peso),

            faixa_tamanho(f.tamanho),

            faixa_acidez(f.acidez)

        ])

    return transacoes


def gerar_regras_qualidade():

    return executar_apriori(
        gerar_transacoes_qualidade()
    )


# ==================================================
# RISCO AGRÍCOLA
# ==================================================

def gerar_transacoes_risco():

    leituras = LeituraDAO.listar_todas()

    grupos = defaultdict(set)

    for leitura in leituras:

        chave = leitura.timestamp.strftime(
            "%Y-%m-%d"
        )

        if leitura.tipo == "temperatura_ar":

            if leitura.valor >= 35:

                grupos[chave].add(
                    "Risco_Calor"
                )

            else:

                grupos[chave].add(
                    faixa_temperatura(
                        leitura.valor
                    )
                )

        elif leitura.tipo == "umidade_solo":

            if leitura.valor <= 20:

                grupos[chave].add(
                    "Risco_Seca"
                )

            else:

                grupos[chave].add(
                    faixa_solo(
                        leitura.valor
                    )
                )

        elif leitura.tipo == "umidade_ar":

            grupos[chave].add(
                faixa_umidade(
                    leitura.valor
                )
            )

    return [
        list(v)
        for v in grupos.values()
        if len(v) >= 2
    ]


def gerar_regras_risco():

    return executar_apriori(
        gerar_transacoes_risco()
    )