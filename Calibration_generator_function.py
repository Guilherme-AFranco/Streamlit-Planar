from planar_functions import *
from tqdm import tqdm
from PIL import Image
import os
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
import imageio
import io
import pymysql
import dotenv
import pandas as pd
from nptdms import TdmsFile
from sqlalchemy import create_engine
import pymysql
from scipy import io
from io import BytesIO

def calibration_generator(names_path,name_VH):
    dotenv.load_dotenv()

    # Configurações de conexão com o banco de dados
    host=os.environ['MYSQL_HOST']
    user=os.environ['MYSQL_USER']
    password=os.environ['MYSQL_PASSWORD']
    database=os.environ['MYSQL_DATABASE']
    port=int(os.environ['MYSQL_PORT'])

    # String de conexão
    connection_string = f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}'

    # Criar engine de conexão
    engine = create_engine(connection_string)

    # Consulta SQL
    path_calibration = {}
    for name in names_path:
        df_name = f'{name}'
        query = f'SELECT * FROM {name}'
        # Ler dados do banco de dados e armazenar em um DataFrame
        path_calibration[df_name] = pd.read_sql(query, con=engine)

    VH = {}
    df_name = f'{name_VH}'
    query = f'SELECT * FROM {name_VH}'
    # Ler dados do banco de dados e armazenar em um DataFrame
    VH[df_name] = pd.read_sql(query, con=engine)

    for key in VH:
        if 'id' in VH[key].columns:
            VH[key] = VH[key].drop(columns=['id'])
        if 'Seconds' in VH[key].columns:
            VH[key] = VH[key].drop(columns=['Seconds'])

    for key in path_calibration:
        if 'id' in path_calibration[key].columns:
            path_calibration[key] = path_calibration[key].drop(columns=['id'])
        if 'Seconds' in path_calibration[key].columns:
            path_calibration[key] = path_calibration[key].drop(columns=['Seconds'])


    grouped_dataframes = {}

    # Agrupar os DataFrames por prefixo
    for key, df in path_calibration.items():
        prefix = key.split('_')[0]  # Obter o prefixo (e.g., "400u" ou "500u")
        if prefix not in grouped_dataframes:
            grouped_dataframes[prefix] = {}
        grouped_dataframes[prefix][key] = df

    #Carrega cada elemento da lista de paths e divide pelo VHmax
    calibrations_dict_imported = grouped_dataframes
    conv = 2/(2**16-1)
    VH_2200 = VH[name_VH].multiply(-1).multiply(conv)
    VHMax, not_concatened_VH = mean_3(VH_2200)# a informação na verdade é 32x16x25000 e querem a média na terceira dimenção

    for elements in tqdm(calibrations_dict_imported):
        for i in calibrations_dict_imported[elements]: # ou 16 já que é fixo
            calib_file = calibrations_dict_imported[elements][i].multiply(-1).multiply(conv)
            calibrations_dict_imported[elements][i], not_concat = mean_3(calib_file)
            calibrations_dict_imported[elements][i] = calibrations_dict_imported[elements][i].div(VHMax)

    #criando o x e y do polinomio

    colunas_ignoradas = 0
    poly_x = [[[] for i in range(16-colunas_ignoradas)] for j in range(13)]
    poly_y = [[[] for i in range(16-colunas_ignoradas)] for j in range(13)]

    for elements in calibrations_dict_imported:
        contador_matrizes = 0
        for matrizes in calibrations_dict_imported[elements]:
            matrix = calibrations_dict_imported[elements][matrizes][10:23].to_numpy()  
            contador_rows = 0 
            for rows in matrix:
                contador_columns = 0
                for index_col, columns in enumerate(rows): #columns or values
                    poly_x[contador_rows][contador_columns].append(columns)
                    if contador_columns == contador_matrizes:
                        poly_y[contador_rows][contador_columns].append(int(elements.replace('u', '')))
                    else:
                        poly_y[contador_rows][contador_columns].append(2201)
                    contador_columns += 1 # posso tirar isso aqui e substituir pelo index_col
                contador_rows += 1
            contador_matrizes += 1
            
    #Remove todos os elementos de 2200 ou mais, e pode dar append 
    for rows in range(len(poly_y)):
        for columns in range(len(poly_y[rows])):
            indices = [i for i, x in enumerate(poly_y[rows][columns]) if x == 2201]
            contador_pop = 0
            for elements in indices:
                poly_y[rows][columns].pop(elements-contador_pop)
                poly_x[rows][columns].pop(elements-contador_pop)
                contador_pop += 1

    #Cria a matrix de polinomio
    matriz_calibracao_nova = np.zeros((13,16,5))

    for i in range(len(matriz_calibracao_nova)):
        for j in range(len(matriz_calibracao_nova[i,:,:])):
            polinomio = np.polyfit(poly_x[i][j],poly_y[i][j],4)
            matriz_calibracao_nova[i,j,0] = polinomio[0] # talvez tenha que inverter a ordem para ficar similar ao .mat
            matriz_calibracao_nova[i,j,1] = polinomio[1]
            matriz_calibracao_nova[i,j,2] = polinomio[2]
            matriz_calibracao_nova[i,j,3] = polinomio[3]
            matriz_calibracao_nova[i,j,4] = polinomio[4]

    return matriz_calibracao_nova

def f_x(x,matriz):
    y = []

    for i in range(len(matriz[0,:,:])):
        a = np.mean(matriz[:,i,0])
        b = np.mean(matriz[:,i,1])
        c = np.mean(matriz[:,i,2])
        d = np.mean(matriz[:,i,3])
        e = np.mean(matriz[:,i,4])

        y.append(a*x**4 + b*x**3 + c*x**2 + d*x + e)
    
    return y

