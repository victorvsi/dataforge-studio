import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pipeline import PipelineERP

# Configuração da Página
st.set_page_config(layout="wide", page_title="DataForge Studio", page_icon="🚀")
st.title("DataForge Studio - Simulação de ERP/WMS")

# ==========================================
# SIDEBAR (Controle da Simulação)
# ==========================================
with st.sidebar:
    st.header("⚙️ Controle do Motor")
    st.info("O DataForge gera um gêmeo digital do seu ERP, incluindo histórico de compras, WMS e injeção de falhas (Chaos Engineering).")
    
    if st.button("Executar Simulação (Completa)", use_container_width=True):
        with st.spinner("Gerando dimensões, simulando dias e injetando ruído..."):
            pipeline = PipelineERP()
            pipeline.executar()
        st.success("Pipeline finalizado com sucesso!")

# ==========================================
# FUNÇÃO AUXILIAR DE CARREGAMENTO
# ==========================================
@st.cache_data(ttl=60) # Cache para não recarregar do disco a todo clique
def load_data(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

# Carregamento dos Datasets Limpos (Facts)
df_mov = load_data("output/facts/fato_movimentacoes.csv")
df_ped = load_data("output/facts/fato_pedidos.csv")
df_rup = load_data("output/facts/fato_rupturas.csv")
df_snap = load_data("output/facts/fato_snapshot_estoque.csv")

# Carregamento dos Datasets Sujos (Quality)
df_mov_sujo = load_data("output/quality/fato_movimentacoes.csv")

# ==========================================
# INTERFACE PRINCIPAL (ABAS)
# ==========================================
tab1, tab2, tab3 = st.tabs(["📊 Visão Geral (Supply Chain)", "📦 Estoque & WMS", "⚠️ Auditoria de Qualidade (Caos)"])

if df_mov is None or df_ped is None:
    st.warning("👈 Nenhum dado encontrado. Por favor, clique em 'Executar Simulação' no menu lateral para gerar o Gêmeo Digital.")
else:
    # ------------------------------------------
    # ABA 1: VISÃO GERAL (SUPPLY CHAIN)
    # ------------------------------------------
    with tab1:
        st.subheader("Indicadores Logísticos e Financeiros")
        
        # KPIs Superiores
        col1, col2, col3, col4 = st.columns(4)
        total_comprado = df_ped['valor_total'].sum()
        total_consumido = df_mov[df_mov['tipo_movimentacao'] == 'Saída']['valor_total_mov'].sum()
        
        col1.metric("📦 Pedidos Emitidos", f"{len(df_ped)}")
        col2.metric("💰 Valor Total Comprado", f"R$ {total_comprado:,.2f}")
        col3.metric("🔥 Valor Consumido (CMV)", f"R$ {total_consumido:,.2f}")
        col4.metric("🚨 Ocorrências de Ruptura", f"{len(df_rup) if df_rup is not None else 0}")
        
        st.markdown("---")
        
        # Gráficos de Linha do Tempo
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            st.markdown("**Volume de Entradas vs Saídas ao longo do tempo**")
            # Preparação dos dados temporais
            df_mov['data'] = pd.to_datetime(df_mov['data_hora']).dt.date
            mov_timeline = df_mov.groupby(['data', 'tipo_movimentacao'])['quantidade'].sum().reset_index()
            
            fig1 = px.line(mov_timeline, x='data', y='quantidade', color='tipo_movimentacao', 
                           color_discrete_map={'Entrada': '#2ecc71', 'Saída': '#e74c3c'},
                           template='plotly_dark')
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_graf2:
            st.markdown("**Status do Funil de Compras**")
            pedidos_status = df_ped['status'].value_counts().reset_index()
            pedidos_status.columns = ['Status', 'Quantidade']
            
            fig2 = px.pie(pedidos_status, values='Quantidade', names='Status', hole=0.4,
                          color='Status', color_discrete_map={'Recebido': '#3498db', 'Em Trânsito': '#f1c40f'},
                          template='plotly_dark')
            st.plotly_chart(fig2, use_container_width=True)

    # ------------------------------------------
    # ABA 2: ESTOQUE E WMS (SNAPSHOTS E RUPTURAS)
    # ------------------------------------------
    with tab2:
        st.subheader("Distribuição Física e Gargalos")
        
        col_wms1, col_wms2 = st.columns(2)
        
        with col_wms1:
            st.markdown("**Saldo Atual por Depósito (Último Snapshot)**")
            if df_snap is not None and not df_snap.empty:
                df_snap['data'] = pd.to_datetime(df_snap['data'])
                ultima_data = df_snap['data'].max()
                ultimo_snap = df_snap[df_snap['data'] == ultima_data]
                
                saldo_deposito = ultimo_snap.groupby('deposito')['saldo_total'].sum().reset_index()
                fig3 = px.bar(saldo_deposito, x='deposito', y='saldo_total', text='saldo_total',
                              color='deposito', template='plotly_dark')
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Dados de snapshot indisponíveis.")
                
        with col_wms2:
            st.markdown("**Mapa de Calor de Rupturas (Falta de Material)**")
            if df_rup is not None and not df_rup.empty:
                rupturas_agg = df_rup.groupby(['deposito', 'criticidade']).size().reset_index(name='contagem')
                fig4 = px.density_heatmap(rupturas_agg, x='deposito', y='criticidade', z='contagem',
                                          color_continuous_scale='Reds', template='plotly_dark')
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.success("Excelente! Nenhuma ruptura de estoque registrada nesta simulação.")

    # ------------------------------------------
    # ABA 3: DATA QUALITY E CAOS
    # ------------------------------------------
    with tab3:
        st.subheader("Engenharia do Caos e Monitoramento de ETL")
        st.write("Visão do *DataFrame* corrompido intencionalmente para testes de resiliência de Data Warehouses.")
        
        if df_mov_sujo is not None:
            col_caos1, col_caos2, col_caos3 = st.columns(3)
            
            # Cálculo dos "estragos"
            qtd_original = len(df_mov)
            qtd_sujo = len(df_mov_sujo)
            duplicatas = qtd_sujo - qtd_original
            nulos_sku = df_mov_sujo['sku'].isna().sum()
            outliers = (df_mov_sujo['quantidade'] >= 999999).sum()
            
            col_caos1.metric("📑 Linhas Duplicadas Injetadas", f"{duplicatas}")
            col_caos2.metric("👻 Valores Nulos (SKU/Depósito)", f"{nulos_sku}")
            col_caos3.metric("💥 Outliers Matemáticos (Qtd absurda)", f"{outliers}")
            
            st.markdown("---")
            st.markdown("**Distribuição de Eventos CDC (Change Data Capture)**")
            if 'operacao_cdc' in df_mov_sujo.columns:
                cdc_counts = df_mov_sujo['operacao_cdc'].value_counts().reset_index()
                cdc_counts.columns = ['Operação', 'Registros']
                fig5 = px.bar(cdc_counts, x='Operação', y='Registros', color='Operação',
                              color_discrete_map={'I': '#2ecc71', 'U': '#f39c12', 'D': '#e74c3c'},
                              template='plotly_dark')
                st.plotly_chart(fig5, use_container_width=True)
                
            st.markdown("**Amostra do Dado Corrompido**")
            st.dataframe(df_mov_sujo.head(15), use_container_width=True)
        else:
            st.info("Dados corrompidos não encontrados. Verifique a exportação da qualidade.")