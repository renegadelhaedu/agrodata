import pandas as pd
from dao.leitura_dao import *

def gerar_correlacao_sensor(tipo1, tipo2):
    dado1 = LeituraDAO.get_dados_sensor(tipo1)
    dado2 = LeituraDAO.get_dados_sensor(tipo2)


    dado1_df = pd.DataFrame([{
        "valor": l.getValor(),
        "timestamp": l.getTimestamp()
    } for l in dado1])


    dado2_df = pd.DataFrame([{
        "valor": l.getValor(),
        "timestamp": l.getTimestamp()
    } for l in dado2])

    #depois nao precisara remover timessamtp
    dado1_df.drop(columns=['timestamp'], inplace=True)
    dado2_df.drop(columns=['timestamp'], inplace=True)
    #retirar isso depois pois o tamanho ja deve ser igual

    dado1_df = dado1_df[dado1_df.index < 10]

    correlacao = dado1_df['valor'].corr(dado2_df['valor'])

    return correlacao, dado1_df, dado2_df
