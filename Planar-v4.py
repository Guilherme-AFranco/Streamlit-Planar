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
import time
import plotly.express as px

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
    cols = st.columns(3)
    with cols[0]:
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

    with cols[1]:
        # Exclusão de arquivos
        df['Arquivos alocados'] = df['Tables_in_base_de_dados']

        delet_file_box = st.multiselect('Selecione os arquivos para exclusão (essa exclusão é irreversível).', df['Arquivos alocados'])
        
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

    with cols[2]:
        st.write(df['Arquivos alocados'])
    
    st.write('Obs.: Os nomes dos arquivos a incluir devem ser no formato \'XXXu-YY\'')
    st.write('Onde XXX é a espessura do cilindro de calibração (400, 520, ...) e YY é a coleta realizada (00, 01, 02, 03, ...)')


# Conteúdo da Página 2
elif page == "Gerador de matriz de calibração":
    cols = st.columns(2)

    with cols[0]:
        # Filtrar os nomes que começam com números
        number_names = df[df['Tables_in_base_de_dados'].str.contains(r'^\d')]['Tables_in_base_de_dados']
        # Exibir a caixa de seleção com os valores filtrados
        file_box = st.multiselect('Selecione a espessura da calibração', number_names.apply(lambda x: extrair_valor(x)).unique().tolist())
    filtered = df[df['Tables_in_base_de_dados'].apply(lambda x: any(x.startswith(val) for val in file_box))]['Tables_in_base_de_dados'].tolist()

    with cols[1]:
        # Filtrar os nomes que começam com "VH"
        vh_names = df[df['Tables_in_base_de_dados'].str.startswith('VH')]['Tables_in_base_de_dados']

        # Exibir a caixa de seleção com os valores filtrados
        VH_box = st.selectbox('Selecione o VH', vh_names)
        # VH_box = st.selectbox('Selecione o VH', df['Tables_in_base_de_dados'])
    
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
            st.session_state.matriz_fig = plot_matriz_calib_plotly(st.session_state.equacao_calib)

    # Verificando se a matriz foi gerada para exibir os elementos subsequentes
    if st.session_state.matriz_fig:
        # Criando colunas
        col1, col2 = st.columns(2)

        # Exibindo a imagem na primeira coluna
        with col1:
            # st.image(st.session_state.matriz_fig, caption='Matriz de calibração', use_column_width=False, width=int(300))
            st.plotly_chart(st.session_state.matriz_fig, use_container_width=True)

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

    cols = st.columns(2)

    with cols[0]:
        # Filtrar os nomes que começam com "VH"
        matriz_names = df[df['Tables_in_base_de_dados'].str.startswith('Matriz')]['Tables_in_base_de_dados']

        matriz_file_box = st.selectbox('Selecione a matriz de calibração', matriz_names.apply(lambda x: extrair_valor_matriz(x)).unique().tolist())
    
    if 'calib_fig' not in st.session_state:
        st.session_state.calib_fig = None

    # Inicializar uma flag para determinar se a análise foi feita
    if 'analise_feita' not in st.session_state:
        st.session_state.analise_feita = False

    if st.button("Analise de matriz"):
        # Dados para os gráficos
        Rx_labels = [i for i in range(0, 13)]  # Nomes dos Rx (colunas)
        values_calib = [12] * 13  # Valores arbitrários

        st.session_state.Rx_labels = Rx_labels
        st.session_state.values_calib = values_calib

        filtered_matriz_calib = df[df['Tables_in_base_de_dados'].str.startswith(matriz_file_box)]['Tables_in_base_de_dados'].tolist() # Obtendo todos os arquivos da espessura selecionada

        matriz_cali = capture_calib(filtered_matriz_calib)

        # Guardar a matriz no estado da sessão para acesso posterior
        st.session_state.matriz_cali = matriz_cali
        
        # Definir que a análise foi feita
        st.session_state.analise_feita = True
        
    # Verificar se a análise já foi feita para exibir os botões Rx e o gráfico correspondente
    if (st.session_state.analise_feita == True):
        # Criação do gráfico de barras (primeiro exibir o gráfico)
        fig = px.bar(x=st.session_state.Rx_labels, y=st.session_state.values_calib, labels={'x': '', 'y': 'Tx'}, title="Características da malha")
        
        # Remover os números no eixo x
        fig.update_xaxes(showticklabels=False)

        # Exibição do gráfico interativo no Streamlit
        st.plotly_chart(fig)

        # Colunas para os botões Rx (depois exibir os botões abaixo do gráfico)
        cols = st.columns(14)

        # Simulação de clique nos botões
        for i in range(13):
            with cols[i+1]:
                if st.button(f"Rx{i}"):
                    st.session_state.calib_fig = plot_matriz_calib_calib(st.session_state.matriz_cali, i, matriz_file_box)

        cols = st.columns(2)
        with cols[1]:
            # Exibição da figura de calibração (se houver)
            if 'calib_fig' in st.session_state:
                st.plotly_chart(st.session_state.calib_fig)

