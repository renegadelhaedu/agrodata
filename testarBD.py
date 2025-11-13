import pandas as pd
from dao.leitura_dao import *
import app
app = app.app


with app.app_context():
    umi_ar = LeituraDAO.get_dados_sensor('umidade_ar')
    umi_solo = LeituraDAO.get_dados_sensor('umidade_solo')

    umi_ar_df = pd.DataFrame([{
        "valor": l.getValor(),
        "timestamp": l.getTimestamp()
    } for l in umi_ar])

    umi_solo_df = pd.DataFrame([{
        "valor": l.getValor(),
        "timestamp": l.getTimestamp()
    } for l in umi_solo])

    umi_ar_df.drop(columns=['timestamp'], inplace=True)
    umi_solo_df.drop(columns=['timestamp'], inplace=True)
    umi_ar_df = umi_ar_df[umi_ar_df.index < 10]
    print(umi_ar_df)
    print(umi_solo_df)

    correlacao = umi_ar_df['valor'].corr(umi_solo_df['valor'])
    print(correlacao)




