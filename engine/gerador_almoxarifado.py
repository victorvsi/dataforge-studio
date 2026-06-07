import pandas as pd
from faker import Faker
import random

# Inicializa o gerador de dados falsos com localização brasileira
fake = Faker('pt_BR')

def gerar_dados_almoxarifado(num_linhas=100):
    dados = []
    itens_validos = [
        'Cimento CP II (Saco 50kg)', 
        'Vergalhão 10mm (Barra 12m)', 
        'Tinta Acrílica Branca (18L)', 
        'Areia Fina (m³)'
    ]
    
    for _ in range(num_linhas):
        dados.append({
            'id_transacao': str(fake.uuid4()),
            'data_movimentacao': fake.date_between(start_date='-1y', end_date='today'),
            'item': random.choice(itens_validos),
            'tipo_movimentacao': random.choice(['Entrada', 'Saída']),
            'quantidade': random.randint(1, 100)
        })
        
    df = pd.DataFrame(dados)
    
    df = df.sort_values('data_movimentacao').reset_index(drop=True)
    
    return df