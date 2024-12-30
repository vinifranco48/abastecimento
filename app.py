import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import sqlite3
import os

# Configuração da página
st.set_page_config(page_title="Sistema de Gestão de Abastecimento", layout="wide")

# Configuração do banco de dados
def init_db():
    conn = sqlite3.connect('abastecimento.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo TEXT,
            placa TEXT,
            responsavel TEXT,
            status TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS abastecimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data DATE,
            veiculo TEXT,
            placa TEXT,
            responsavel TEXT,
            valor REAL,
            litros REAL,
            tipo_combustivel TEXT,
            observacao TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_veiculo(veiculo, placa, responsavel):
    conn = sqlite3.connect('abastecimento.db')
    c = conn.cursor()
    c.execute('INSERT INTO veiculos (veiculo, placa, responsavel, status) VALUES (?, ?, ?, ?)',
              (veiculo, placa, responsavel, 'Ativo'))
    conn.commit()
    conn.close()

def get_veiculos():
    conn = sqlite3.connect('abastecimento.db')
    df = pd.read_sql_query('SELECT * FROM veiculos WHERE status = "Ativo"', conn)
    conn.close()
    return df

def add_abastecimento(data, veiculo, placa, responsavel, valor, litros, tipo_combustivel, observacao):
    conn = sqlite3.connect('abastecimento.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO abastecimentos 
        (data, veiculo, placa, responsavel, valor, litros, tipo_combustivel, observacao)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data, veiculo, placa, responsavel, valor, litros, tipo_combustivel, observacao))
    conn.commit()
    conn.close()

def get_abastecimentos():
    conn = sqlite3.connect('abastecimento.db')
    df = pd.read_sql_query('SELECT * FROM abastecimentos', conn)
    conn.close()
    return df

def cadastrar_veiculo():
    st.header("Cadastro de Veículo")
    
    with st.form(key="cadastro_veiculo"):
        veiculo = st.text_input("Veículo")
        placa = st.text_input("Placa")
        responsavel = st.selectbox(
            "Responsável",
            ["Loja", "Oficina", "Test Drive", "Test Ride", "Outros"]
        )
        
        submit_button = st.form_submit_button(label="Cadastrar")
        
        if submit_button:
            if veiculo and responsavel:
                add_veiculo(veiculo, placa, responsavel)
                st.success("Veículo cadastrado com sucesso!")
            else:
                st.error("Por favor, preencha os campos obrigatórios.")

def registrar_abastecimento():
    st.header("Registro de Abastecimento")
    
    # Carregar veículos cadastrados
    veiculos_df = get_veiculos()
    
    if veiculos_df.empty:
        st.warning("Nenhum veículo cadastrado. Por favor, cadastre um veículo primeiro.")
        return
    
    with st.form(key="registro_abastecimento"):
        data = st.date_input("Data")
        veiculo = st.selectbox("Veículo", veiculos_df['veiculo'].tolist())
        
        # Auto-preenchimento da placa e responsável
        veiculo_info = veiculos_df[veiculos_df['veiculo'] == veiculo].iloc[0]
        placa = veiculo_info['placa']
        responsavel = veiculo_info['responsavel']
        
        st.text(f"Placa: {placa}")
        st.text(f"Responsável: {responsavel}")
        
        col1, col2 = st.columns(2)
        with col1:
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        with col2:
            litros = st.number_input("Litros", min_value=0.0, step=0.1)
        
        tipo_combustivel = st.selectbox(
            "Tipo de Combustível",
            ["Gasolina", "Etanol", "Diesel", "Diesel S10"]
        )
        
        observacao = st.text_area("Observação")
        
        submit_button = st.form_submit_button(label="Registrar")
        
        if submit_button:
            if valor > 0 and litros > 0:
                add_abastecimento(data, veiculo, placa, responsavel, valor, litros, 
                                tipo_combustivel, observacao)
                st.success("Abastecimento registrado com sucesso!")
            else:
                st.error("Por favor, preencha todos os campos obrigatórios.")

