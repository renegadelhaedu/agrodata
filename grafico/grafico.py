from plotly import express as px
import pandas as pd
import plotly
import json

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
