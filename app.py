import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pipeline import PipelineERP

st.set_page_config(layout="wide", page_title="DataForge Studio", page_icon="")
st.title("DataForge Studio - Simulação de ERP/WMS")

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.header("⚙️ Controle do Motor")
    st.info("Gere um gêmeo digital do seu ERP, incluindo histórico de compras, WMS e injeção de falhas.")
    
    if st.button("Executar Simulação (Completa)", use_container_width=True):
        with st.spinner("Gerando dimensões, simulando dias e injetando ruído..."):
            pipeline = PipelineERP()
            pipeline.executar()
        st.success("Pipeline finalizado com sucesso!")

# ==========================================
# FUNÇÃO DE CARREGAMENTO
# ==========================================
@st.cache_data(ttl=60)
def load_data(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

# Carregamento Fatos
df_mov = load_data("output/facts/fato_movimentacoes.csv")
df_ped = load_data("output/facts/fato_pedidos.csv")
df_rup = load_data("output/facts/fato_rupturas.csv")
df_snap = load_data("output/facts/fato_snapshot_estoque.csv")

# Carregamento Dimensões
df_prod = load_data("output/dimensions/dim_produto.csv")
df_forn = load_data("output/dimensions/dim_fornecedor.csv")

# Carregamento Qualidade
df_mov_sujo = load_data("output/quality/fato_movimentacoes.csv") 
if df_mov_sujo is None:
    df_mov_sujo = load_data("output/quality/movimentacoes_sujo.csv")

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Supply Chain", 
    "📦 WMS & Estoque", 
    "🗃️ Catálogo & Dimensões", 
    "⚠️ Data Quality & ETL"
])

if df_mov is None or df_ped is None:
    st.warning("👈 Nenhum dado encontrado. Execute a simulação no menu lateral.")
