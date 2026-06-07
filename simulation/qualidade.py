import random

def processar_quarentena(simulador, data):
    """
    Processa os lotes em quarentena, aprovando ou rejeitando-os com base
    em uma taxa de aprovação e registra as movimentações correspondentes.
    """
    for deposito in simulador.estoque.estoque:
        for sku in simulador.estoque.estoque[deposito]:
            lotes = simulador.estoque.estoque[deposito][sku]
            for lote in lotes:
                if lote["status"] != "Quarentena":
                    continue

                aprovado = random.random() < 0.95
                if aprovado:
                    lote["status"] = "Disponível"
                    saldo = simulador.estoque.saldo_disponivel(deposito, sku)
                    simulador.registrar_movimento(
                        data_hora=data,
                        sku=sku,
                        deposito=deposito,
                        lote_id=lote["lote_id"],
                        tipo_movimentacao="Entrada",
                        motivo_movimentacao="Liberação Quarentena",
                        quantidade=lote["qtd"],
                        custo_unitario=lote["custo_unitario"],
                        saldo_apos_movimento=saldo
                    )
                else:
                    lote["status"] = "Rejeitado"
                    simulador.registrar_movimento(
                        data_hora=data,
                        sku=sku,
                        deposito=deposito,
                        lote_id=lote["lote_id"],
                        tipo_movimentacao="Baixa",
                        motivo_movimentacao="Rejeição Qualidade",
                        quantidade=lote["qtd"],
                        custo_unitario=lote["custo_unitario"],
                        saldo_apos_movimento=0
                    )