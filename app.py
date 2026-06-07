import streamlit as st
import pandas as pd
from pipeline import PipelineERP

st.set_page_config(layout="wide", page_title="DataForge Studio")
st.title("DataForge Studio - Simulação de ERP/WMS")

# Aba 1: Execução do Pipeline
with st.sidebar:
    st.header("Configurações")
    if st.button("Executar Simulação"):
        pipeline = PipelineERP()
        pipeline.executar()
        st.success("Pipeline finalizado!")

# Aba 2: Dashboards
tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🔍 Data Quality", "📦 Estoque & Lotes"])

with tab1:
    st.subheader("Indicadores de Performance")
    # Carregue os CSVs gerados na pasta /output
    try:
        df_mov = pd.read_csv("output/facts/fato_movimentacoes.csv")
        st.metric("Total de Movimentações", len(df_mov))
        st.line_chart(df_mov.groupby('data_hora')['quantidade'].sum())
    except:
        st.info("Execute o pipeline para carregar os dados.")

with tab2:
    st.subheader("Auditoria de Qualidade")
    # Mostrar nulos e duplicatas corrompidos pela classe DataQualitySimulator
    
with tab3:
    st.subheader("Snapshot por Depósito")
    # Gráfico de barras comparando saldo entre Depósito Principal e Canteiros