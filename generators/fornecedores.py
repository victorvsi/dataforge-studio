import random
import pandas as pd
from faker import Faker

fake = Faker("pt_BR")

ESTADOS = [
    "SP",
    "RJ",
    "MG",
    "PR",
    "SC",
    "RS",
    "BA",
    "PE",
    "CE",
    "GO"
]

def gerar_fornecedores(
    quantidade: int
) -> pd.DataFrame:

    dados = []

    for i in range(quantidade):

        dados.append({
            "fornecedor_id": f"FORN-{i+1:05}",
            "cnpj": fake.cnpj(),
            "razao_social": fake.company(),
            "cidade": fake.city(),
            "estado": random.choice(ESTADOS),
            "lead_time_dias": random.randint(2, 30),
            "score_confiabilidade": random.choices(
                ["Alto", "Médio", "Baixo"],
                weights=[60, 30, 10]
            )[0],
            "vigencia_inicio": pd.Timestamp.now().normalize(),
            "vigencia_fim": pd.Timestamp('9999-12-31'),
            "registro_ativo": True,
            "versao": 1
        })

    return pd.DataFrame(dados)