def f_x_calib(x,matriz):
    y = []
    coefs = []

    a = np.mean(matriz['a'])
    b = np.mean(matriz['b'])
    c = np.mean(matriz['c'])
    d = np.mean(matriz['d'])
    e = np.mean(matriz['e'])

    coefs = [a, b, c, d, e]
    y.append(a*x**4 + b*x**3 + c*x**2 + d*x + e)
    
    return y, coefs

def plot_matriz_calib_plotly(matriz):
    # Criar um array de valores x
    x = np.linspace(0, 2, 400)  # 400 pontos de -1 a 1

    # Criar uma figura Plotly
    fig = go.Figure()

    # Gerar as curvas e adicionar traços ao gráfico
    y = f_x(x, matriz)
    for m in range(len(matriz)):
        # fig.add_trace(go.Scatter(x=y[m], y=x, mode='lines', name=f'Curva {m+1}'))
        if m<9:
            fig.add_trace(go.Scatter(x=y[m], y=x, mode='lines', name=f'Rx0{m+1}'))
        else:
            fig.add_trace(go.Scatter(x=y[m], y=x, mode='lines', name=f'Rx{m+1}'))
    # Personalizar os eixos e o título
    fig.update_layout(
        title='Curvas de Grau 4 - Matriz de calibração',
        xaxis_title='Espessura (10^-6 m)',
        yaxis_title='Tensão (V)',
        showlegend=True,
        template='plotly_white'
    )

    return fig  # Certificar-se de retornar um objeto `go.Figure`

def capture_calib(names_calib):
    dotenv.load_dotenv()

    # Configurações de conexão com o banco de dados
    host=os.environ['MYSQL_HOST']
    user=os.environ['MYSQL_USER']
    password=os.environ['MYSQL_PASSWORD']
    database=os.environ['MYSQL_DATABASE']
    port=int(os.environ['MYSQL_PORT'])

    # String de conexão
    connection_string = f'mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}'

    # Criar engine de conexão
    engine = create_engine(connection_string)

    path_matriz = {}
    for name in names_calib:
        df_matriz = f'{name}'
        query = f'SELECT * FROM {name}'
        path_matriz[df_matriz] = pd.read_sql(query,con=engine)

    for key in path_matriz:
        if 'id' in path_matriz[key].columns:
            path_matriz[key] = path_matriz[key].drop(columns=['id'])
        if 'Seconds' in path_matriz[key].columns:
            path_matriz[key] = path_matriz[key].drop(columns=['Seconds'])
    
    grouped_matriz = {}
    # Agrupar os DataFrames por prefixo
    for key, df in path_matriz.items():
        prefix = "_".join(key.split('_')[:2])
        if prefix not in grouped_matriz:
            grouped_matriz[prefix] = {}
        grouped_matriz[prefix][key] = df
    return grouped_matriz

def plot_matriz_calib_calib(matriz, m, name):
    # Criar um array de valores x
    x = np.linspace(0, 2, 400)  # 400 pontos de -1 a 1
    
    # Definir o título e a curva para o Rx específico
    if m < 10:
        y, coefs = f_x_calib(x, matriz[name][f'{name}_0{m}'])
        title = f'Curva de calibração Rx0{m}'
    else:
        y, coefs = f_x_calib(x, matriz[name][f'{name}_{m}'])
        title = f'Curva de calibração Rx{m}'

    # Criar o gráfico com Plotly
    fig = go.Figure()

    # Adicionar a curva de calibração
    fig.add_trace(go.Scatter(x=y[0], y=x, mode='lines', name=f'Rx{m}'))

    # Definir os títulos e rótulos dos eixos
    fig.update_layout(
        title=title,
        xaxis_title='Espessura (10^-6 m)',
        yaxis_title='Tensão (V)',
        showlegend=False,
        template='plotly_dark'  # Opcional: escolhe um tema escuro
    )

    # Adicionar grade
    fig.update_xaxes(showgrid=True)
    fig.update_yaxes(showgrid=True)

    return fig, coefs

def plot_planar_view(i_row=None):
    # Gerar os dados para tx_values (Transmissões)
    tx_values = []
    for i in range(1, 14):
        tx_values.append(f'Tx{i:02}')  # Adiciona valor Tx01, Tx02, etc.

    # Gerar os dados para rx_values (Receptores)
    rx_values = []
    for i in range(1, 17):
        rx_values.append(f'Rx{i:02}')  # Adiciona valor Rx01, Rx02, etc.

    # Criar uma matriz de valores para o heatmap (usando valores binários de transmissão)
    heatmap_data = []
    row = [0] * 16  # Criando uma linha com treze 1's
    for _ in rx_values:
        heatmap_data.append(row)  # Adiciona a linha à matriz de dados

    if i_row != None:
        heatmap_data[i_row] = [1]*16

    # Criar o gráfico de calor com Plotly
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        x=rx_values,
        y=tx_values,
        zmin=0,
        zmax=1,
        showscale=False,
        # colorscale='Viridis'  # Escala de cores
    ))

    # Título e labels
    fig.update_layout(
        title={
            'text': 'Modelo estrutural do planar',
            'y': 0.9,  # Posição vertical do título (1.0 é o topo do gráfico)
            'x': 0.5,  # Centraliza horizontalmente
            'xanchor': 'center',  # Âncora do título no centro
            'yanchor': 'top'  # Âncora do título na parte superior
        },
        xaxis_title='Receptores (Rx)',
        yaxis_title='Transmissões (Tx)'
    )
    return fig, tx_values