else:
    # ------------------------------------------
    # ABA 1: SUPPLY CHAIN
    # ------------------------------------------
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Pedidos Emitidos", f"{len(df_ped)}")
        col2.metric("💰 Valor Total Comprado", f"R$ {df_ped['valor_total'].sum():,.2f}")
        col3.metric("🔥 Valor Consumido (CMV)", f"R$ {df_mov[df_mov['tipo_movimentacao'] == 'Saída']['valor_total_mov'].sum():,.2f}")
        col4.metric("🚨 Ocorrências de Ruptura", f"{len(df_rup) if df_rup is not None else 0}")
        
        st.markdown("---")
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown("**Volume de Entradas vs Saídas ao longo do tempo**")
            df_mov['data'] = pd.to_datetime(df_mov['data_hora']).dt.date
            mov_timeline = df_mov.groupby(['data', 'tipo_movimentacao'])['quantidade'].sum().reset_index()
            fig1 = px.line(mov_timeline, x='data', y='quantidade', color='tipo_movimentacao', 
                           color_discrete_map={'Entrada': '#2ecc71', 'Saída': '#e74c3c'}, template='plotly_dark')
            st.plotly_chart(fig1, use_container_width=True)
            
        with col_graf2:
            st.markdown("**Status do Funil de Compras**")
            pedidos_status = df_ped['status'].value_counts().reset_index()
            fig2 = px.pie(pedidos_status, values='count', names='status', hole=0.4, template='plotly_dark')
            st.plotly_chart(fig2, use_container_width=True)

    # ------------------------------------------
    # ABA 2: WMS & ESTOQUE
    # ------------------------------------------
    with tab2:
        col_wms1, col_wms2 = st.columns(2)
        with col_wms1:
            st.markdown("**Saldo Atual por Depósito (Último Snapshot)**")
            if df_snap is not None:
                ultimo_snap = df_snap[df_snap['data'] == df_snap['data'].max()]
                saldo_deposito = ultimo_snap.groupby('deposito')['saldo_total'].sum().reset_index()
                fig3 = px.bar(saldo_deposito, x='deposito', y='saldo_total', color='deposito', template='plotly_dark')
                st.plotly_chart(fig3, use_container_width=True)
                
        with col_wms2:
            st.markdown("**Mapa de Calor de Rupturas**")
            if df_rup is not None and not df_rup.empty:
                rupturas_agg = df_rup.groupby(['deposito', 'criticidade']).size().reset_index(name='contagem')
                fig4 = px.density_heatmap(rupturas_agg, x='deposito', y='criticidade', z='contagem', template='plotly_dark')
                st.plotly_chart(fig4, use_container_width=True)

    # ------------------------------------------
    # ABA 3: CATÁLOGO E DIMENSÕES
    # ------------------------------------------
    with tab3:
        st.subheader("Governança de Dados Mestre")
        
        if df_prod is not None and df_forn is not None:
            col_cat1, col_cat2 = st.columns([1, 2])
            
            with col_cat1:
                st.markdown("**Distribuição Curva ABC (Por Valor)**")
                # Pega apenas os registros ativos do SCD Tipo 2
                prod_ativos = df_prod[df_prod['registro_ativo'] == True] if 'registro_ativo' in df_prod.columns else df_prod
                abc_counts = prod_ativos['curva_abc'].value_counts().reset_index()
                fig_abc = px.pie(abc_counts, values='count', names='curva_abc', 
                                 color='curva_abc', color_discrete_map={'A': '#2ecc71', 'B': '#f1c40f', 'C': '#95a5a6'},
                                 template='plotly_dark')
                st.plotly_chart(fig_abc, use_container_width=True)
                
            with col_cat2:
                st.markdown("**Lista de Fornecedores Ativos**")
                forn_ativos = df_forn[df_forn['registro_ativo'] == True] if 'registro_ativo' in df_forn.columns else df_forn
                st.dataframe(forn_ativos[['fornecedor_id', 'razao_social', 'estado', 'score_confiabilidade', 'lead_time_dias']], 
                             use_container_width=True, height=350)
                
            st.markdown("**Lista de Produtos (SKUs)**")
            st.dataframe(prod_ativos[['sku', 'descricao', 'categoria', 'curva_abc', 'estoque_minimo', 'estoque_maximo']], 
                         use_container_width=True)
        else:
            st.info("Dimensões não encontradas. Verifique os arquivos na pasta output/dimensions/")

    # ------------------------------------------
    # ABA 4: DATA QUALITY E LIMPEZA
    # ------------------------------------------
    with tab4:
        st.subheader("Chaos Engineering & Simulação de ETL")
        
        if df_mov_sujo is not None:
            st.markdown("O pipeline gerou dados corrompidos. Você pode visualizar os erros e simular uma rotina de limpeza.")
            
            col_caos1, col_caos2, col_caos3 = st.columns(3)
            qtd_original = len(df_mov)
            qtd_sujo = len(df_mov_sujo)
            
            col_caos1.metric("📑 Linhas Totais (Com Duplicatas)", f"{qtd_sujo}")
            col_caos2.metric("👻 Valores Nulos (SKU)", f"{df_mov_sujo['sku'].isna().sum()}")
            col_caos3.metric("💥 Outliers (Qtd > 100k)", f"{(df_mov_sujo['quantidade'] > 100000).sum()}")
            
            # Botão de Limpeza
            if st.button("🧹 Executar Limpeza de Dados (Sanitize)"):
                with st.spinner("Limpando duplicatas, removendo nulos e tratando outliers..."):
                    # 1. Remove duplicatas exatas
                    df_limpo = df_mov_sujo.drop_duplicates()
                    
                    # 2. Remove linhas onde a chave principal (SKU) é nula
                    df_limpo = df_limpo.dropna(subset=['sku'])
                    
                    # 3. Trata outliers (Exemplo: remove quantidades absurdas)
                    df_limpo = df_limpo[df_limpo['quantidade'] < 100000]
                    
                    st.success("Limpeza concluída! Veja o resultado abaixo.")
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("📑 Linhas Restantes", f"{len(df_limpo)}", delta=f"{len(df_limpo) - qtd_sujo}", delta_color="normal")
                    c2.metric("👻 Valores Nulos (SKU)", f"{df_limpo['sku'].isna().sum()}")
                    c3.metric("💥 Outliers (Qtd > 100k)", f"{(df_limpo['quantidade'] > 100000).sum()}")
                    
                    st.dataframe(df_limpo.head(15), use_container_width=True)
            else:
                st.markdown("**Amostra do Dado Corrompido**")
                st.dataframe(df_mov_sujo.head(15), use_container_width=True)
        else:
            st.info("Arquivo de movimentações sujas não encontrado. Verifique exportador.py.")