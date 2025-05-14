import pandas as pd
import streamlit as st
import re
import unicodedata
from io import BytesIO

# Configurações da página
st.set_page_config(page_title="Analisador CNP", layout="wide", page_icon="📊")
st.title("🔍 Analisador de Bases CNP - Controle Da Base")

# ================================================
# FUNÇÕES AUXILIARES
# ================================================

def sanitizar_nome_arquivo(nome):
    """Remove caracteres inválidos para nomes de arquivo"""
    return re.sub(r'[\\/*?:"<>|]', "", nome).strip()

def processar_base(df):
    """Padroniza e limpa a base de dados"""
    try:
        # Normalizar nomes das colunas
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.normalize('NFKD')
            .str.encode('ascii', errors='ignore')
            .str.decode('utf-8')
            .str.replace(' ', '_')
        )

        # Converter campos críticos
        for col in ['numero_da_solicitacao', 'mes', 'tarefa_da_solicitacao']:
            if col in df.columns:
                df[col] = (
                    df[col].astype(str)
                    .str.normalize('NFKD')
                    .str.encode('ascii', errors='ignore')
                    .str.decode('utf-8')
                    .str.strip()
                    .str.lower()
                )
        
        # Sanitizar dados
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].apply(
                lambda x: re.sub(r'[^\x20-\x7E\t\n\r]', '', str(x))
            )
        
        return df
    except Exception as e:
        st.error(f"Erro no processamento: {str(e)}")
        return None

def analisar_duplicatas(df):
    """Identifica diferentes tipos de duplicatas"""
    return {
        'por_solicitacao': df[df.duplicated('numero_da_solicitacao', keep=False)],
        'por_tarefa': df[df.duplicated('tarefa_da_solicitacao', keep=False)],
        'por_combinacao': df[df.duplicated(['numero_da_solicitacao', 'tarefa_da_solicitacao'], keep=False)]
    }

def comparar_meses(base_antiga, base_nova):
    """Compara as bases mês a mês"""
    try:
        meses_comuns = sorted(list(set(base_antiga['mes']).intersection(set(base_nova['mes']))))
        resultados = []
        
        for mes in meses_comuns:
            antigo = base_antiga[base_antiga['mes'] == mes]
            novo = base_nova[base_nova['mes'] == mes]
            
            faltantes_antigo = antigo[~antigo['numero_da_solicitacao'].isin(novo['numero_da_solicitacao'])]
            faltantes_novo = novo[~novo['numero_da_solicitacao'].isin(antigo['numero_da_solicitacao'])]
            
            resultados.append({
                'mes': mes,
                'faltantes_antigo': faltantes_antigo,
                'faltantes_novo': faltantes_novo,
                'total_antigo': len(antigo),
                'total_novo': len(novo)
            })
        
        return resultados
    except Exception as e:
        st.error(f"Erro na comparação mensal: {str(e)}")
        return []

def analisar_qualidade(df):
    """Realiza análise completa da qualidade dos dados"""
    analise = {
        'nulos': df.isnull().mean().round(4) * 100,
        'unicos': df.nunique(),
        'tipos': df.dtypes,
        'anomalias': {}
    }
    
    # Verificar datas
    if 'data' in df.columns:
        try:
            datas = pd.to_datetime(df['data'], errors='coerce')
            analise['anomalias']['datas_invalidas'] = datas.isnull().sum()
        except:
            pass
    
    # Verificar valores negativos
    for col in df.select_dtypes(include='number').columns:
        analise['anomalias'][f'{col}_negativos'] = df[df[col] < 0][col].count()
    
    return analise

