import random
import numpy as np
import pandas as pd


class DataQualitySimulator:
      def __init__(

        self,

        taxa_nulos=0.02,

        taxa_duplicatas=0.01,

        taxa_outliers=0.005,

        taxa_fk_orfa=0.003,

        taxa_datas_invalidas=0.002,

        taxa_negativos=0.002
    ):

        self.taxa_nulos = taxa_nulos

        self.taxa_duplicatas = taxa_duplicatas

        self.taxa_outliers = taxa_outliers

        self.taxa_fk_orfa = taxa_fk_orfa

        self.taxa_datas_invalidas = taxa_datas_invalidas

        self.taxa_negativos = taxa_negativos

      def aplicar_cdc(
        self,
        df
    ):

        df = df.copy()

        df["operacao_cdc"] = np.random.choice(

            ["I", "U", "D"],

            size=len(df),

            p=[0.97, 0.02, 0.01]
        )

        return df
      def aplicar_duplicatas(
        self,
        df
    ):

        df = df.copy()

        qtd = int(
            len(df)
            *
            self.taxa_duplicatas
        )

        if qtd <= 0:
            return df

        duplicados = df.sample(
            qtd
        )

        return pd.concat(

            [
                df,
                duplicados
            ],

            ignore_index=True
        )
      
      def aplicar_nulos(
        self,
        df,
        colunas
    ):

        df = df.copy()

        qtd = int(
            len(df)
            *
            self.taxa_nulos
        )

        for coluna in colunas:

            if coluna not in df.columns:
                continue

            idx = np.random.choice(

                df.index,

                size=min(
                    qtd,
                    len(df)
                ),

                replace=False
            )

            df.loc[
                idx,
                coluna
            ] = np.nan

        return df
      
      def aplicar_outliers(
        self,
        df,
        coluna
    ):

        df = df.copy()

        if coluna not in df.columns:
            return df

        qtd = int(
            len(df)
            *
            self.taxa_outliers
        )

        if qtd <= 0:
            return df

        idx = np.random.choice(

            df.index,

            size=qtd,

            replace=False
        )

        df.loc[
            idx,
            coluna
        ] *= random.randint(
            100,
            1000
        )

        return df
      
      def aplicar_negativos(
        self,
        df,
        coluna
    ):

        df = df.copy()

        if coluna not in df.columns:
            return df

        qtd = int(
            len(df)
            *
            self.taxa_negativos
        )

        idx = np.random.choice(

            df.index,

            size=qtd,

            replace=False
        )

        df.loc[
            idx,
            coluna
        ] *= -1

        return df
      def aplicar_fk_orfa(
        self,
        df,
        coluna_fk
    ):

        df = df.copy()

        if coluna_fk not in df.columns:
            return df

        qtd = int(
            len(df)
            *
            self.taxa_fk_orfa
        )

        idx = np.random.choice(

            df.index,

            size=qtd,

            replace=False
        )

        df.loc[
            idx,
            coluna_fk
        ] = "INVALIDO_999999"

        return df
      
      def aplicar_datas_invalidas(
        self,
        df,
        coluna
    ):

        df = df.copy()

        if coluna not in df.columns:
            return df

        qtd = int(
            len(df)
            *
            self.taxa_datas_invalidas
        )

        idx = np.random.choice(

            df.index,

            size=qtd,

            replace=False
        )

        df.loc[
            idx,
            coluna
        ] = pd.Timestamp(
            "1900-01-01"
        )

        return df
      def corromper_movimentacoes(
        self,
        df
    ):

        df = self.aplicar_cdc(df)

        df = self.aplicar_duplicatas(df)

        df = self.aplicar_nulos(

            df,

            [
                "sku",
                "deposito",
                "lote_id"
            ]
        )

        df = self.aplicar_outliers(

            df,

            "quantidade"
        )

        df = self.aplicar_negativos(

            df,

            "valor_total_mov"
        )

        return df
      
      def corromper_pedidos(
        self,
        df
    ):

        df = self.aplicar_cdc(df)

        df = self.aplicar_fk_orfa(

            df,

            "fornecedor_id"
        )

        df = self.aplicar_outliers(

            df,

            "quantidade"
        )

        df = self.aplicar_datas_invalidas(

            df,

            "data_prevista"
        )

        return df
  
      def corromper_snapshot(
        self,
        df
    ):

        df = self.aplicar_nulos(

            df,

            [
                "deposito",
                "sku"
            ]
        )

        df = self.aplicar_outliers(

            df,

            "saldo_total"
        )

        return df
      
      