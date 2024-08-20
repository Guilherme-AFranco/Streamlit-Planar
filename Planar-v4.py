import pandas as pd
import streamlit as st
import altair as alt
from PIL import Image
from sqlalchemy import create_engine
import os
import pymysql
import dotenv
import matplotlib.pyplot as plt
import numpy as np
import imageio
import io
import pymysql
from nptdms import TdmsFile
import pymysql

from Insert_function import *
from Calibration_analysis_function import *
from Calibration_generator_function import *
from Pos_calibration_analysis_function import *

# --- Criar o dataframe
dotenv.load_dotenv()

# Configurações de conexão com o banco de dados
host=os.environ['MYSQL_HOST']
user=os.environ['MYSQL_USER']
password=os.environ['MYSQL_PASSWORD']
database=os.environ['MYSQL_DATABASE']
port=int(os.environ['MYSQL_PORT'])

# String de conexão
connection_string = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'

# Criar engine de conexão
engine = create_engine(connection_string)

# Obter dados do banco de dados
sql = 'SHOW TABLES'
df = pd.read_sql(sql, con=engine)

# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title='DASHBOARD - Sensor Planar',
    page_icon='💲',
    layout='wide',
    initial_sidebar_state='expanded',
    menu_items={
        'Get Help': 'http://www.meusite.com.br',
        'Report a bug': "http://www.meuoutrosite.com.br",
        'About': "App desenvolvido para inspeção do sensor planar."
    }
)

# Função para extrair o valor desejado
def extrair_valor(valor):
    return valor.split('_')[0]

def extrair_valor_matriz(valor):
    return '_'.join(valor.split('_')[:2])

def extrair_valor_pos_sublinhado(valor):
    return valor.split('_', 1)[1]

with st.sidebar:
    logo_teste = Image.open('./Imagens/Lemi-Logo.png')
    st.image(logo_teste, width=300)
    st.subheader('MENU - DASHBOARD PLANAR')
# Criação de um seletor na barra lateral
    page = st.sidebar.radio(
        "", 
        ("Inclusão/Exclusão de arquivos", "Gerador de matriz de calibração" , "Análise dos graficos", "Visualização", "Pós Calibração")
        )

# Conteúdo da Página 1
if page == "Inclusão/Exclusão de arquivos":
    # Caixa de entrada para o caminho da pasta
    folder_path = st.text_input("Digite o caminho para inserir os arquivos (ex.: E:\Planar\Calib):")

    # Verifica se um caminho de pasta foi fornecido
    if folder_path:
        try:
            st.write("Realizando inclusão dos arquivos selecionados...")
            # Lista todos os arquivos na pasta
            files_insert = insert_calibration(folder_path)
            
            st.write("Arquivos carregados corretamente.")

        except:
            st.write("Ocorreu um erro na importação.")

    # Exclusão de arquivos
    df['Arquivos alocados'] = df['Tables_in_base_de_dados']

    delet_file_box = st.multiselect('Selecione os arquivos para exclusão', df['Arquivos alocados'])
    
    # Botão para realizar a ação
    if st.button('Excluir arquivos'):
        if delet_file_box:
            st.write("Arquivo(s) selecionado(s):")
            for arquivo in delet_file_box:
                st.write(arquivo)
            
            # Realizar exclusão dos arquivos selecionados
            st.write("Realizando exclusão do(s) arquivo(s) selecionado(s)...")
            for arquivo in delet_file_box:
                files_exclude = exclude_calibration(arquivo)
            st.write("Exclusão concluída")

        else:
            st.write("Nenhum arquivo selecionado.")

    st.write(df['Arquivos alocados'])


# Conteúdo da Página 2
elif page == "Gerador de matriz de calibração":

    file_box = st.multiselect('Selecione a espessura da calibração', df['Tables_in_base_de_dados'].apply(lambda x: extrair_valor(x)).unique().tolist())
    filtered = df[df['Tables_in_base_de_dados'].apply(lambda x: any(x.startswith(val) for val in file_box))]['Tables_in_base_de_dados'].tolist()
    VH_box = st.selectbox('Selecione o VH', df['Tables_in_base_de_dados'])
    
    # Inicializando session state
    if 'equacao_calib' not in st.session_state:
        st.session_state.equacao_calib = None
    if 'matriz_fig' not in st.session_state:
        st.session_state.matriz_fig = None

    #st.write(filtrado)
    # Botão para realizar a ação
    if st.button('Gerar Matriz'):
        if file_box and VH_box:
            st.write("Gerando matriz de calibração...")
            st.session_state.equacao_calib = calibration_generator(filtered, VH_box)
            st.write("Matriz gerada")
            st.session_state.matriz_fig = plot_matriz_calib(st.session_state.equacao_calib)

    # Verificando se a matriz foi gerada para exibir os elementos subsequentes
    if st.session_state.matriz_fig:
        # Criando colunas
        col1, col2 = st.columns(2)

        # Exibindo a imagem na primeira coluna
        with col1:
            st.image(st.session_state.matriz_fig, caption='Matriz de calibração', use_column_width=False, width=int(300))

        # Exibindo a imagem na primeira coluna
        with col2:
            with st.form(key='save_form'):
                nome_equacao_calib = st.text_input("Nome do arquivo de calibração (ex.: Matriz_calib)")
                submit_button = st.form_submit_button(label='Salvar equação no banco de dados')

                if submit_button:
                    if nome_equacao_calib:
                        st.write("Incluindo matriz no banco de dados...")
                        insert_matriz(st.session_state.equacao_calib, nome_equacao_calib)
                        st.write("Matriz incluida.")
                    else:
                        st.write("Gere a equação antes.")
        
