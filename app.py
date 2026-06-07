import streamlit as st
import pandas as pd
import plotly.express as px
import os
from pipeline import PipelineERP

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(layout="wide", page_title="DataForge Studio", page_icon="📈")
st.title("📈 DataForge Studio: Gêmeo Digital de Supply Chain")

# ==========================================
# FUNÇÃO DE CARREGAMENTO E CACHE
# ==========================================
@st.cache_data(ttl=300) # Cache por 5 minutos
def load_data(path):
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except Exception as e:
            st.error(f"Erro ao carregar {path}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# ==========================================
# CARREGAMENTO E PREPARAÇÃO DOS DADOS
# ==========================================
with st.spinner("Carregando datasets..."):
    # Fatos
    df_mov = load_data("output/facts/fato_movimentacoes.csv")
    df_ped = load_data("output/facts/fato_pedidos.csv")
    df_rup = load_data("output/facts/fato_rupturas.csv")
    df_snap = load_data("output/facts/fato_snapshot_estoque.csv")
    df_back = load_data("output/facts/fato_backorders.csv")

    # Dimensões
    df_prod = load_data("output/dimensions/dim_produto.csv")
    df_forn = load_data("output/dimensions/dim_fornecedor.csv")
    df_dep = load_data("output/dimensions/dim_deposito.csv")

    # Qualidade
    df_mov_sujo = load_data("output/quality/fato_movimentacoes_sujo.csv")

# ==========================================
# REGRAS DE NEGÓCIO E ENRIQUECIMENTO
# ==========================================
df_vendas = pd.DataFrame()
if not df_mov.empty and not df_prod.empty:
    # Usar apenas a versão ativa dos produtos para o merge
    df_prod_ativos = df_prod[df_prod['registro_ativo'] == True].copy()
    
    # Criação da visão de "Vendas" aplicando 40% de margem sobre o custo
    df_vendas = df_mov[df_mov['tipo_movimentacao'] == 'Saída'].copy()
    df_vendas['faturamento'] = df_vendas['valor_total_mov'] * 1.40
    df_vendas['lucro'] = df_vendas['faturamento'] - df_vendas['valor_total_mov']
    
    # Conversão de data e criação de colunas temporais
    df_vendas['data'] = pd.to_datetime(df_vendas['data_hora']).dt.date
    df_vendas['mes_ano'] = pd.to_datetime(df_vendas['data_hora']).dt.to_period('M').astype(str)

    # Cruzamento com Produtos para ter Categoria, Curva ABC e Fornecedor
    df_vendas = df_vendas.merge(
        df_prod_ativos[['sku', 'descricao', 'curva_abc', 'categoria', 'fornecedor_id']], 
        on='sku', 
        how='left'
    )

# ==========================================
# SIDEBAR E FILTROS
# ==========================================
with st.sidebar:
    st.header("⚙️ Motor de Dados")
    if st.button("Executar Simulação Completa", type="primary", use_container_width=True):
        with st.spinner("Executando pipeline... Isso pode levar um minuto."):
            pipeline = PipelineERP()
            pipeline.executar()
        st.success("Pipeline executado e dados atualizados!")
        st.cache_data.clear() # Limpa o cache para recarregar os dados
        st.rerun()
    
    st.markdown("---")
    st.header("🔍 Filtros Globais")
    
    if not df_vendas.empty:
        # Filtro de Data
        min_data = df_vendas['data'].min()
        max_data = df_vendas['data'].max()
        filtro_data = st.date_input(
            "Período de Análise",
            value=(min_data, max_data),
            min_value=min_data,
            max_value=max_data,
            help="Selecione o intervalo de datas para a análise."
        )
        if len(filtro_data) != 2: # Garante que o filtro de data sempre tenha início e fim
            filtro_data = (min_data, max_data)

        # Filtros de Categoria e Curva ABC
        categorias_disponiveis = df_vendas['categoria'].unique().tolist()
        filtro_categorias = st.multiselect("Categorias de Produto", categorias_disponiveis, default=categorias_disponiveis)

        curvas_disponiveis = sorted(df_vendas['curva_abc'].unique().tolist())
        filtro_curvas = st.multiselect("Curva ABC", curvas_disponiveis, default=curvas_disponiveis)
        
        # Aplicação dos filtros
        df_vendas_filtrado = df_vendas[
            (df_vendas['data'] >= filtro_data[0]) &
            (df_vendas['data'] <= filtro_data[1]) &
            (df_vendas['categoria'].isin(filtro_categorias)) &
            (df_vendas['curva_abc'].isin(filtro_curvas))
        ]
    else:
        st.info("Gere os dados para habilitar os filtros.")
        df_vendas_filtrado = pd.DataFrame()

    # OBT Export
    st.markdown("---")
    st.header("📤 Integração (BI & Analytics)")
    
    @st.cache_data
    def gerar_obt(df_vendas_obt, df_forn_obt):
        # Prepara a OBT (One Big Table) para exportação
        df_obt = df_vendas_obt.merge(df_forn_obt[['fornecedor_id', 'razao_social', 'cidade', 'estado']], on='fornecedor_id', how='left')
        return df_obt.to_csv(index=False).encode('utf-8')
    
    if not df_vendas_filtrado.empty:
        st.download_button(
            "Baixar OBT de Vendas (CSV)", 
            data=gerar_obt(df_vendas_filtrado, df_forn), 
            file_name="obt_vendas_analise.csv", 
            mime="text/csv", 
            use_container_width=True,
            help="Baixa a tabela de vendas enriquecida com dados de produtos e fornecedores, pronta para análise."
        )

# ==========================================
# INTERFACE PRINCIPAL (ABAS)
# ==========================================
if df_mov.empty:
    st.warning("👈 O banco de dados está vazio. Clique em 'Executar Simulação Completa' no menu lateral para gerar os dados.")
else:
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 **Visão Geral Financeira**", 
        "🏆 **Análise de Produtos**", 
        "🚚 **Operações & Fornecedores**",
        "🛡️ **Qualidade de Dados**",
        "🔎 **Explorador de Dados**"
    ])

    # ------------------------------------------
    # ABA 1: VISÃO GERAL FINANCEIRA
    # ------------------------------------------
    with tab1:
        st.markdown("### Indicadores Chave de Performance (KPIs)")
        
        total_faturado = df_vendas_filtrado['faturamento'].sum()
        total_custo = df_vendas_filtrado['valor_total_mov'].sum()
        total_lucro = df_vendas_filtrado['lucro'].sum()
        margem_lucro = (total_lucro / total_faturado) * 100 if total_faturado > 0 else 0
        
        # Custo da Ruptura (Receita Perdida)
        df_rup_ativos = df_rup.merge(df_prod[df_prod['registro_ativo'] == True][['sku', 'custo_unitario']], on='sku', how='left')
        receita_perdida = (df_rup_ativos['demanda_nao_atendida'] * df_rup_ativos['custo_unitario'] * 1.40).sum()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Faturamento Bruto", f"R$ {total_faturado:,.2f}", help="Receita total gerada pelas saídas de estoque (vendas simuladas).")
        c2.metric("Custo da Mercadoria (CMV)", f"R$ {total_custo:,.2f}", help="Custo total dos produtos que saíram do estoque.")
        c3.metric("Lucro Bruto", f"R$ {total_lucro:,.2f}", delta=f"{margem_lucro:.1f}% Margem", help="Faturamento - Custo da Mercadoria.")
        c4.metric("Receita Perdida (Ruptura)", f"R$ {receita_perdida:,.2f}", delta_color="inverse", help="Estimativa de receita não realizada devido à falta de estoque para atender a demanda.")
        
        st.markdown("---")
        st.markdown("### Evolução Mensal: Faturamento vs. Custo")
        
        vendas_mensais = df_vendas_filtrado.groupby('mes_ano')[['faturamento', 'valor_total_mov']].sum().reset_index()
        vendas_mensais.rename(columns={'valor_total_mov': 'Custo da Mercadoria'}, inplace=True)
        vendas_mensais = vendas_mensais.sort_values('mes_ano')
        
        fig_dre = px.bar(vendas_mensais, x='mes_ano', y=['faturamento', 'Custo da Mercadoria'], barmode='group',
                         title="Faturamento vs. Custo da Mercadoria Vendida (CMV) por Mês",
                         labels={'value': 'Valor (R$)', 'mes_ano': 'Mês/Ano', 'variable': 'Métrica'},
                         color_discrete_map={'faturamento': '#2ecc71', 'Custo da Mercadoria': '#e74c3c'}, 
                         template='streamlit',
                         hover_data={"mes_ano": True, "value": ":.2f"})
        fig_dre.update_layout(hovermode="x unified")
        st.plotly_chart(fig_dre, use_container_width=True)

    # ------------------------------------------
    # ABA 2: ANÁLISE DE PRODUTOS
    # ------------------------------------------
    with tab2:
        st.markdown("### Desempenho por Produto e Categoria")
        
        col_p1, col_p2 = st.columns([1, 2])
        
        with col_p1:
            st.markdown("**Lucratividade por Curva ABC**")
            abc_lucro = df_vendas_filtrado.groupby('curva_abc')['lucro'].sum().reset_index()
            fig_abc = px.pie(abc_lucro, values='lucro', names='curva_abc', hole=0.4,
                             title="Distribuição do Lucro por Curva ABC",
                             color='curva_abc', color_discrete_map={'A': '#27AE60', 'B': '#F1C40F', 'C': '#95A5A6'}, 
                             template='streamlit')
            fig_abc.update_traces(textinfo='percent+label', pull=[0.05, 0, 0])
            st.plotly_chart(fig_abc, use_container_width=True)
            
        with col_p2:
            st.markdown("**Top 10 Produtos Mais Lucrativos**")
            top_produtos = df_vendas_filtrado.groupby(['sku', 'descricao', 'curva_abc'])[['quantidade', 'faturamento', 'lucro']].sum().reset_index()
            top_produtos = top_produtos.sort_values(by='lucro', ascending=False).head(10)
            
            st.dataframe(
                top_produtos.style.format({
                    'faturamento': 'R$ {:,.2f}',
                    'lucro': 'R$ {:,.2f}',
                    'quantidade': '{:,.0f}'
                }).background_gradient(cmap='Greens', subset=['lucro']), 
                use_container_width=True, hide_index=True
            )
        
        st.markdown("---")
        st.markdown("**Análise de Lucratividade por Categoria e Produto (Treemap)**")
        fig_tree_prod = px.treemap(df_vendas_filtrado, path=[px.Constant("Todas as Categorias"), 'categoria', 'curva_abc', 'descricao'], 
                                   values='lucro',
                                   color='lucro',
                                   color_continuous_scale='Greens',
                                   title="Navegue na Lucratividade: Categoria > Curva ABC > Produto",
                                   template='streamlit',
                                   hover_data={'lucro': ':.2f'})
        fig_tree_prod.update_layout(margin = dict(t=50, l=25, r=25, b=25))
        st.plotly_chart(fig_tree_prod, use_container_width=True)

    # ------------------------------------------
    # ABA 3: OPERAÇÕES & FORNECEDORES
    # ------------------------------------------
    with tab3:
        st.markdown("### Análise de Compras e Desempenho de Fornecedores")
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("**Valor de Pedidos por Fornecedor e Status**")
            if not df_ped.empty and not df_forn.empty:
                df_forn_ativos = df_forn[df_forn['registro_ativo'] == True]
                ped_forn = df_ped.merge(df_forn_ativos[['fornecedor_id', 'razao_social']], on='fornecedor_id', how='left')
                contas_pagar = ped_forn.groupby(['razao_social', 'status'])['valor_total'].sum().reset_index()
                
                fig_contas = px.bar(contas_pagar.sort_values('valor_total', ascending=True), 
                                    y='razao_social', x='valor_total', color='status', orientation='h',
                                    title="Pedidos de Compra por Fornecedor",
                                    labels={'razao_social': 'Fornecedor', 'valor_total': 'Valor Total dos Pedidos (R$)'},
                                    color_discrete_map={'Recebido': '#3498db', 'Em Trânsito': '#e67e22', 'Parcialmente Recebido': '#f1c40f'}, 
                                    template='streamlit')
                st.plotly_chart(fig_contas, use_container_width=True)
                
        with col_g2:
            st.markdown("**Atrasos de Entrega vs. Confiabilidade do Fornecedor**")
            if not df_ped.empty:
                atrasos = ped_forn[(ped_forn['dias_atraso'] > 0) & (ped_forn['status'] != 'Em Trânsito')]
                if not atrasos.empty:
                    fig_gargalo = px.scatter(atrasos, x='dias_atraso', y='valor_total', size='quantidade', color='score_fornecedor',
                                             hover_name='razao_social',
                                             title="Impacto dos Atrasos por Fornecedor",
                                             labels={'dias_atraso': 'Dias de Atraso', 'valor_total': 'Valor do Pedido (R$)', 'score_fornecedor': 'Score de Confiabilidade'},
                                             color_discrete_map={'Baixo': '#e74c3c', 'Médio': '#f1c40f', 'Alto': '#2ecc71'},
                                             template='streamlit', size_max=40)
                    st.plotly_chart(fig_gargalo, use_container_width=True)
                else:
                    st.success("🎉 Nenhum atraso de fornecedor registrado no período!")

        st.markdown("---")
        st.markdown("### Diagnóstico de Rupturas e Backorders")
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown("**Causas da Ruptura de Estoque**")
            if not df_rup.empty:
                rupturas_agg = df_rup.groupby(['deposito', 'criticidade'])['demanda_nao_atendida'].sum().reset_index()
                fig_tree_rup = px.treemap(rupturas_agg, path=['deposito', 'criticidade'], values='demanda_nao_atendida',
                                      color='demanda_nao_atendida', color_continuous_scale='Reds', 
                                      title="Onde a Demanda Não Foi Atendida?",
                                      template='streamlit')
                st.plotly_chart(fig_tree_rup, use_container_width=True)
        
        with col_r2:
            st.markdown("**Pedidos Pendentes (Backorders)**")
            if not df_back.empty:
                back_forn = df_back.merge(ped_forn[['pedido_id', 'razao_social']], on='pedido_id', how='left')
                back_agg = back_forn.groupby('razao_social')['qtd_pendente'].sum().reset_index().sort_values('qtd_pendente')
                fig_back = px.bar(back_agg, x='qtd_pendente', y='razao_social', orientation='h',
                                  title="Quantidade Pendente por Fornecedor",
                                  labels={'qtd_pendente': 'Unidades Pendentes', 'razao_social': 'Fornecedor'},
                                  template='streamlit')
                st.plotly_chart(fig_back, use_container_width=True)
            else:
                st.info("Nenhum backorder registrado.")

    # ------------------------------------------
    # ABA 4: QUALIDADE DE DADOS
    # ------------------------------------------
    with tab4:
        st.subheader("🛡️ Observabilidade e Qualidade dos Dados")
        st.markdown("""
        Este painel é o *Data Contract* da sua pipeline. Ele monitora a qualidade dos dados de movimentações de estoque
        antes de serem consumidos pelo BI. Regras são aplicadas para garantir completude, unicidade e conformidade dos dados.
        """)
        
        if df_mov_sujo is not None and not df_mov_sujo.empty:
            total_linhas = len(df_mov_sujo)
            
            # Execução dos Testes de Qualidade
            falhas_sku = df_mov_sujo['sku'].isna().sum()
            taxa_sku = (total_linhas - falhas_sku) / total_linhas if total_linhas > 0 else 0
            
            qtd_limpa = df_mov_sujo['quantidade'].fillna(0)
            falhas_qtd = (~qtd_limpa.between(1, 100000)).sum()
            taxa_qtd = (total_linhas - falhas_qtd) / total_linhas if total_linhas > 0 else 0
            
            falhas_dup = df_mov_sujo.duplicated(subset=['id_transacao']).sum()
            taxa_dup = (total_linhas - falhas_dup) / total_linhas if total_linhas > 0 else 0

            st.markdown("### 📋 Report Card da Ingestão: `fato_movimentacoes`")
            
            def exibir_expectation(col, titulo, taxa, falhas, help_text):
                with col:
                    status = "✅ Pass" if falhas == 0 else "❌ Fail"
                    delta = "Nenhum erro" if falhas == 0 else f"-{falhas} registros"
                    st.metric(f"{titulo} ({status})", f"{taxa*100:.1f}% de Conformidade", delta=delta, delta_color="inverse", help=help_text)
                    st.progress(float(taxa))

            c1, c2, c3 = st.columns(3)
            exibir_expectation(c1, "Completude (SKU)", taxa_sku, falhas_sku, "Verifica se a coluna 'sku' está preenchida (NOT NULL).")
            exibir_expectation(c2, "Unicidade (ID)", taxa_dup, falhas_dup, "Verifica se o 'id_transacao' é único para cada registro.")
            exibir_expectation(c3, "Limites (Quantidade)", taxa_qtd, falhas_qtd, "Verifica se a 'quantidade' está dentro de um limite razoável (1 a 100.000).")
            
            st.markdown("---")
            
            st.markdown("### 🧹 Quarentena e Limpeza de Dados (Sanitize)")
            st.write("Abaixo está uma amostra dos dados brutos, com os problemas de qualidade introduzidos. Você pode executar um pipeline de limpeza para corrigir esses problemas e ver o resultado.")
            
            if 'df_limpo' not in st.session_state:
                st.session_state.df_limpo = None

            if st.button("Executar Pipeline de Correção", type="primary"):
                with st.spinner("Aplicando regras de limpeza..."):
                    df_limpo = df_mov_sujo.drop_duplicates(subset=['id_transacao'])
                    df_limpo = df_limpo.dropna(subset=['sku'])
                    df_limpo = df_limpo[df_limpo['quantidade'].between(1, 100000)]
                    st.session_state.df_limpo = df_limpo
                st.success(f"Pipeline finalizado! {total_linhas - len(df_limpo)} linhas com problemas foram tratadas/removidas.")
            
            if st.session_state.df_limpo is not None:
                st.markdown("**Resultado: Dados Limpos e Prontos para o BI**")
                col_limp1, col_limp2 = st.columns([1, 3])
                with col_limp1:
                    st.metric("Total de Linhas Aprovadas", f"{len(st.session_state.df_limpo):,}")
                    st.metric("Conformidade Final", "100%", delta="Pronto para BI")
                with col_limp2:
                    st.dataframe(st.session_state.df_limpo.head(10), use_container_width=True)
            else:
                st.markdown("**Amostra dos Dados Brutos (Com Problemas)**")
                st.dataframe(df_mov_sujo.head(10), use_container_width=True)
        else:
            st.info("Arquivo de movimentações corrompidas (`fato_movimentacoes_sujo.csv`) não encontrado. Execute a simulação para gerá-lo.")

    # ------------------------------------------
    # ABA 5: EXPLORADOR DE DADOS
    # ------------------------------------------
    with tab5:
        st.subheader("🔎 Explorador de Datasets Gerados")
        st.markdown("Selecione um dos datasets gerados pela simulação para visualizar seus dados brutos.")

        datasets = {
            "Vendas (Enriquecido)": df_vendas_filtrado,
            "Movimentações de Estoque": df_mov,
            "Pedidos de Compra": df_ped,
            "Rupturas de Estoque": df_rup,
            "Backorders": df_back,
            "Snapshot Diário do Estoque": df_snap,
            "Dimensão: Produtos (Histórico)": df_prod,
            "Dimensão: Fornecedores (Histórico)": df_forn,
            "Dimensão: Depósitos": df_dep,
            "Qualidade: Movimentações (Sujo)": df_mov_sujo
        }

        dataset_selecionado = st.selectbox("Escolha o dataset para visualizar:", options=list(datasets.keys()))

        if dataset_selecionado and not datasets[dataset_selecionado].empty:
            df_display = datasets[dataset_selecionado]
            st.dataframe(df_display, use_container_width=True)
            
            st.info(f"Exibindo {len(df_display)} linhas e {len(df_display.columns)} colunas.")
            
            # Download do dataset selecionado
            @st.cache_data
            def convert_df_to_csv(df):
                return df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label=f"Baixar {dataset_selecionado} (CSV)",
                data=convert_df_to_csv(df_display),
                file_name=f"{dataset_selecionado.lower().replace(' ', '_')}.csv",
                mime='text/csv',
            )
        else:
            st.warning(f"O dataset '{dataset_selecionado}' está vazio ou não foi encontrado.")


