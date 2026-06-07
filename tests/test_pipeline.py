import pytest
from pathlib import Path
from pipeline import PipelineERP
from config import OUTPUT_DIR, FACTS_DIR, DIMENSIONS_DIR

@pytest.fixture(scope="module")
def pipeline_executado():
    """
    Executa o pipeline uma vez e disponibiliza a instância para todos os testes do módulo.
    Isso economiza tempo, pois o pipeline não precisa rodar para cada teste.
    """
    print("\nExecutando pipeline completo para a suíte de testes...")
    pipeline = PipelineERP()
    pipeline.executar()
    print("Pipeline executado.")
    return pipeline

def test_pipeline_executa_sem_erros(pipeline_executado):
    """Verifica se a instância do pipeline foi criada e executada."""
    assert pipeline_executado is not None
    assert pipeline_executado.simulador is not None

def test_geracao_arquivos_fatos(pipeline_executado):
    """Verifica se os principais arquivos de fatos foram criados."""
    arquivos_fatos_esperados = [
        "fato_movimentacoes.csv",
        "fato_pedidos.csv",
        "fato_rupturas.csv",
        "fato_backorders.csv",
        "fato_snapshot_estoque.csv"
    ]
    for arquivo in arquivos_fatos_esperados:
        caminho_arquivo = FACTS_DIR / arquivo
        assert caminho_arquivo.exists(), f"Arquivo de fato esperado não foi encontrado: {arquivo}"
        assert caminho_arquivo.stat().st_size > 50, f"Arquivo de fato parece estar vazio: {arquivo}"

def test_geracao_arquivos_dimensoes(pipeline_executado):
    """Verifica se os arquivos de dimensão (históricos) foram criados."""
    arquivos_dim_esperados = [
        "dim_produto.csv",
        "dim_fornecedor.csv",
        "dim_deposito.csv"
    ]
    for arquivo in arquivos_dim_esperados:
        caminho_arquivo = DIMENSIONS_DIR / arquivo
        assert caminho_arquivo.exists(), f"Arquivo de dimensão esperado não foi encontrado: {arquivo}"
        assert caminho_arquivo.stat().st_size > 50, f"Arquivo de dimensão parece estar vazio: {arquivo}"