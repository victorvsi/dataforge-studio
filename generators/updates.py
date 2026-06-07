import random
import pandas as pd
from faker import Faker

fake = Faker("pt_BR")

def gerar_atualizacoes_fornecedores(df_fornecedores: pd.DataFrame, taxa_mudanca=0.1, taxa_novos=0.05):
    """Gera um novo DataFrame com fornecedores atualizados, novos e inalterados."""
    df_novo = df_fornecedores.copy()

    # 1. Atualizar existentes
    indices_para_mudar = df_novo.sample(frac=taxa_mudanca).index
    for idx in indices_para_mudar:
        df_novo.loc[idx, 'score_confiabilidade'] = random.choices(['Alto', 'Médio', 'Baixo'], weights=[60, 30, 10])[0]
        df_novo.loc[idx, 'lead_time_dias'] = random.randint(2, 30)

    # 2. Adicionar novos
    num_novos = int(len(df_fornecedores) * taxa_novos)
    if num_novos > 0:
        novos_fornecedores = []
        total_fornecedores = len(df_fornecedores)
        for i in range(num_novos):
            novos_fornecedores.append({
                "fornecedor_id": f"FORN-{total_fornecedores+i+1:05}",
                "cnpj": fake.cnpj(), "razao_social": fake.company(), "cidade": fake.city(),
                "estado": random.choice(["SP", "RJ", "MG"]), "lead_time_dias": random.randint(2, 30),
                "score_confiabilidade": random.choices(['Alto', 'Médio', 'Baixo'], weights=[60, 30, 10])[0],
                "vigencia_inicio": pd.Timestamp.now().normalize(), "vigencia_fim": pd.Timestamp('9999-12-31'),
                "registro_ativo": True, "versao": 1
            })
        df_novo = pd.concat([df_novo, pd.DataFrame(novos_fornecedores)], ignore_index=True)

    return df_novo

def gerar_atualizacoes_produtos(df_produtos: pd.DataFrame, taxa_mudanca=0.1):
    """Gera um novo DataFrame com produtos atualizados."""
    df_novo = df_produtos.copy()
    indices_para_mudar = df_novo.sample(frac=taxa_mudanca).index
    for idx in indices_para_mudar:
        custo_atual = df_novo.loc[idx, 'custo_unitario']
        df_novo.loc[idx, 'custo_unitario'] = round(custo_atual * random.uniform(0.95, 1.05), 2)
    return df_novo