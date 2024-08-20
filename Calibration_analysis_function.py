from planar_functions import *
from tqdm import tqdm
from PIL import Image
import os
import matplotlib.pyplot as plt
import numpy as np
import imageio
import io
import pymysql
import dotenv
import pandas as pd
from nptdms import TdmsFile
from sqlalchemy import create_engine
import pymysql

def calibration_analysis(names_path,name_VH):
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

    VH_max = VH[name_VH].multiply(-1).multiply(2/(2**16-1))
    VHMAX, not_concatened_VH = mean_3(VH_max)# a informação na verdade é 32x16x25000 e querem a média na terceira dimenção

    for key in path_calibration:
        if 'id' in path_calibration[key].columns:
            path_calibration[key] = path_calibration[key].drop(columns=['id'])
        if 'Seconds' in path_calibration[key].columns:
            path_calibration[key] = path_calibration[key].drop(columns=['Seconds'])

    # Criação das figuras
    figs = [[] for _ in range(len(path_calibration))]  # Inicializa a lista de listas

    for index, elements in (enumerate(path_calibration)):
    #    for paths in path_calibration[elements]:
        fig = plot_color_map_trio(path_calibration[elements], elements, VHMAX)
        figs[index].append(fig)  # Adiciona a figura na ordem correta

    # Converter as figuras em imagens e armazenar em uma lista
    imagens = []
    for fig_list in figs:
        for fig in fig_list:
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            img = Image.open(buf)
            imagens.append(img)
            plt.close(fig)  # Fechar a figura para liberar memória

    return imagens