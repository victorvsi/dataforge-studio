from pathlib import Path

# --- Diretórios ---
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
DIMENSIONS_DIR = OUTPUT_DIR / "dimensions"
FACTS_DIR = OUTPUT_DIR / "facts"
PARQUET_DIR = OUTPUT_DIR / "parquet"
QUALITY_DIR = OUTPUT_DIR / "quality"
METADATA_DIR = OUTPUT_DIR / "metadata"

# Cria os diretórios se não existirem
for path in [OUTPUT_DIR, DIMENSIONS_DIR, FACTS_DIR, PARQUET_DIR, QUALITY_DIR, METADATA_DIR]:
    path.mkdir(parents=True, exist_ok=True)

# --- Parâmetros da Simulação ---
NUM_FORNECEDORES = 50
NUM_SKUS = 200
DIAS_SIMULACAO = 90

# --- Parâmetros SCD ---
TAXA_MUDANCA_FORNECEDOR = 0.10  # 10% dos fornecedores terão dados atualizados
TAXA_NOVOS_FORNECEDORES = 0.05  # 5% de novos fornecedores serão adicionados
TAXA_MUDANCA_PRODUTO = 0.15     # 15% dos produtos terão o custo atualizado