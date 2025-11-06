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


