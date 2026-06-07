import json
import pandas as pd

from config import *


class Exportador:

    @staticmethod
    def salvar_dimensoes(

        df_produtos,
        df_fornecedores,
        df_depositos,
        df_calendario
    ):

        df_produtos.to_csv(
            DIMENSIONS_DIR /
            "dim_produto.csv",
            index=False
        )

        df_fornecedores.to_csv(
            DIMENSIONS_DIR /
            "dim_fornecedor.csv",
            index=False
        )

        df_depositos.to_csv(
            DIMENSIONS_DIR /
            "dim_deposito.csv",
            index=False
        )

        if df_calendario is not None:
            df_calendario.to_csv(
                DIMENSIONS_DIR /
                "dim_calendario.csv",
                index=False
            )

    @staticmethod
    def salvar_fatos(
        simulador
    ):

        simulador.exportar_movimentacoes().to_csv(

            FACTS_DIR /
            "fato_movimentacoes.csv",

            index=False
        )

        simulador.exportar_pedidos().to_csv(

            FACTS_DIR /
            "fato_pedidos.csv",

            index=False
        )

        simulador.exportar_rupturas().to_csv(

            FACTS_DIR /
            "fato_rupturas.csv",

            index=False
        )

        simulador.exportar_backorders().to_csv(

            FACTS_DIR /
            "fato_backorders.csv",

            index=False
        )

        simulador.exportar_snapshot_estoque().to_csv(

            FACTS_DIR /
            "fato_snapshot_estoque.csv",

            index=False
        )

    @staticmethod
    def salvar_parquet(
        simulador
    ):

        simulador.exportar_movimentacoes().to_parquet(

            PARQUET_DIR /
            "fato_movimentacoes.parquet",

            index=False
        )

        simulador.exportar_pedidos().to_parquet(

            PARQUET_DIR /
            "fato_pedidos.parquet",

            index=False
        )

        simulador.exportar_rupturas().to_parquet(

            PARQUET_DIR /
            "fato_rupturas.parquet",

            index=False
        )

        simulador.exportar_backorders().to_parquet(

            PARQUET_DIR /
            "fato_backorders.parquet",

            index=False
        )

        simulador.exportar_snapshot_estoque().to_parquet(

            PARQUET_DIR /
            "fato_snapshot_estoque.parquet",

            index=False
        )

    @staticmethod
    def salvar_quality(

        mov_sujo,
        ped_sujo,
        snap_sujo
    ):

        mov_sujo.to_csv(

            QUALITY_DIR /
            "fato_movimentacoes_sujo.csv",

            index=False
        )

        ped_sujo.to_csv(

            QUALITY_DIR /
            "fato_pedidos_sujo.csv",

            index=False
        )

        snap_sujo.to_csv(

            QUALITY_DIR /
            "fato_snapshot_sujo.csv",

            index=False
        )

    @staticmethod
    def salvar_metadata(
        simulador
    ):

        with open(

            METADATA_DIR /
            "estatisticas_execucao.json",

            "w",
            encoding="utf-8"

        ) as f:

            json.dump(

                simulador.resumo_execucao(),

                f,

                ensure_ascii=False,

                indent=4,

                default=str
            )
