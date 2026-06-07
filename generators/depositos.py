import pandas as pd

def gerar_depositos():

    return pd.DataFrame([
        {
            "deposito_id": "DEP-001",
            "nome": "Depósito Principal",
            "capacidade_m3": 50000,
            "cidade": "São Paulo"
        },
        {
            "deposito_id": "DEP-002",
            "nome": "Canteiro A",
            "capacidade_m3": 10000,
            "cidade": "Campinas"
        },
        {
            "deposito_id": "DEP-003",
            "nome": "Canteiro B",
            "capacidade_m3": 8000,
            "cidade": "Sorocaba"
        },
        {
            "deposito_id": "DEP-004",
            "nome": "Canteiro C",
            "capacidade_m3": 12000,
            "cidade": "Santos"
        }
    ])