# Conteúdo da Página 3
elif page == "Análise dos graficos":

    gif_file_box = st.selectbox('Selecione a espessura da calibração', df['Tables_in_base_de_dados'].apply(lambda x: extrair_valor(x)).unique().tolist())
    filtered_gif = df[df['Tables_in_base_de_dados'].str.startswith(gif_file_box)]['Tables_in_base_de_dados'].tolist() # Obtendo todos os arquivos da espessura selecionada
    #filtrado = [name[1:-1] for name in filtered_gif]
    VH_file_box = st.selectbox('Selecione o VH', df['Tables_in_base_de_dados'])
    
    #st.write(filtrado)
    # Botão para realizar a ação
    if st.button('Gerar gif'):
        if gif_file_box and VH_file_box:
            st.write("Gerando GIF...")
            imagens = calibration_analysis(filtered_gif,VH_file_box)
            # Realizar a tarefa de inclusão de gif
            st.write("Gif gerado")

            # Criar um GIF a partir das imagens
            gif_bytes = io.BytesIO()
            imageio.mimsave(gif_bytes, imagens, format='GIF', duration=5)
            gif_bytes.seek(0)
            # Exibir o GIF em Streamlit
            st.image(gif_bytes.read())

        else:
            st.write("Erro.")

# Conteúdo da Página 4
elif page == "Visualização":
    df['Espessuras'] = df['Tables_in_base_de_dados'].apply(lambda x: extrair_valor(x))
    df['Faixa'] = df['Tables_in_base_de_dados'].apply(lambda x: extrair_valor_pos_sublinhado(x))

    # -- Criar o sidebar
    with st.sidebar:
        fEspessura = st.selectbox(
            "Selecione a Espessura:",
            options=df['Espessuras'].unique()
        )
        fFaixa = st.selectbox(
            "Selecione a Faixa utilizada:",
            options=df['Faixa'].unique()
        )

    #Tabela Qtde vendida por produto
    tab1_value_calibration = df.loc[(
        df['Espessuras'] == fEspessura) &
        (df['Faixa'] == fFaixa)
    ]

    table_name = tab1_value_calibration['Tables_in_base_de_dados'].iloc[0]
    # Consulta SQL
    sql = f'SELECT * FROM {table_name}'

    # Ler dados do banco de dados e armazenar em um DataFrame
    df_calibration = pd.read_sql(sql, con=engine)

    # Exibir título da aplicação
    st.title('Tabela calibração')

    # Exibir o DataFrame
    st.write(f'Valores obtidos para a calibração {table_name}:')
    st.dataframe(df_calibration)

# Conteúdo da Página 5
elif page == "Pós Calibração":
    # Criando colunas
    col1, col2, col3 = st.columns(3)

    # Exibindo a imagem na primeira coluna
    with col1:
        pos_file_box = st.selectbox('Selecione a espessura da calibração', df['Tables_in_base_de_dados'].apply(lambda x: extrair_valor(x)).unique().tolist())
        VH_file_box = st.selectbox('Selecione o VH', df['Tables_in_base_de_dados'])

    # Exibindo a imagem na primeira coluna
    with col2:
        matriz_file_box = st.selectbox('Selecione a matriz de calibração', df['Tables_in_base_de_dados'].apply(lambda x: extrair_valor_matriz(x)).unique().tolist())
        VL_file_box = st.selectbox('Selecione o VL', df['Tables_in_base_de_dados'])

    filtered_pos = df[df['Tables_in_base_de_dados'].str.startswith(pos_file_box)]['Tables_in_base_de_dados'].tolist() # Obtendo todos os arquivos da espessura selecionada
    filtered_matriz = df[df['Tables_in_base_de_dados'].str.startswith(matriz_file_box)]['Tables_in_base_de_dados'].tolist() # Obtendo todos os arquivos da espessura selecionada

    
    # Inicializando session state
    if 'fr_all' not in st.session_state:
        st.session_state.fr_all = None
    if 'VL_compar' not in st.session_state:
        st.session_state.VL_compar = None

    # Botão para realizar a ação
    if st.button('Gerar análise'):
        if pos_file_box and VH_file_box:
            st.write("Gerando GIF...")
            st.session_state.fr_all,st.session_state.VL_compar = pos_calibration_analysis(filtered_pos,filtered_matriz,VH_file_box,VL_file_box)
            # Realizar a tarefa de inclusão de variaveis
            st.write("Gráfrico gerado")

    if st.session_state.fr_all:
        fr_min,fr_max = min_max(st.session_state.fr_all)

        # Criar os graficos
        for idx,value in enumerate(st.session_state.fr_all):
            plot_color_map(st.session_state.fr_all[value]['fr1'][0].apply(pd.to_numeric, errors='coerce'),value,fr_min,fr_max)

        else:
            st.write("Erro.")