def to_excel(df):
    """Converter DataFrame para Excel"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

# ================================================
# INTERFACE PRINCIPAL
# ================================================

with st.expander("📤 CARREGAR BASES", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        base_antiga_file = st.file_uploader("Base Histórica", type='csv')
    with col2:
        base_nova_file = st.file_uploader("Base Atual", type='csv')

if base_antiga_file and base_nova_file:
    with st.spinner('Processando bases...'):
        try:
            # Carregar e processar bases
            base_antiga = processar_base(pd.read_csv(base_antiga_file, delimiter=';'))
            base_nova = processar_base(pd.read_csv(base_nova_file, delimiter=';'))
            
            # Realizar análises
            dup_antiga = analisar_duplicatas(base_antiga)
            dup_nova = analisar_duplicatas(base_nova)
            comparacao_meses = comparar_meses(base_antiga, base_nova)
            qualidade_antiga = analisar_qualidade(base_antiga)
            qualidade_nova = analisar_qualidade(base_nova)
            meses_adicionais = list(set(base_nova['mes']) - set(base_antiga['mes']))
            
        except Exception as e:
            st.error(f"Erro crítico: {str(e)}")
            st.stop()

    # ================================================
    # SEÇÃO DE QUALIDADE DOS DADOS
    # ================================================
    st.subheader("🔍 ANÁLISE DE QUALIDADE")
    tab1, tab2 = st.tabs(["Base Histórica", "Base Atual"])
    
    with tab1:
        st.markdown("### 📉 Campos Nulos (%)")
        st.dataframe(qualidade_antiga['nulos'].to_frame('Porcentagem').style.format("{:.2f}%"))
        
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Tipos de Dados**")
            st.dataframe(qualidade_antiga['tipos'].to_frame('Tipo'))
        with col2:
            st.write("**Problemas**")
            for k, v in qualidade_antiga['anomalias'].items():
                st.write(f"- {k.replace('_', ' ').title()}: {v}")
    
    with tab2:
        st.markdown("### 📉 Campos Nulos (%)")
        st.dataframe(qualidade_nova['nulos'].to_frame('Porcentagem').style.format("{:.2f}%"))
        
        
        
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Tipos de Dados**")
            st.dataframe(qualidade_nova['tipos'].to_frame('Tipo'))
        with col2:
            st.write("**Problemas**")
            for k, v in qualidade_nova['anomalias'].items():
                st.write(f"- {k.replace('_', ' ').title()}: {v}")

    # ================================================
    # SEÇÃO DE DUPLICATAS
    # ================================================
    st.subheader("🚨 Análise de Duplicatas")
    col_dup1, col_dup2 = st.columns(2)
    
    with col_dup1:
        st.markdown("### Base Histórica")
        with st.expander("Por Número de Solicitação"):
            if not dup_antiga['por_solicitacao'].empty:
                st.dataframe(dup_antiga['por_solicitacao'][['numero_da_solicitacao', 'mes']].head())
                st.download_button("📥 Baixar", data=to_excel(dup_antiga['por_solicitacao']), 
                                 file_name="duplicatas_solicitacao_antiga.xlsx")
        
        with st.expander("Por Tarefa"):
            if not dup_antiga['por_tarefa'].empty:
                st.dataframe(dup_antiga['por_tarefa'][['tarefa_da_solicitacao', 'mes']].head())
                st.download_button("📥 Baixar", data=to_excel(dup_antiga['por_tarefa']),
                                 file_name="duplicatas_tarefa_antiga.xlsx")
        
        with st.expander("Por Combinação"):
            if not dup_antiga['por_combinacao'].empty:
                st.dataframe(dup_antiga['por_combinacao'][['numero_da_solicitacao', 'tarefa_da_solicitacao']].head())
                st.download_button("📥 Baixar", data=to_excel(dup_antiga['por_combinacao']),
                                 file_name="duplicatas_combinacao_antiga.xlsx")
    
    with col_dup2:
        st.markdown("### Base Atual")
        with st.expander("Por Número de Solicitação"):
            if not dup_nova['por_solicitacao'].empty:
                st.dataframe(dup_nova['por_solicitacao'][['numero_da_solicitacao', 'mes']].head())
                st.download_button("📥 Baixar", data=to_excel(dup_nova['por_solicitacao']),
                                 file_name="duplicatas_solicitacao_atual.xlsx")
        
        with st.expander("Por Tarefa"):
            if not dup_nova['por_tarefa'].empty:
                st.dataframe(dup_nova['por_tarefa'][['tarefa_da_solicitacao', 'mes']].head())
                st.download_button("📥 Baixar", data=to_excel(dup_nova['por_tarefa']),
                                 file_name="duplicatas_tarefa_atual.xlsx")
        
        with st.expander("Por Combinação"):
            if not dup_nova['por_combinacao'].empty:
                st.dataframe(dup_nova['por_combinacao'][['numero_da_solicitacao', 'tarefa_da_solicitacao']].head())
                st.download_button("📥 Baixar", data=to_excel(dup_nova['por_combinacao']),
                                 file_name="duplicatas_combinacao_atual.xlsx")

    # ================================================
    # COMPARAÇÃO MENSAL
    # ================================================
    st.subheader("📅 COMPARAÇÃO MÊS A MÊS")
    if comparacao_meses:
        tabs = st.tabs([f"📆 {mes['mes'].upper()}" for mes in comparacao_meses])
        
        for idx, tab in enumerate(tabs):
            with tab:
                mes_data = comparacao_meses[idx]
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"### 🔴 Faltantes na Nova ({len(mes_data['faltantes_antigo'])})")
                    if not mes_data['faltantes_antigo'].empty:
                        st.dataframe(mes_data['faltantes_antigo'][['numero_da_solicitacao', 'tarefa_da_solicitacao']].head())
                        st.download_button("📥 Baixar Completo", 
                                         data=to_excel(mes_data['faltantes_antigo']),
                                         file_name=f"faltantes_nova_{mes_data['mes']}.xlsx")
                
                with col2:
                    st.markdown(f"### 🔵 Faltantes na Antiga ({len(mes_data['faltantes_novo'])})")
                    if not mes_data['faltantes_novo'].empty:
                        st.dataframe(mes_data['faltantes_novo'][['numero_da_solicitacao', 'tarefa_da_solicitacao']].head())
                        st.download_button("📥 Baixar Completo", 
                                         data=to_excel(mes_data['faltantes_novo']),
                                         file_name=f"faltantes_antiga_{mes_data['mes']}.xlsx")
    else:
        st.warning("Nenhum mês em comum para comparação")

    # ================================================
    # MESES ADICIONAIS
    # ================================================
    if meses_adicionais:
        st.subheader("🆕 NOVOS MESES DETECTADOS")
        for mes in meses_adicionais:
            mes_clean = sanitizar_nome_arquivo(mes).upper()
            dados_mes = base_nova[base_nova['mes'] == mes]
            
            st.markdown(f"### 📌 {mes_clean}")
            st.write(f"Total de solicitações: {len(dados_mes)}")
            
            with st.expander("Ver detalhes"):
                st.dataframe(dados_mes.head())
                st.download_button(f"📥 Baixar {mes_clean}", 
                                 data=to_excel(dados_mes),
                                 file_name=f"novo_mes_{mes_clean[:20]}.xlsx")

st.markdown("---")
st.caption("© CNP Seguradora - Sistema de Análise de Bases | v5.0")