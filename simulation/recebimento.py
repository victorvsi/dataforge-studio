import random

def receber_pedidos(simulador, data):
    """
    Verifica e processa o recebimento de pedidos de compra que estão em trânsito
    e cuja data prevista de chegada é o dia atual.
    """
    deposito = "DEP-001"

    for pedido in simulador.pedidos:
        if pedido["status"] != "Em Trânsito":
            continue

        if pedido["data_prevista"].date() != data.date():
            continue

        sku = pedido["sku"]
        produto = simulador.produtos[sku]

        percentual_entrega = random.uniform(0.60, 1.00)
        qtd_recebida = int(pedido["quantidade"] * percentual_entrega)
        saldo_pendente = pedido["quantidade"] - qtd_recebida

        if qtd_recebida <= 0:
            continue

        if saldo_pendente > 0:
            pedido["status"] = "Parcialmente Recebido"
            simulador.registrar_backorder(pedido, data, saldo_pendente)
        else:
            pedido["status"] = "Recebido"

        lote_id = simulador.estoque.receber_lote(
            deposito=deposito,
            sku=sku,
            quantidade=qtd_recebida,
            custo_unitario=produto["custo_unitario"],
            controla_validade=produto["controla_validade"]
        )

        pedido["data_recebimento_real"] = data
        simulador.em_transito[sku] -= qtd_recebida

        saldo = simulador.estoque.saldo_quarentena(deposito, sku)
        simulador.registrar_movimento(
            data_hora=data,
            sku=sku,
            deposito=deposito,
            lote_id=lote_id,
            tipo_movimentacao="Entrada",
            motivo_movimentacao="Recebimento",
            quantidade=qtd_recebida,
            custo_unitario=produto["custo_unitario"],
            saldo_apos_movimento=saldo
        )