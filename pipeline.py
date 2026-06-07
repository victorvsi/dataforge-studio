from generators.fornecedores import (
    gerar_fornecedores
)

from generators.depositos import (
    gerar_depositos
)

from generators.produtos import (
    gerar_produtos
)

from generators.updates import (
    gerar_atualizacoes_fornecedores,
    gerar_atualizacoes_produtos
)

from transforms.scd import (
    aplicar_scd_tipo2
)

from simulation.estoque import (
    EstoqueWMS
)

from simulation.eventos import (
    SimuladorERP
)

from quality.qualidade import (
    DataQualitySimulator
)

from exports.exportador import (
    Exportador
)

from config import *


class PipelineERP:

    def __init__(self):

        self.df_fornecedores = None
        self.df_depositos = None
        self.df_produtos = None

        self.df_fornecedores_historico = None
        self.df_produtos_historico = None

        self.simulador = None

        self.mov_sujo = None
        self.ped_sujo = None
        self.snap_sujo = None

    # ==================================================
    # DIMENSÕES
    # ==================================================

    def gerar_dimensoes_iniciais(self):

        print(
            "\n[1/6] Gerando dimensões (Carga Inicial)..."
        )

        self.df_fornecedores = (
            gerar_fornecedores(
                NUM_FORNECEDORES
            )
        )

        self.df_depositos = (
            gerar_depositos()
        )

        self.df_produtos = (
            gerar_produtos(
                self.df_fornecedores,
                NUM_SKUS
            )
        )

        # A primeira carga é a versão 1 do histórico
        self.df_fornecedores_historico = self.df_fornecedores.copy()
        self.df_produtos_historico = self.df_produtos.copy()

        print(
            "Dimensões geradas."
        )

    # ==================================================
    # SCD TIPO 2
    # ==================================================

    def aplicar_scd(self):
        print("\n[2/6] Aplicando SCD Tipo 2...")

        # Simula a chegada de um novo lote de dados de fornecedores com alterações
        df_fornecedores_novo_lote = gerar_atualizacoes_fornecedores(
            self.df_fornecedores,
            taxa_mudanca=TAXA_MUDANCA_FORNECEDOR,
            taxa_novos=TAXA_NOVOS_FORNECEDORES
        )

        self.df_fornecedores_historico = aplicar_scd_tipo2(
            df_atual=self.df_fornecedores_historico,
            df_novo=df_fornecedores_novo_lote,
            chave_negocio=['fornecedor_id'],
            colunas_scd=['razao_social', 'cidade', 'estado', 'score_confiabilidade', 'lead_time_dias']
        )

        # Simula a chegada de um novo lote de dados de produtos com alterações
        df_produtos_novo_lote = gerar_atualizacoes_produtos(
            self.df_produtos,
            taxa_mudanca=TAXA_MUDANCA_PRODUTO
        )

        self.df_produtos_historico = aplicar_scd_tipo2(
            df_atual=self.df_produtos_historico,
            df_novo=df_produtos_novo_lote,
            chave_negocio=['sku'],
            colunas_scd=['descricao', 'custo_unitario', 'peso_kg', 'volume_m3', 'criticidade']
        )
        print("SCD Tipo 2 aplicado.")

    # ==================================================
    # SIMULAÇÃO
    # ==================================================

    def executar_simulacao(self):

        print(
            "\n[3/6] Executando simulação..."
        )

        # A simulação deve usar a versão ATIVA mais recente das dimensões
        df_produtos_ativos = self.df_produtos_historico[
            self.df_produtos_historico['registro_ativo'] == True
        ].copy()  # O .copy() é crucial aqui
        df_fornecedores_ativos = self.df_fornecedores_historico[
            self.df_fornecedores_historico['registro_ativo'] == True
        ].copy()  # O .copy() é crucial aqui

        estoque = EstoqueWMS()

        estoque.gerar_estoque_inicial(

            df_produtos_ativos,

            self.df_depositos
        )

        self.simulador = (

            SimuladorERP(

                estoque=estoque,

                df_produtos=df_produtos_ativos,

                df_fornecedores=df_fornecedores_ativos
            )
        )

        self.simulador.executar(
            dias=DIAS_SIMULACAO
        )

        print(
            "Simulação concluída."
        )

    # ==================================================
    # DATA QUALITY
    # ==================================================

    def gerar_datasets_sujos(self):

        print(
            "\n[4/6] Aplicando problemas de qualidade..."
        )

        quality = (
            DataQualitySimulator()
        )

        self.mov_sujo = (

            quality
            .corromper_movimentacoes(

                self.simulador
                .exportar_movimentacoes()
            )
        )

        self.ped_sujo = (

            quality
            .corromper_pedidos(

                self.simulador
                .exportar_pedidos()
            )
        )

        self.snap_sujo = (

            quality
            .corromper_snapshot(

                self.simulador
                .exportar_snapshot_estoque()
            )
        )

        print(
            "Data Quality aplicada."
        )

    # ==================================================
    # EXPORTAÇÃO
    # ==================================================

    def exportar(self):

        print(
            "\n[5/6] Exportando datasets..."
        )

        # Salva as dimensões HISTÓRICAS completas
        Exportador.salvar_dimensoes(
            df_produtos=self.df_produtos_historico,
            df_fornecedores=self.df_fornecedores_historico,
            df_depositos=self.df_depositos,
            df_calendario=None  # Calendário não foi implementado
        )

        Exportador.salvar_fatos(
            self.simulador
        )

        Exportador.salvar_parquet(
            self.simulador
        )

        Exportador.salvar_quality(

            self.mov_sujo,

            self.ped_sujo,

            self.snap_sujo
        )

        Exportador.salvar_metadata(
            self.simulador
        )

        print(
            "Exportação concluída."
        )

    # ==================================================
    # RESUMO
    # ==================================================

    def imprimir_resumo(self):

        print(
            "\n[6/6] Resumo da execução\n"
        )

        print(
            self.simulador
            .resumo_execucao()
        )

        print(
            "\nDistribuição Curva ABC\n"
        )

        print(

            self.df_produtos_historico.loc[
                self.df_produtos_historico['registro_ativo'] == True, "curva_abc"
            ].value_counts()
        )

    # ==================================================
    # PIPELINE COMPLETO
    # ==================================================

    def executar(self):

        self.gerar_dimensoes_iniciais()

        self.aplicar_scd()

        self.executar_simulacao()

        self.gerar_datasets_sujos()

        self.exportar()

        self.imprimir_resumo()

        print(
            "\nPipeline finalizado."
        )