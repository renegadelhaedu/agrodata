from plotly import express as px
import pandas as pd
import plotly
import json


def calcular_media_semanal(leituras=None, coletas=None):
    medias = {
        "sensores": pd.DataFrame(columns=["semana", "tipo", "valor"]),
        "frutos": pd.DataFrame(columns=["semana", "nome_fruto", "frutose", "peso", "tamanho", "acidez"])
    }

    if leituras:
        df_sensores = pd.DataFrame([{
            "tipo": l.tipo,
            "valor": l.getValor(),
            "timestamp": l.getTimestamp()
        } for l in leituras])

        df_sensores["timestamp"] = pd.to_datetime(df_sensores["timestamp"])
        df_sensores["semana"] = df_sensores["timestamp"].dt.to_period("W").apply(lambda p: p.start_time.date())

        medias["sensores"] = (
            df_sensores
            .groupby(["semana", "tipo"], as_index=False)["valor"]
            .mean()
            .sort_values(["semana", "tipo"])
        )

    if coletas:
        df_frutos = pd.DataFrame([{
            "nome_fruto": c.nome_fruto,
            "frutose": c.frutose,
            "peso": c.peso,
            "tamanho": c.tamanho,
            "acidez": c.acidez,
            "timestamp": c.timestamp
        } for c in coletas])

        df_frutos["timestamp"] = pd.to_datetime(df_frutos["timestamp"])
        df_frutos["semana"] = df_frutos["timestamp"].dt.to_period("W").apply(lambda p: p.start_time.date())

        medias["frutos"] = (
            df_frutos
            .groupby(["semana", "nome_fruto"], as_index=False)[["frutose", "peso", "tamanho", "acidez"]]
            .mean()
            .sort_values(["semana", "nome_fruto"])
        )

    return medias


def gerar_graf(leituras, tipo):
    if not leituras:
        return False

    df = pd.DataFrame([{
        "valor": l.getValor(),
        "timestamp": l.getTimestamp()
    } for l in leituras])

    df.sort_values("timestamp", inplace=True)

    fig = px.line(
        df,
        x="timestamp",
        y="valor",
        title=f"Leituras do sensor: {tipo}",
        markers=True,
        template="plotly_white"
    )

    return fig

def grafico_correlacao(df1, df2):

    min_len = min(len(df1), len(df2))
    df1 = df1.head(min_len).reset_index(drop=True)
    df2 = df2.head(min_len).reset_index(drop=True)

    df_all = pd.DataFrame({
        'Sensor 1': df1['valor'],
        'Sensor 2': df2['valor']
    })

    fig = px.line(
        df_all,
        y=df_all.columns,
        title='Comparação de Séries Temporais'
    )

    fig.update_layout(
        xaxis_title='Índice',
        yaxis_title='Valor',
        hovermode='x unified',
        template='plotly_white',
        legend_title_text='Sensores'
    )

    return fig
