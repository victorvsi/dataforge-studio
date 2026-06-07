import random

def _consumir_sku(simulador, data, deposito, sku, demanda):
    """
    Função auxiliar para consumir uma quantidade de um SKU específico de um depósito,
    utilizando a lógica FEFO.
    """
    consumidos, restante = simulador.estoque.consumir_fefo(deposito, sku, demanda)

    for item in consumidos:
        saldo = simulador.estoque.saldo_disponivel(deposito, sku)
        simulador.registrar_movimento(
            data_hora=data,
            sku=sku,
            deposito=deposito,
            lote_id=item["lote_id"],
            tipo_movimentacao="Saída",
            motivo_movimentacao="Consumo",
            quantidade=item["quantidade"],
            custo_unitario=item["custo_unitario"],
            saldo_apos_movimento=saldo
        )
    return restante

def processar_consumo(simulador, data):
    """
    Simula o consumo diário de materiais no depósito principal, registrando
    saídas de estoque e possíveis rupturas.
    """
    deposito_principal = "DEP-001"

    for sku, produto in simulador.produtos.items():
        demanda = int(produto["consumo_medio_dia"] * random.uniform(0.70, 1.30))
        if demanda <= 0:
            continue

        restante = _consumir_sku(simulador, data, deposito_principal, sku, demanda)

        if restante > 0:
            simulador.registrar_ruptura(
                data=data,
                sku=sku,
                deposito=deposito_principal,
                demanda=restante,
                criticidade=produto["criticidade"]
            )