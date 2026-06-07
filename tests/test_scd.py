import pytest
import pandas as pd
from transforms.scd import aplicar_scd_tipo2

@pytest.fixture
def setup_scd_data():
    """Prepara DataFrames de exemplo para os testes de SCD Tipo 2."""
    data_atual = {
        'fornecedor_id': ['F-1', 'F-2', 'F-3'],
        'razao_social': ['Fornecedor A', 'Fornecedor B', 'Fornecedor C'],
        'cidade': ['São Paulo', 'Rio de Janeiro', 'Belo Horizonte'],
        'versao': [1, 1, 1],
        'registro_ativo': [True, True, True],
        'vigencia_inicio': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-01')],
        'vigencia_fim': [pd.Timestamp('9999-12-31'), pd.Timestamp('9999-12-31'), pd.Timestamp('9999-12-31')]
    }
    df_atual = pd.DataFrame(data_atual)

    # Cenário:
    # F-1: Sem alteração
    # F-2: Cidade alterada (deve gerar nova versão)
    # F-3: Não existe mais no novo lote (deve ser expirado)
    # F-4: Novo fornecedor
    data_novo = {
        'fornecedor_id': ['F-1', 'F-2', 'F-4'],
        'razao_social': ['Fornecedor A', 'Fornecedor B', 'Fornecedor D'],
        'cidade': ['São Paulo', 'Niterói', 'Curitiba'],
        'versao': [1, 1, 1],
        'registro_ativo': [True, True, True],
        'vigencia_inicio': [pd.Timestamp('2023-01-01'), pd.Timestamp('2023-01-01'), pd.Timestamp('2024-01-01')],
        'vigencia_fim': [pd.Timestamp('9999-12-31'), pd.Timestamp('9999-12-31'), pd.Timestamp('9999-12-31')]
    }
    df_novo = pd.DataFrame(data_novo)

    chave_negocio = ['fornecedor_id']
    colunas_scd = ['razao_social', 'cidade']

    return df_atual, df_novo, chave_negocio, colunas_scd

def test_scd_novo_registro(setup_scd_data):
    """
    Valida se um novo registro (F-4) é adicionado corretamente.
    """
    df_atual, df_novo, chave, colunas = setup_scd_data
    df_resultado = aplicar_scd_tipo2(df_atual, df_novo, chave, colunas)

    novo_registro = df_resultado[df_resultado['fornecedor_id'] == 'F-4']
    assert len(novo_registro) == 1, "Deveria haver apenas um registro para o novo fornecedor."
    assert novo_registro.iloc[0]['versao'] == 1
    assert novo_registro.iloc[0]['registro_ativo'] == True

def test_scd_registro_atualizado(setup_scd_data):
    """
    Valida se um registro atualizado (F-2) gera uma nova versão e expira a antiga.
    """
    df_atual, df_novo, chave, colunas = setup_scd_data
    df_resultado = aplicar_scd_tipo2(df_atual, df_novo, chave, colunas)

    registros_f2 = df_resultado[df_resultado['fornecedor_id'] == 'F-2']
    assert len(registros_f2) == 2, "Deveria haver duas versões para o fornecedor F-2."

    versao_antiga = registros_f2[registros_f2['versao'] == 1].iloc[0]
    assert versao_antiga['registro_ativo'] == False
    assert versao_antiga['vigencia_fim'] < pd.Timestamp('9999-12-31')
    assert versao_antiga['cidade'] == 'Rio de Janeiro'

    versao_nova = registros_f2[registros_f2['versao'] == 2].iloc[0]
    assert versao_nova['registro_ativo'] == True
    assert versao_nova['vigencia_fim'] == pd.Timestamp('9999-12-31')
    assert versao_nova['cidade'] == 'Niterói'

def test_scd_registro_deletado(setup_scd_data):
    """
    Valida se um registro removido (F-3) é corretamente expirado.
    """
    df_atual, df_novo, chave, colunas = setup_scd_data
    df_resultado = aplicar_scd_tipo2(df_atual, df_novo, chave, colunas)

    registro_f3 = df_resultado[df_resultado['fornecedor_id'] == 'F-3']
    assert len(registro_f3) == 1, "Deveria haver apenas uma versão para o fornecedor F-3."
    
    registro_expirado = registro_f3.iloc[0]
    assert registro_expirado['registro_ativo'] == False
    assert registro_expirado['vigencia_fim'] < pd.Timestamp('9999-12-31')

def test_scd_registro_inalterado(setup_scd_data):
    """
    Valida se um registro inalterado (F-1) permanece como está.
    """
    df_atual, df_novo, chave, colunas = setup_scd_data
    df_resultado = aplicar_scd_tipo2(df_atual, df_novo, chave, colunas)

    registro_f1 = df_resultado[df_resultado['fornecedor_id'] == 'F-1']
    assert len(registro_f1) == 1, "Deveria haver apenas uma versão para o fornecedor F-1."
    
    registro_ativo = registro_f1.iloc[0]
    assert registro_ativo['registro_ativo'] == True
    assert registro_ativo['versao'] == 1
    assert registro_ativo['vigencia_fim'] == pd.Timestamp('9999-12-31')

def test_scd_contagem_total(setup_scd_data):
    """
    Valida a contagem total de registros após a aplicação do SCD.
    """
    df_atual, df_novo, chave, colunas = setup_scd_data
    df_resultado = aplicar_scd_tipo2(df_atual, df_novo, chave, colunas)

    # Esperado:
    # F-1: 1 registro (inalterado)
    # F-2: 2 registros (versão 1 expirada, versão 2 ativa)
    # F-3: 1 registro (expirado)
    # F-4: 1 registro (novo)
    # Total = 5
    assert len(df_resultado) == 5