# Conteúdo da Página 3
elif page == "Análise dos graficos":

    cols = st.columns(2)
    # Filtrar os nomes que começam com números
    number_names = df[df['Tables_in_base_de_dados'].str.contains(r'^\d')]['Tables_in_base_de_dados']

    with cols[0]:
        # Exibir a caixa de seleção com os valores filtrados
        gif_file_box = st.multiselect('Selecione a espessura da calibração', number_names.apply(lambda x: extrair_valor(x)).unique().tolist())
        filtered_gif = df[df['Tables_in_base_de_dados'].apply(lambda x: any(x.startswith(val) for val in gif_file_box))]['Tables_in_base_de_dados'].tolist()
    # filtered_gif = df[df['Tables_in_base_de_dados'].str.startswith(gif_file_box)]['Tables_in_base_de_dados'].tolist() # Obtendo todos os arquivos da espessura selecionada
    #filtrado = [name[1:-1] for name in filtered_gif]
    
    # Filtrar os nomes que começam com "VH"
    vh_names = df[df['Tables_in_base_de_dados'].str.startswith('VH')]['Tables_in_base_de_dados']
    with cols[1]:
        # Exibir a caixa de seleção com os valores filtrados
        VH_file_box = st.selectbox('Selecione o VH', vh_names)
    
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

    # Remover as colunas 'id' e 'segundos' do DataFrame
    df_calibration_filtered = df_calibration.drop(columns=['id', 'Seconds'])

    # Gerar heatmap utilizando Plotly
    fig = px.imshow(df_calibration_filtered.values, 
                    labels=dict(color="Valores"),
                    x=list(df_calibration_filtered.columns), 
                    y=df_calibration_filtered.index,
                    title=f'Média Temporal: {table_name}')

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig)

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
    
    # if st.button('Salvar gráfico no banco de dados.'):
    #     pos_calibration_save(fr_all)

    col1, col2 = st.columns(2)

    # with col1:
    #     if st.session_state.fr_all:
    #         fr_min,fr_max = min_max(st.session_state.fr_all)

    #         # Interface para selecionar qual gráfico visualizar
    #         selected_graph = st.selectbox("Escolha o gráfico", list(st.session_state.fr_all.keys()))
            
    #         # Exibe o gráfico correspondente
    #         plot_color_map(st.session_state.fr_all[selected_graph]['fr1'][0].apply(pd.to_numeric, errors='coerce'), selected_graph, fr_min, fr_max)

    if st.session_state.fr_all:
        fr_min, fr_max = min_max(st.session_state.fr_all)
    fr_max = 500

    col1, col2, col3, col4 = st.columns(4)

    if st.button("Gerar gráficos"):
        if st.session_state.fr_all:
            col_map = {0: col1, 1: col2, 2: col3, 3: col4}  # Mapeia os índices às colunas

            for idx, value in enumerate(st.session_state.fr_all):
                col = col_map[idx % 4]  # Seleciona a coluna com base no índice
                with col:
                    # Exibe o gráfico correspondente
                    plot_color_map(st.session_state.fr_all[value]['fr1'][0].apply(pd.to_numeric, errors='coerce'), value, fr_min, fr_max)
        else:
            st.write("Gere a análise primeiro")
        #     for idx, value in enumerate(st.session_state.fr_all):
        #         if idx%4==0:
        #             with col1:
        #                 # Exibe o gráfico correspondente
        #                 plot_color_map(st.session_state.fr_all[value]['fr1'][0].apply(pd.to_numeric, errors='coerce'),value, fr_min, fr_max)
        #         elif idx%4==1:
        #             with col2:
        #                 # Exibe o gráfico correspondente
        #                 plot_color_map(st.session_state.fr_all[value]['fr1'][0].apply(pd.to_numeric, errors='coerce'),value, fr_min, fr_max)
        #         elif idx%4==2:
        #             with col3:
        #                 # Exibe o gráfico correspondente
        #                 plot_color_map(st.session_state.fr_all[value]['fr1'][0].apply(pd.to_numeric, errors='coerce'),value, fr_min, fr_max)
        #         else:
        #             with col4:
        #                 # Exibe o gráfico correspondente
        #                 plot_color_map(st.session_state.fr_all[value]['fr1'][0].apply(pd.to_numeric, errors='coerce'),value, fr_min, fr_max)
        # else:
        #     st.write("Gere a análise primeiro")
