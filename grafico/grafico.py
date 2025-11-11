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
    df_all = pd.concat([df1, df2], ignore_index=True, axis=1)

    df_all.columns = ['Sensor 1', 'Sensor 2']

    fig = px.line(df_all, x=df_all.index, y=df_all.columns,
                  title='Comparação de Séries Temporais'
                  )

    fig.update_layout(
        xaxis_title='Índice',
        yaxis_title='Valor',
        hovermode='x unified',
        template='plotly_white',
        legend_title_text='Origem dos dados'
    )

    return fig