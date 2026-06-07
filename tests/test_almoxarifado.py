import pytest
from engine.gerador_almoxarifado import gerar_mestre_materiais

def test_unicidade_sku():
    """Garante que o gerador não crie SKUs duplicados."""
    df = gerar_mestre_materiais(500)
    assert df['sku'].is_unique, "Falha: SKUs duplicados encontrados."

def test_distribuicao_curva_abc():
    """Valida se a proporção da Curva ABC respeita rigorosamente a regra 20/30/50."""
    total = 1000
    df = gerar_mestre_materiais(total)
    
    # Conta a proporção de cada categoria
    proporcoes = df['curva_abc'].value_counts(normalize=True)
    
    assert proporcoes['A'] == pytest.approx(0.20, rel=0.001), "Erro na proporção da Curva A"
    assert proporcoes['B'] == pytest.approx(0.30, rel=0.001), "Erro na proporção da Curva B"
    assert proporcoes['C'] == pytest.approx(0.50, rel=0.001), "Erro na proporção da Curva C"

def test_medidas_fisicas_validas():
    """Nenhum item pode ter peso ou volume nulo ou negativo."""
    df = gerar_mestre_materiais(100)
    assert (df['peso_kg'] > 0).all(), "Valores inválidos detectados na coluna peso_kg."
    assert (df['volume_m3'] > 0).all(), "Valores inválidos detectados na coluna volume_m3."

def test_formato_enderecamento():
    """Valida se o endereço consolidado segue a estrutura Rua-Prateleira-Nível-Posição."""
    df = gerar_mestre_materiais(50)
    # Testa se a string possui o formato X-00-00-000 usando regex
    padrao_valido = df['endereco_fisico'].str.match(r'^[A-Z]-\d{2}-\d{2}-\d{3}$')
    assert padrao_valido.all(), "O formato de endereçamento físico foi quebrado."

from engine.gerador_almoxarifado import gerar_movimentacoes

def test_saldo_estoque_nunca_negativo():
    """Garante a regra de ouro: O saldo após movimentação não pode ser menor que zero."""
    df_mestre = gerar_mestre_materiais(100)
    df_mov = gerar_movimentacoes(df_mestre, 1000)
    assert (df_mov['saldo_apos_movimento'] >= 0).all(), "Falha: Transação gerou saldo negativo."

def test_ordem_cronologica_movimentacoes():
    """Garante que as transações fluem linearmente no tempo (Time Series válida)."""
    df_mestre = gerar_mestre_materiais(10)
    df_mov = gerar_movimentacoes(df_mestre, 500)
    # Verifica se a coluna de datas está estritamente ordenada de forma crescente
    assert df_mov['data_hora'].is_monotonic_increasing, "Falha: As datas não estão em ordem cronológica."

def test_volume_movimentacao_curva_abc():
    """Valida se a regra de negócio da Curva ABC (Regra 80/20) está sendo aplicada no volume transacional."""
    df_mestre = gerar_mestre_materiais(200)
    df_mov = gerar_movimentacoes(df_mestre, 5000)
    
    # Realiza um JOIN para trazer a classificação ABC para a tabela de movimentos
    df_analise = df_mov.merge(df_mestre[['sku', 'curva_abc']], on='sku')
    
    proporcoes = df_analise['curva_abc'].value_counts(normalize=True)
    
    # Tolerância de 5% (0.05) devido à natureza aleatória do sorteio
    assert proporcoes['A'] == pytest.approx(0.80, abs=0.05), "Erro no volume transacional da Curva A"
    assert proporcoes['B'] == pytest.approx(0.15, abs=0.05), "Erro no volume transacional da Curva B"
    assert proporcoes['C'] == pytest.approx(0.05, abs=0.05), "Erro no volume transacional da Curva C"