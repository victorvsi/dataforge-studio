import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pipeline import PipelineERP

st.set_page_config(layout="wide", page_title="DataForge Studio", page_icon="🚀")
st.title("🚀 DataForge Studio - Command Center")

# ==========================================
# FUNÇÃO DE CARREGAMENTO E PREPARAÇÃO
# ==========================================
@st.cache_data(ttl=60)
def load_data(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame() 

# Carregamento Fatos
df_mov = load_data("output/facts/fato_movimentacoes.csv")
df_ped = load_data("output/facts/fato_pedidos.csv")
df_rup = load_data("output/facts/fato_rupturas.csv")
df_snap = load_data("output/facts/fato_snapshot_estoque.csv")

# Carregamento Dimensões
df_prod = load_data("output/dimensions/dim_produto.csv")
df_forn = load_data("output/dimensions/dim_fornecedor.csv")

# Carregamento Qualidade 
df_mov_sujo = load_data("output/quality/fato_movimentacoes_sujo.csv") 

# ==========================================
# SIDEBAR: CONTROLES E FILTROS
# ==========================================
with st.sidebar:
    st.header("⚙️ Motor de Simulação")
    if st.button("Executar Simulação", use_container_width=True, type="primary"):
        with st.spinner("Construindo Gêmeo Digital..."):
            pipeline = PipelineERP()
            pipeline.executar()
        st.success("Sucesso! Atualizando painéis...")
        if hasattr(st, "rerun"): 
            st.rerun() 
        else: 
            st.experimental_rerun()
    
    st.markdown("---")
    
    # Filtros Globais 
    st.header("🔍 Filtros Globais")
    if not df_mov.empty:
        df_mov['data'] = pd.to_datetime(df_mov['data_hora']).dt.date
        data_min, data_max = df_mov['data'].min(), df_mov['data'].max()
        
        filtro_datas = st.date_input("Período de Análise", [data_min, data_max], min_value=data_min, max_value=data_max)
        
        depositos_disponiveis = df_mov['deposito'].unique().tolist()
        filtro_depositos = st.multiselect("Selecione os Depósitos", depositos_disponiveis, default=depositos_disponiveis)
    else:
        st.info("Gere a simulação para habilitar os filtros.")
        filtro_datas = None
        filtro_depositos = []

    st.markdown("---")
    
    # Exportação Unificada (OBT)
    st.header("📤 Integração BI")
    st.caption("Gera uma tabela desnormalizada cruzando Fatos e Dimensões para testes em Power BI / Tableau.")
    if not df_mov.empty and not df_prod.empty:
        @st.cache_data
        def gerar_csv_unificado():
            df_unificado = df_mov.merge(df_prod[['sku', 'categoria', 'curva_abc', 'fornecedor_id']], on='sku', how='left')
            if not df_forn.empty:
                df_unificado = df_unificado.merge(df_forn[['fornecedor_id', 'estado', 'score_confiabilidade']], on='fornecedor_id', how='left')
            return df_unificado.to_csv(index=False).encode('utf-8')
            
        csv_data = gerar_csv_unificado()
        st.download_button(
            label="Baixar CSV Unificado (OBT)",
            data=csv_data,
            file_name="dataset_unificado_bi.csv",
            mime="text/csv",
            use_container_width=True
        )

# ==========================================
# APLICAÇÃO DOS FILTROS (LÓGICA)
# ==========================================
if not df_mov.empty and filtro_datas and len(filtro_datas) == 2:
    start_date, end_date = filtro_datas
    mask_mov = (df_mov['data'] >= start_date) & (df_mov['data'] <= end_date) & (df_mov['deposito'].isin(filtro_depositos))
    df_mov_filtered = df_mov.loc[mask_mov]
else:
    df_mov_filtered = df_mov

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
if df_mov.empty:
    st.warning("👈 Banco de dados vazio. Configure a simulação no menu lateral.")
else:
    # DEFINIÇÃO CORRETA DAS 4 ABAS
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Performance Financeira e Logística", 
        "📦 Operação WMS e Rupturas", 
        "🗃️ Governança de Dados (Catálogo)",
        "🛡️ Data Contracts & Qualidade"
    ])

    # ------------------------------------------
    # ABA 1: PERFORMANCE
    # ------------------------------------------
    with tab1:
        st.markdown("### Visão Geral da Operação")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Movimentações (Período)", f"{len(df_mov_filtered):,}")
        c2.metric("Valor Consumido (CMV)", f"R$ {df_mov_filtered[df_mov_filtered['tipo_movimentacao'] == 'Saída']['valor_total_mov'].sum():,.2f}")
        c3.metric("Entradas Físicas (R$)", f"R$ {df_mov_filtered[df_mov_filtered['tipo_movimentacao'] == 'Entrada']['valor_total_mov'].sum():,.2f}")
        
        st.markdown("---")
        
        st.markdown("**Ritmo de Operação: Entradas vs Saídas**")
        if not df_mov_filtered.empty:
            timeline = df_mov_filtered.groupby(['data', 'tipo_movimentacao'])['quantidade'].sum().reset_index()
            fig1 = px.line(timeline, x='data', y='quantidade', color='tipo_movimentacao', 
                           color_discrete_map={'Entrada': '#2ecc71', 'Saída': '#e74c3c'}, template='plotly_dark')
            st.plotly_chart(fig1, use_container_width=True)
            
            with st.expander("💡 O que este gráfico me diz?"):
                st.write("""
                * **Sincronia Logística:** Picos de 'Entrada' muito distantes dos picos de 'Saída' indicam que o dinheiro está ficando parado no estoque.
                * **Gargalos de Doca:** Se as entradas ocorrerem todas no mesmo dia da semana, sua doca pode estar sobrecarregada.
                """)

    # ------------------------------------------
    # ABA 2: WMS & RUPTURAS
    # ------------------------------------------
    with tab2:
        st.markdown("### Saúde Física do Estoque")
        
        col_wms1, col_wms2 = st.columns(2)
        with col_wms1:
            st.markdown("**Distribuição de Volume por Depósito**")
            mov_por_dep = df_mov_filtered.groupby('deposito')['quantidade'].sum().reset_index()
            fig2 = px.bar(mov_por_dep, x='deposito', y='quantidade', color='deposito', template='plotly_dark')
            st.plotly_chart(fig2, use_container_width=True)
            
            with st.expander("💡 Insight de Armazenagem"):
                st.write("Identifique desbalanceamento de carga. Canteiros com muito volume podem precisar de transferência de equipe.")

        with col_wms2:
            st.markdown("**Mapa de Calor: Onde estamos falhando? (Rupturas)**")
            if not df_rup.empty:
                rupturas_agg = df_rup.groupby(['deposito', 'criticidade']).size().reset_index(name='contagem')
                fig3 = px.density_heatmap(rupturas_agg, x='deposito', y='criticidade', z='contagem', 
                                          color_continuous_scale='Reds', template='plotly_dark')
                st.plotly_chart(fig3, use_container_width=True)
                
                with st.expander("💡 Insight de Nível de Serviço"):
                    st.write("""
                    * **Criticidade Alta no Vermelho:** Alerta gravíssimo. Falta de materiais críticos paralisa a operação.
                    * **Concentração em Canteiros:** Indica que a rotina de transferência do CD para o Canteiro está lenta.
                    """)
            else:
                st.success("Nenhuma ruptura detectada no período atual.")

    # ------------------------------------------
    # ABA 3: GOVERNANÇA E DIMENSÕES
    # ------------------------------------------
    with tab3:
        st.markdown("### Qualidade e Distribuição do Catálogo Mestre")
        
        if not df_prod.empty:
            col_cat1, col_cat2 = st.columns([1, 2])
            
            with col_cat1:
                st.markdown("**Curva ABC de Materiais**")
                prod_ativos = df_prod[df_prod['registro_ativo'] == True] if 'registro_ativo' in df_prod.columns else df_prod
                abc = prod_ativos['curva_abc'].value_counts().reset_index()
                fig4 = px.pie(abc, values='count', names='curva_abc', color='curva_abc', 
                              color_discrete_map={'A': '#2ecc71', 'B': '#f1c40f', 'C': '#95a5a6'}, template='plotly_dark')
                st.plotly_chart(fig4, use_container_width=True)
                
            with col_cat2:
                st.markdown("**Matriz de Fornecedores Ativos**")
                forn_ativos = df_forn[df_forn['registro_ativo'] == True] if not df_forn.empty and 'registro_ativo' in df_forn.columns else df_forn
                st.dataframe(forn_ativos[['fornecedor_id', 'razao_social', 'estado', 'score_confiabilidade', 'lead_time_dias']], 
                             use_container_width=True, height=350)
                
            with st.expander("💡 Insight de Compras"):
                st.write("""
                * A **Curva A** representa os 20% dos itens que consomem 80% do orçamento.
                * Monitore fornecedores com `score_confiabilidade` 'Baixo' fornecendo itens Críticos.
                """)

    # ------------------------------------------
    # ABA 4: DATA QUALITY E LIMPEZA
    # ------------------------------------------
    with tab4:
        st.subheader("🛡️ Data Contracts & Validações de Qualidade")
        st.markdown("""
        Painel de Observabilidade de Dados. Valida as regras de negócio da tabela Fato antes da exportação para o BI.
        """)
        
        if df_mov_sujo is not None and not df_mov_sujo.empty:
            total_linhas = len(df_mov_sujo)
            
            # Execução dos Testes 
            falhas_sku = df_mov_sujo['sku'].isna().sum()
            taxa_sku = ((total_linhas - falhas_sku) / total_linhas)
            
            qtd_limpa = df_mov_sujo['quantidade'].fillna(0)
            falhas_qtd = (~qtd_limpa.between(1, 100000)).sum()
            taxa_qtd = ((total_linhas - falhas_qtd) / total_linhas)
            
            falhas_dup = df_mov_sujo.duplicated().sum()
            taxa_dup = ((total_linhas - falhas_dup) / total_linhas)

            st.markdown("### 📋 Report Card da Ingestão")
            
            def exibir_expectation(col, titulo, taxa, falhas):
                with col:
                    status = "✅ Pass" if falhas == 0 else "❌ Fail"
                    delta = "Sem erros" if falhas == 0 else f"-{falhas} registros"
                    st.metric(f"{titulo} ({status})", f"{taxa*100:.1f}% Saudável", delta=delta, delta_color="inverse")
                    st.progress(float(taxa))

            c1, c2, c3 = st.columns(3)
            exibir_expectation(c1, "Completude (SKU)", taxa_sku, falhas_sku)
            exibir_expectation(c2, "Limites (Outliers)", taxa_qtd, falhas_qtd)
            exibir_expectation(c3, "Unicidade", taxa_dup, falhas_dup)
            
            st.markdown("---")
            
            st.markdown("### 🧹 Quarentena e Limpeza de Dados (Sanitize)")
            
            if st.button("Executar Pipeline de Correção", type="primary"):
                with st.spinner("Tratando dados..."):
                    df_limpo = df_mov_sujo.drop_duplicates()
                    df_limpo = df_limpo.dropna(subset=['sku'])
                    df_limpo = df_limpo[df_limpo['quantidade'].between(1, 100000)]
                    
                    st.success(f"Pipeline finalizado! {total_linhas - len(df_limpo)} linhas ruins descartadas.")
                    
                    col_limp1, col_limp2 = st.columns([1, 3])
                    with col_limp1:
                        st.metric("Total de Linhas Aprovadas", f"{len(df_limpo):,}")
                        st.metric("Aprovação do Data Contract", "100%", delta="Pronto para BI")
                    with col_limp2:
                        st.dataframe(df_limpo.head(10), use_container_width=True)
            else:
                st.markdown("**Amostra dos Dados Reprovados (Com ruído)**")
                st.dataframe(df_mov_sujo.head(10), use_container_width=True)
        else:
            st.info("Arquivo de movimentações corrompidas não encontrado.")