def show_dashboard():
    st.header("Dashboard de Análise")
    
    # Carregar dados
    df = get_abastecimentos()
    if df.empty:
        st.warning("Nenhum dado de abastecimento registrado ainda.")
        return
    
    # Converter coluna de data
    df['data'] = pd.to_datetime(df['data'])
    df['mes'] = df['data'].dt.strftime('%Y-%m')
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        meses = sorted(df['mes'].unique())
        mes_selecionado = st.selectbox('Selecione o Mês:', ['Todos'] + list(meses))
    
    with col2:
        responsaveis = sorted(df['responsavel'].unique())
        responsavel_selecionado = st.selectbox('Selecione o Responsável:', ['Todos'] + list(responsaveis))
    
    with col3:
        veiculos = sorted(df['veiculo'].unique())
        veiculo_selecionado = st.selectbox('Selecione o Veículo:', ['Todos'] + list(veiculos))
    
    # Aplicar filtros
    df_filtered = df.copy()
    if mes_selecionado != 'Todos':
        df_filtered = df_filtered[df_filtered['mes'] == mes_selecionado]
    if responsavel_selecionado != 'Todos':
        df_filtered = df_filtered[df_filtered['responsavel'] == responsavel_selecionado]
    if veiculo_selecionado != 'Todos':
        df_filtered = df_filtered[df_filtered['veiculo'] == veiculo_selecionado]
    
    # Métricas
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Gasto", f"R$ {df_filtered['valor'].sum():,.2f}")
    with col2:
        st.metric("Total de Litros", f"{df_filtered['litros'].sum():,.1f} L")
    with col3:
        preco_medio = df_filtered['valor'].sum() / df_filtered['litros'].sum() if df_filtered['litros'].sum() > 0 else 0
        st.metric("Preço Médio por Litro", f"R$ {preco_medio:.2f}")
    with col4:
        st.metric("Quantidade de Abastecimentos", len(df_filtered))
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de gastos por mês
        gastos_mes = df_filtered.groupby('mes')['valor'].sum().reset_index()
        fig = px.line(gastos_mes, x='mes', y='valor',
                     title='Evolução dos Gastos por Mês',
                     labels={'mes': 'Mês', 'valor': 'Valor (R$)'})
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de distribuição por tipo de combustível
        gastos_combustivel = df_filtered.groupby('tipo_combustivel')['valor'].sum().reset_index()
        fig = px.pie(gastos_combustivel, values='valor', names='tipo_combustivel',
                    title='Distribuição por Tipo de Combustível')
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de gastos por veículo
    st.subheader("Gastos por Veículo")
    if not df_filtered.empty:
        gastos_veiculo = df_filtered.groupby('veiculo').agg({
            'valor': 'sum',
            'litros': 'sum'
        }).reset_index()
        gastos_veiculo['preco_medio'] = gastos_veiculo['valor'] / gastos_veiculo['litros']
        gastos_veiculo.columns = ['Veículo', 'Valor Total', 'Litros Total', 'Preço Médio/L']
        st.dataframe(gastos_veiculo.round(2))

def consultar_dados():
    st.header("Consulta de Dados")
    
    # Carregar dados
    df = get_abastecimentos()
    if df.empty:
        st.warning("Nenhum dado de abastecimento registrado ainda.")
        return
    
    # Converter coluna de data
    df['data'] = pd.to_datetime(df['data'])
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input("Data Inicial")
    with col2:
        data_fim = st.date_input("Data Final")
    
    # Aplicar filtros de data
    mask = (df['data'].dt.date >= data_inicio) & (df['data'].dt.date <= data_fim)
    df_filtered = df.loc[mask]
    
    # Mostrar dados filtrados
    st.dataframe(df_filtered)
    
    # Botão de download
    if not df_filtered.empty:
        csv = df_filtered.to_csv(index=False)
        st.download_button(
            label="Download dos dados em CSV",
            data=csv,
            file_name=f"abastecimentos_{data_inicio}_{data_fim}.csv",
            mime="text/csv"
        )

def main():
    init_db()
    
    st.title("Abastecimento")
    
    # Menu principal
    menu = st.sidebar.selectbox(
        "Menu",
        ["Dashboard", "Cadastrar Veículo", "Registrar Abastecimento", "Consultar Dados"]
    )
    
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Cadastrar Veículo":
        cadastrar_veiculo()
    elif menu == "Registrar Abastecimento":
        registrar_abastecimento()
    elif menu == "Consultar Dados":
        consultar_dados()

if __name__ == "__main__":
    main()