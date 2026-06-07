import pandas as pd
from faker import Faker
from datetime import timedelta
import random

fake = Faker('pt_BR')

def gerar_mestre_materiais(total_itens=1000):
    """
    Gera o catálogo estático de itens (Mestre de Materiais) 
    com Curva ABC, dimensões físicas e endereçamento.
    """
    dados = []
    
    # Cálculo para a distribuição da Curva ABC
    qtd_a = int(total_itens * 0.20)
    qtd_b = int(total_itens * 0.30)
    qtd_c = total_itens - qtd_a - qtd_b # Garante que a soma sempre bata 100%
    
    curva_abc = ['A'] * qtd_a + ['B'] * qtd_b + ['C'] * qtd_c
    random.shuffle(curva_abc) # Embaralha as classificações
    
    # Domínios de Dados
    categorias = ['Construção', 'Elétrica', 'Hidráulica', 'Pintura', 'Ferramentas', 'EPI', 'Fixação']
    unidades = ['UN', 'KG', 'L', 'M', 'CX', 'PCT', 'RL']
    
    for i in range(total_itens):
        categoria = random.choice(categorias)
        
        # Geração do Endereçamento
        rua = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        prateleira = random.randint(1, 20)
        nivel = random.randint(1, 5)
        posicao = random.randint(1, 100)
        endereco = f"{rua}-{prateleira:02d}-{nivel:02d}-{posicao:03d}"
        
        dados.append({
            'sku': f"SKU-{str(i+1).zfill(6)}",
            'descricao': f"Produto {fake.word().capitalize()} - {categoria}",
            'categoria': categoria,
            'unidade': random.choice(unidades),
            'peso_kg': round(random.uniform(0.1, 50.0), 2),
            'volume_m3': round(random.uniform(0.001, 2.0), 3),
            'fornecedor': fake.company(),
            'curva_abc': curva_abc[i],
            'endereco_fisico': endereco,
            'rua': rua,
            'prateleira': prateleira,
            'nivel': nivel,
            'posicao': posicao
        })
        
    return pd.DataFrame(dados)

def gerar_movimentacoes(df_mestre, num_transacoes=5000):
    """
    Gera o histórico de transações de estoque baseado no Mestre de Materiais,
    garantindo saldo nunca negativo e respeitando o volume da Curva ABC.
    """
    # Mapeamento de SKUs por classificação ABC
    skus_a = df_mestre[df_mestre['curva_abc'] == 'A']['sku'].tolist()
    skus_b = df_mestre[df_mestre['curva_abc'] == 'B']['sku'].tolist()
    skus_c = df_mestre[df_mestre['curva_abc'] == 'C']['sku'].tolist()
    
    # Dicionário de estado: rastreia o saldo atual de cada SKU
    estoque_atual = {sku: 0 for sku in df_mestre['sku']}
    
    # Geração de uma linha do tempo ordenada para simular logs reais
    data_inicial = fake.date_time_between(start_date='-1y', end_date='-11m')
    datas_transacoes = sorted([data_inicial + timedelta(hours=random.randint(1, 8000)) for _ in range(num_transacoes)])
    
    movimentacoes = []
    
    for i in range(num_transacoes):
        # Regra da Curva ABC: Itens 'A' representam 80% do volume de movimentação
        curva_sorteada = random.choices(['A', 'B', 'C'], weights=[80, 15, 5])[0]
        
        if curva_sorteada == 'A' and skus_a:
            sku = random.choice(skus_a)
        elif curva_sorteada == 'B' and skus_b:
            sku = random.choice(skus_b)
        else:
            sku = random.choice(skus_c)
            
        saldo = estoque_atual[sku]
        
        # Regra de Negócio: Impede saída se não houver saldo
        if saldo == 0:
            tipo = 'Entrada'
            qtd = random.randint(50, 500)
        else:
            # Viés de consumo: 70% de chance de ser uma saída caso haja saldo
            tipo = random.choices(['Entrada', 'Saída'], weights=[30, 70])[0]
            if tipo == 'Saída':
                qtd = random.randint(1, saldo) # Limita a saída ao saldo disponível
            else:
                qtd = random.randint(50, 500)
                
        # Atualiza o estado em memória
        if tipo == 'Entrada':
            estoque_atual[sku] += qtd
        else:
            estoque_atual[sku] -= qtd
            
        movimentacoes.append({
            'id_transacao': str(fake.uuid4()),
            'data_hora': datas_transacoes[i],
            'sku': sku,
            'tipo_movimentacao': tipo,
            'quantidade': qtd,
            'saldo_apos_movimento': estoque_atual[sku]
        })
        
    return pd.DataFrame(movimentacoes)