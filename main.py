from pipeline import PipelineERP
import time


def main():

    print("Iniciando pipeline de geração de dados ERP...")
    start_time = time.time()

    try:
        pipeline = PipelineERP()
        pipeline.executar()
    except Exception as e:
        print(f"\n--- ERRO DURANTE A EXECUÇÃO DO PIPELINE ---")
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        print("---------------------------------------------")
    finally:
        end_time = time.time()
        print(f"\nTempo total de execução: {end_time - start_time:.2f} segundos.")


if __name__ == "__main__":
    main()