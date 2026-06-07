import random
import pandas as pd
from faker import Faker

fake = Faker("pt_BR")

REGRAS_CATEGORIA = {

    "Construção": {
        "unidades": ["SC", "KG", "M3"],
        "validade": True,
        "custo": (15, 300),
        "consumo": (10, 50)
    },

    "Elétrica": {
        "unidades": ["UN", "RL", "M"],
        "validade": False,
        "custo": (2, 500),
        "consumo": (5, 100)
    },

    "Hidráulica": {
        "unidades": ["UN", "CX", "M"],
        "validade": False,
        "custo": (5, 250),
        "consumo": (2, 40)
    },

    "Pintura": {
        "unidades": ["LT", "GL"],
        "validade": True,
        "custo": (20, 800),
        "consumo": (1, 20)
    },

    "Ferramentas": {
        "unidades": ["UN", "CJ"],
        "validade": False,
        "custo": (100, 3000),
        "consumo": (0.1, 2)
    },

    "EPI": {
        "unidades": ["UN", "CX", "PR"],
        "validade": True,
        "custo": (5, 150),
        "consumo": (5, 30)
    },

    "Fixação": {
        "unidades": ["CX", "MIL"],
        "validade": False,
        "custo": (1, 50),
        "consumo": (50, 500)
    }
}

def gerar_endereco_wms():

    rua = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    corredor = random.randint(1, 30)

    nivel = random.randint(1, 8)

    posicao = random.randint(1, 200)

    return (
        f"{rua}-"
        f"{corredor:02d}-"
        f"{nivel:02d}-"
        f"{posicao:03d}"
    )

def calcular_curva_abc(df):

    df = df.copy()

    df["valor_anual"] = (
        df["consumo_medio_dia"]
        * 365
        * df["custo_unitario"]
    )

    df = df.sort_values(
        "valor_anual",
        ascending=False
    )

    df["perc_acumulado"] = (
        df["valor_anual"].cumsum()
        /
        df["valor_anual"].sum()
    )

    df["curva_abc"] = pd.cut(
        df["perc_acumulado"],
        bins=[0, 0.80, 0.95, 1.00],
        labels=["A", "B", "C"],
        include_lowest=True
    )

    return (
        df
        .drop(columns=[
            "valor_anual",
            "perc_acumulado"
        ])
        .reset_index(drop=True)
    )

def gerar_produtos(
    df_fornecedores,
    quantidade
):

    dados = []

    for i in range(quantidade):

        categoria = random.choice(
            list(REGRAS_CATEGORIA.keys())
        )

        regras = REGRAS_CATEGORIA[categoria]

        fornecedor = (
            df_fornecedores
            .sample(1)
            .iloc[0]
        )

        lead_time_real = (
            fornecedor["lead_time_dias"]
            +
            random.randint(0, 5)
        )

        custo = round(
            random.uniform(
                *regras["custo"]
            ),
            2
        )

        consumo = round(
            random.uniform(
                *regras["consumo"]
            ),
            2
        )

        estoque_minimo = int(
            consumo
            *
            lead_time_real
        )

        ponto_reposicao = int(
            consumo
            *
            (
                lead_time_real
                + 3
            )
        )

        estoque_maximo = (
            estoque_minimo
            +
            int(
                consumo
                *
                random.randint(
                    30,
                    60
                )
            )
        )

        criticidade = random.choices(
            [
                "Alta",
                "Média",
                "Baixa"
            ],
            weights=[
                15,
                35,
                50
            ]
        )[0]

        dados.append({

            "sku":
                f"SKU-{i+1:06}",

            "descricao":
                f"{categoria} "
                f"{fake.word().capitalize()}",

            "categoria":
                categoria,

            "unidade":
                random.choice(
                    regras["unidades"]
                ),

            "peso_kg":
                round(
                    random.uniform(
                        0.1,
                        50
                    ),
                    2
                ),

            "volume_m3":
                round(
                    random.uniform(
                        0.001,
                        2
                    ),
                    3
                ),

            "fornecedor_id":
                fornecedor[
                    "fornecedor_id"
                ],

            "custo_unitario":
                custo,

            "consumo_medio_dia":
                consumo,

            "lead_time":
                lead_time_real,

            "estoque_minimo":
                estoque_minimo,

            "ponto_reposicao":
                ponto_reposicao,

            "estoque_maximo":
                estoque_maximo,

            "criticidade":
                criticidade,

            "controla_validade":
                regras["validade"],

            "endereco_wms": gerar_endereco_wms(),

            "vigencia_inicio": pd.Timestamp.now().normalize(),
            "vigencia_fim": pd.Timestamp('9999-12-31'),
            "registro_ativo": True,
            "versao": 1
        })

    df = pd.DataFrame(dados)

    return calcular_curva_abc(df)