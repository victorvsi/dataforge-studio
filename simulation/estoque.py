import uuid
import random
import pandas as pd


class EstoqueWMS:

    def __init__(self):

        self.estoque = {}

    # =====================================================
    # ESTRUTURA
    # =====================================================

    def criar_deposito(
        self,
        deposito_id
    ):

        if deposito_id not in self.estoque:

            self.estoque[deposito_id] = {}

    def criar_sku(
        self,
        deposito_id,
        sku
    ):

        self.criar_deposito(
            deposito_id
        )

        if sku not in self.estoque[deposito_id]:

            self.estoque[deposito_id][sku] = []

    # =====================================================
    # ESTOQUE INICIAL
    # =====================================================

    def gerar_estoque_inicial(
        self,
        df_produtos,
        df_depositos
    ):

        produtos = df_produtos.to_dict(
            "records"
        )

        for deposito in df_depositos[
            "deposito_id"
        ]:

            self.criar_deposito(
                deposito
            )

            for produto in produtos:

                sku = produto["sku"]

                self.criar_sku(
                    deposito,
                    sku
                )

                qtd_total = int(
                    produto[
                        "estoque_maximo"
                    ]
                    *
                    random.uniform(
                        0.80,
                        1.00
                    )
                )

                if qtd_total <= 0:
                    continue

                qtd_lotes = random.randint(
                    1,
                    5
                )

                saldo = qtd_total

                for i in range(
                    qtd_lotes
                ):

                    if saldo <= 0:
                        break

                    if i == qtd_lotes - 1:

                        qtd_lote = saldo

                    else:

                        qtd_lote = random.randint(
                            1,
                            saldo
                        )

                    saldo -= qtd_lote

                    data_fabricacao = (
                        pd.Timestamp.now()
                        -
                        pd.Timedelta(
                            days=random.randint(
                                1,
                                365
                            )
                        )
                    )

                    validade = None

                    if produto[
                        "controla_validade"
                    ]:

                        validade = (
                            data_fabricacao
                            +
                            pd.Timedelta(
                                days=random.randint(
                                    180,
                                    720
                                )
                            )
                        )

                    self.estoque[
                        deposito
                    ][sku].append({

                        "lote_id":
                            f"LOT-{str(uuid.uuid4())[:8].upper()}",

                        "sku":
                            sku,

                        "deposito":
                            deposito,

                        "qtd":
                            qtd_lote,

                        "custo_unitario":
                            produto[
                                "custo_unitario"
                            ],

                        "data_fabricacao":
                            data_fabricacao,

                        "validade":
                            validade,

                        "status":
                            "Disponível"
                    })

    # =====================================================
    # CONSULTA DE LOTES
    # =====================================================

    def lotes(
        self,
        deposito,
        sku
    ):

        """
        Retorna a lista de lotes para um SKU em um depósito.
        Retorna uma lista vazia se o depósito ou SKU não existir, evitando KeyErrors.
        """
        return self.estoque.get(deposito, {}).get(sku, [])

    # =====================================================
    # FEFO
    # =====================================================

    def consumir_fefo(
        self,
        deposito,
        sku,
        quantidade
    ):

        lotes = self.lotes(
            deposito,
            sku
        )

        disponiveis = [

            lote

            for lote in lotes

            if (
                lote["status"]
                ==
                "Disponível"
            )

            and

            lote["qtd"] > 0
        ]

        max_date = (
            pd.Timestamp.max.date()
        )

        disponiveis.sort(

            key=lambda x:

            x["validade"]

            if x["validade"]

            else max_date
        )

        restante = quantidade

        consumidos = []

        for lote in disponiveis:

            if restante <= 0:
                break

            retirar = min(
                lote["qtd"],
                restante
            )

            lote["qtd"] -= retirar

            restante -= retirar

            consumidos.append({

                "lote_id":
                    lote["lote_id"],

                "quantidade":
                    retirar,

                "custo_unitario":
                    lote[
                        "custo_unitario"
                    ],

                "validade":
                    lote[
                        "validade"
                    ]
            })

        return (
            consumidos,
            restante
        )

    # =====================================================
    # RECEBIMENTO
    # =====================================================

    def receber_lote(
        self,
        deposito,
        sku,
        quantidade,
        custo_unitario,
        controla_validade
    ):

        self.criar_sku(
            deposito,
            sku
        )

        data_fabricacao = (
            pd.Timestamp.now()
        )

        validade = None

        if controla_validade:

            validade = (
                data_fabricacao
                +
                pd.Timedelta(
                    days=random.randint(
                        180,
                        720
                    )
                )
            )

        lote_id = (
            f"LOT-{str(uuid.uuid4())[:8].upper()}"
        )

        self.estoque[
            deposito
        ][sku].append({

            "lote_id":
                lote_id,

            "sku":
                sku,

            "deposito":
                deposito,

            "qtd":
                quantidade,

            "custo_unitario":
                custo_unitario,

            "data_fabricacao":
                data_fabricacao,

            "validade":
                validade,

            "status":
                "Quarentena"
        })

        return lote_id

    # =====================================================
    # QUARENTENA
    # =====================================================

    def liberar_quarentena(
        self,
        taxa_aprovacao=0.95
    ):

        for deposito in self.estoque:

            for sku in self.estoque[
                deposito
            ]:

                for lote in self.estoque[
                    deposito
                ][sku]:

                    if lote[
                        "status"
                    ] == "Quarentena":

                        if (
                            random.random()
                            <
                            taxa_aprovacao
                        ):

                            lote[
                                "status"
                            ] = "Disponível"

                        else:

                            lote[
                                "status"
                            ] = "Rejeitado"

    # =====================================================
    # TRANSFERÊNCIA
    # =====================================================

    def transferir(
        self,
        origem,
        destino,
        sku,
        quantidade
    ):

        consumidos, restante = (
            self.consumir_fefo(
                origem,
                sku,
                quantidade
            )
        )

        transferido = (
            quantidade
            -
            restante
        )

        if transferido <= 0:

            return 0

        self.criar_sku(
            destino,
            sku
        )

        for item in consumidos:

            self.estoque[
                destino
            ][sku].append({

                "lote_id":
                    item["lote_id"],

                "sku":
                    sku,

                "deposito":
                    destino,

                "qtd":
                    item[
                        "quantidade"
                    ],

                "custo_unitario":
                    item[
                        "custo_unitario"
                    ],

                "data_fabricacao":
                    None,

                "validade":
                    item[
                        "validade"
                    ],

                "status":
                    "Disponível"
            })

        return transferido

    # =====================================================
    # SALDOS
    # =====================================================

    def saldo_disponivel(
        self,
        deposito,
        sku
    ):

        return sum(

            lote["qtd"]

            for lote

            in self.estoque[
                deposito
            ][sku]

            if lote[
                "status"
            ] == "Disponível"
        )

    def saldo_quarentena(
        self,
        deposito,
        sku
    ):

        return sum(

            lote["qtd"]

            for lote

            in self.estoque[
                deposito
            ][sku]

            if lote[
                "status"
            ] == "Quarentena"
        )

    def saldo_rejeitado(
        self,
        deposito,
        sku
    ):

        return sum(

            lote["qtd"]

            for lote

            in self.estoque[
                deposito
            ][sku]

            if lote[
                "status"
            ] == "Rejeitado"
        )

    def saldo_total(
        self,
        deposito,
        sku
    ):

        return sum(

            lote["qtd"]

            for lote

            in self.estoque[
                deposito
            ][sku]
        )

    # =====================================================
    # DATAFRAME
    # =====================================================

    def exportar_lotes(self):

        registros = []

        for deposito in self.estoque:

            for sku in self.estoque[
                deposito
            ]:

                registros.extend(

                    self.estoque[
                        deposito
                    ][sku]
                )

        return pd.DataFrame(
            registros
        )
