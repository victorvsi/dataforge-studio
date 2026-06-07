import uuid
import pandas as pd
from datetime import timedelta

from .qualidade import processar_quarentena
from .recebimento import receber_pedidos
from .consumo import processar_consumo
from .compras import avaliar_reposicao


class SimuladorERP:

    def __init__(
        self,
        estoque,
        df_produtos,
        df_fornecedores
    ):

        self.estoque = estoque

        self.produtos = (
            df_produtos
            .set_index("sku")
            .to_dict("index")
        )

        self.fornecedores = (
            df_fornecedores
            .set_index("fornecedor_id")
            .to_dict("index")
        )

        # -------------------------------------
        # Fatos
        # -------------------------------------

        self.movimentacoes = []

        self.pedidos = []

        self.rupturas = []

        self.backorders = []

        self.snapshot_estoque = []

        # -------------------------------------
        # Controle MRP
        # -------------------------------------

        self.em_transito = {}

        for sku in self.produtos:

            self.em_transito[sku] = 0

    # =====================================================
    # MOVIMENTAÇÕES
    # =====================================================

    def registrar_movimento(
        self,
        data_hora,
        sku,
        deposito,
        lote_id,
        tipo_movimentacao,
        motivo_movimentacao,
        quantidade,
        custo_unitario,
        saldo_apos_movimento
    ):
        registro = {
            "id_transacao": str(uuid.uuid4()),
            "data_hora": data_hora,
            "sku": sku,
            "deposito": deposito,
            "lote_id": lote_id,
            "tipo_movimentacao": tipo_movimentacao,
            "motivo_movimentacao": motivo_movimentacao,
            "quantidade": quantidade,
            "custo_unitario_mov": round(custo_unitario, 2),
            "valor_total_mov": round(quantidade * custo_unitario, 2),
            "saldo_apos_movimento": saldo_apos_movimento
        }
        self.movimentacoes.append(registro)

    def registrar_backorder(
        self,
        pedido,
        data,
        qtd_pendente
    ):
        self.backorders.append({
            "backorder_id": f"BO-{str(uuid.uuid4())[:8].upper()}",
            "pedido_id": pedido["pedido_id"],
            "sku": pedido["sku"],
            "data": data.date(),
            "qtd_pendente": qtd_pendente,
            "dias_em_aberto": 0,
            "status": "Pendente"
        })

    def registrar_pedido(
        self,
        pedido
    ):
        self.pedidos.append(pedido)

    def registrar_ruptura(
        self,
        data,
        sku,
        deposito,
        demanda,
        criticidade
    ):
        self.rupturas.append({
            "data": data.date(),
            "sku": sku,
            "deposito": deposito,
            "demanda_nao_atendida": demanda,
            "criticidade": criticidade
        })

    def registrar_snapshot(
        self,
        data
    ):

        for deposito in self.estoque.estoque:

            for sku in self.estoque.estoque[deposito]:

                saldo_disponivel = self.estoque.saldo_disponivel(deposito, sku)
                saldo_quarentena = self.estoque.saldo_quarentena(deposito, sku)
                saldo_rejeitado = self.estoque.saldo_rejeitado(deposito, sku)

                self.snapshot_estoque.append({
                    "data": data.date(),
                    "deposito": deposito,
                    "sku": sku,
                    "saldo_disponivel": saldo_disponivel,
                    "saldo_quarentena": saldo_quarentena,
                    "saldo_rejeitado": saldo_rejeitado,
                    "saldo_total": self.estoque.saldo_total(deposito, sku)
                })

    # =====================================================
    # ORQUESTRADOR DA SIMULAÇÃO
    # =====================================================

    def executar_dia(self, data):
        """
        Orquestra a execução de todos os processos de negócio para um único dia.
        """
        # 1. Itens em quarentena são inspecionados
        processar_quarentena(self, data)

        # 2. Pedidos com data de chegada para hoje são recebidos na doca
        receber_pedidos(self, data)

        # 3. A demanda diária é gerada e consumida do estoque
        processar_consumo(self, data)

        # 4. O MRP avalia a necessidade de novas compras
        avaliar_reposicao(self, data)

        # 5. Uma foto do estoque é tirada no final do dia
        self.registrar_snapshot(data)

    def executar(self, dias, data_inicio=None):
        """
        Executa o loop de simulação completo pelo número de dias especificado.
        """
        if data_inicio is None:
            data = pd.Timestamp.now() - pd.Timedelta(days=dias)
        else:
            data = pd.Timestamp(data_inicio)

        for _ in range(dias):
            data += pd.Timedelta(days=1)
            self.executar_dia(data)

        return self.resumo_execucao()

    # =====================================================
    # EXPORTAÇÕES E ESTATÍSTICAS
    # =====================================================

    def exportar_movimentacoes(self):
        return pd.DataFrame(self.movimentacoes)

    def exportar_pedidos(self):
        return pd.DataFrame(self.pedidos)

    def exportar_rupturas(self):
        return pd.DataFrame(self.rupturas)

    def exportar_backorders(self):
        return pd.DataFrame(self.backorders)

    def exportar_snapshot_estoque(self):
        return pd.DataFrame(self.snapshot_estoque)

    def resumo_execucao(self):
        """
        Calcula e retorna um resumo com as principais métricas da simulação.
        """
        valor_consumido = round(sum(
            mov.get("valor_total_mov", 0)
            for mov in self.movimentacoes if mov["tipo_movimentacao"] == "Saída"
        ), 2)

        valor_comprado = round(sum(
            ped.get("valor_total", 0) for ped in self.pedidos
        ), 2)

        return {
            "movimentacoes": len(self.movimentacoes),
            "pedidos": len(self.pedidos),
            "rupturas": len(self.rupturas),
            "backorders": len(self.backorders),
            "snapshots": len(self.snapshot_estoque),
            "valor_comprado": valor_comprado,
            "valor_consumido": valor_consumido
        }
