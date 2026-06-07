import uuid
import random
from datetime import timedelta

def avaliar_reposicao(simulador, data):
    """
    Avalia a necessidade de reposição de estoque para cada SKU no depósito principal
    e gera pedidos de compra caso o ponto de reposição seja atingido.
    """
    deposito = "DEP-001"

    for sku, produto in simulador.produtos.items():
        saldo_atual = simulador.estoque.saldo_disponivel(deposito, sku)
        saldo_futuro = saldo_atual + simulador.em_transito[sku]

        if saldo_futuro > produto["ponto_reposicao"]:
            continue

        quantidade_compra = max(0, produto["estoque_maximo"] - saldo_futuro)
        if quantidade_compra <= 0:
            continue

        fornecedor = simulador.fornecedores[produto["fornecedor_id"]]
        score = fornecedor["score_confiabilidade"]

        atraso = 0
        if score == "Baixo":
            atraso = random.randint(3, 10)
        elif score == "Médio":
            atraso = random.randint(1, 4)

        lead_time_real = produto["lead_time"] + atraso
        pedido_id = f"PED-{str(uuid.uuid4())[:8].upper()}"
        data_recebimento = data + timedelta(days=lead_time_real)
        valor_total = round(quantidade_compra * produto["custo_unitario"], 2)

        pedido = {
            "pedido_id": pedido_id,
            "sku": sku,
            "fornecedor_id": produto["fornecedor_id"],
            "quantidade": quantidade_compra,
            "custo_unitario": produto["custo_unitario"],
            "valor_total": valor_total,
            "score_fornecedor": score,
            "lead_time_planejado": produto["lead_time"],
            "lead_time_real": lead_time_real,
            "dias_atraso": atraso,
            "data_emissao": data,
            "data_prevista": data_recebimento,
            "data_recebimento_real": None,
            "status": "Em Trânsito"
        }

        simulador.registrar_pedido(pedido)
        simulador.em_transito[sku] += quantidade_compra