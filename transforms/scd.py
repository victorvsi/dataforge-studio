import pandas as pd


def aplicar_scd_tipo2(df_atual: pd.DataFrame, df_novo: pd.DataFrame, chave_negocio: list, colunas_scd: list) -> pd.DataFrame:
    """
    Aplica a lógica de Slowly Changing Dimension (SCD) Tipo 2.
    Compara um dataframe de estado 'atual' com um 'novo' e gera um novo dataframe histórico.

    Args:
        df_atual (pd.DataFrame): O DataFrame com o estado histórico completo.
        df_novo (pd.DataFrame): O DataFrame com os dados mais recentes (pode conter novos, atualizados e inalterados).
        chave_negocio (list): Lista de colunas que formam a chave de negócio (ex: ['sku']).
        colunas_scd (list): Lista de colunas cujas alterações devem gerar uma nova versão.

    Returns:
        pd.DataFrame: O novo DataFrame histórico completo e atualizado.
    """
    # Junta os dataframes para comparação, usando apenas os registros ativos do histórico
    df_merged = pd.merge(
        df_atual[df_atual['registro_ativo']],
        df_novo,
        on=chave_negocio,
        how='outer',
        suffixes=('_atual', '_novo'),
        indicator=True
    )

    # --- 1. Registros que não mudaram ---
    # A chave de negócio existe em ambos os DFs e não houve alteração nas colunas SCD
    unchanged_keys = []
    updated_mask = (df_merged['_merge'] == 'both')
    if updated_mask.any():
        # Cria uma máscara para qualquer mudança nas colunas SCD
        any_change_mask = pd.Series([False] * len(df_merged))
        for col in colunas_scd:
            # Compara as colunas, tratando NaNs como iguais
            any_change_mask |= (df_merged[f'{col}_atual'].ne(df_merged[f'{col}_novo'])) & \
                              ~(df_merged[f'{col}_atual'].isnull() & df_merged[f'{col}_novo'].isnull())

        unchanged_keys = df_merged[updated_mask & ~any_change_mask][chave_negocio[0]].tolist()

    # --- 2. Novos registros (existem apenas no df_novo) ---
    novos_registros = df_merged[df_merged['_merge'] == 'right_only'].copy()

    # Corrige a seleção de colunas para novos registros, tratando a chave de negócio (sem sufixo).
    cols_to_rename = {f'{c}_novo': c for c in df_novo.columns if c not in chave_negocio}
    cols_to_select = chave_negocio + list(cols_to_rename.keys())
    novos_registros = novos_registros[cols_to_select].rename(columns=cols_to_rename)
    # --- 3. Registros que foram atualizados (mudança em alguma coluna SCD) ---
    chaves_atualizadas = df_merged[updated_mask & any_change_mask][chave_negocio[0]].tolist()

    # --- 4. Registros que foram "deletados" (existem apenas no df_atual) ---
    chaves_deletadas = df_merged[df_merged['_merge'] == 'left_only'][chave_negocio[0]].tolist()

    # --- Processamento ---
    # Pega todos os registros inativos e os inalterados do df_atual para manter o histórico
    registros_para_manter = df_atual[
        (df_atual[chave_negocio[0]].isin(unchanged_keys)) |
        (df_atual['registro_ativo'] == False)
    ].copy()

    # Pega os registros que precisam ser expirados (atualizados ou deletados)
    chaves_para_expirar = chaves_atualizadas + chaves_deletadas
    if chaves_para_expirar:
        expirados_df = df_atual[df_atual[chave_negocio[0]].isin(chaves_para_expirar) & df_atual['registro_ativo']].copy()
        expirados_df['vigencia_fim'] = pd.Timestamp.now().normalize()
        expirados_df['registro_ativo'] = False
    else:
        expirados_df = pd.DataFrame(columns=df_atual.columns)

    # Pega as novas versões dos registros atualizados
    if chaves_atualizadas:
        nova_versao_df = df_novo[df_novo[chave_negocio[0]].isin(chaves_atualizadas)].copy()
        
        # Mapeia a versão anterior para incrementar
        versoes_anteriores = df_atual[df_atual[chave_negocio[0]].isin(chaves_atualizadas) & df_atual['registro_ativo']]
        mapa_versao = pd.Series(versoes_anteriores.versao.values, index=versoes_anteriores[chave_negocio[0]]).to_dict()
        
        nova_versao_df['versao'] = nova_versao_df[chave_negocio[0]].map(mapa_versao) + 1
    else:
        nova_versao_df = pd.DataFrame(columns=df_novo.columns)

    # --- Concatenação Final ---
    df_final = pd.concat([
        registros_para_manter,
        expirados_df,
        nova_versao_df,
        novos_registros
    ], ignore_index=True)

    return df_final.sort_values(by=chave_negocio + ['versao']).reset_index(drop=True)