import pandas as pd

def gerar_calendario(
    inicio,
    fim
):

    calendario = pd.DataFrame({
        "data": pd.date_range(
            start=inicio,
            end=fim,
            freq="D"
        )
    })

    calendario["ano"] = calendario["data"].dt.year
    calendario["mes"] = calendario["data"].dt.month
    calendario["dia"] = calendario["data"].dt.day
    calendario["trimestre"] = calendario["data"].dt.quarter
    calendario["dia_semana"] = calendario["data"].dt.dayofweek

    return calendario