import pytest
from engine.gerador_almoxarifado import gerar_dados_almoxarifado

def test_colunas_obrigatorias():
    """Valida se o DataFrame possui exatamente a estrutura de colunas esperada."""
    df = gerar_dados_almoxarifado(5)
    colunas_esperadas = ['id_transacao', 'data_movimentacao', 'item', 'tipo_movimentacao', 'quantidade']
    assert list(df.columns) == colunas_esperadas

def test_quantidade_valida_positiva():
    """Valida se todas as quantidades geradas são estritamente maiores que zero."""
    df = gerar_dados_almoxarifado(50)
    assert (df['quantidade'] > 0).all(), "Falha: O gerador criou registros com quantidade <= 0."

def test_integridade_tipos_movimentacao():
    """Garante que a coluna tipo_movimentacao aceita apenas os valores de negócio definidos."""
    df = gerar_dados_almoxarifado(50)
    tipos_gerados = set(df['tipo_movimentacao'].unique())
    assert tipos_gerados.issubset({'Entrada', 'Saída'}), "Falha: Tipo de movimentação não reconhecido."