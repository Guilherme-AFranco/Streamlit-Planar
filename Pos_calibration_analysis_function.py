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

def pos_calibration_analysis(names_path,names_calib,name_VH,name_VL):
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

    path_matriz = {}
    for name in names_calib:
        df_matriz = f'{name}'
        query = f'SELECT * FROM {name}'
        path_matriz[df_matriz] = pd.read_sql(query,con=engine)

    VH = {}
    df_name = f'{name_VH}'
    query = f'SELECT * FROM {name_VH}'
    # Ler dados do banco de dados e armazenar em um DataFrame
    VH[df_name] = pd.read_sql(query, con=engine)

    VL = {}
    df_name = f'{name_VL}'
    query = f'SELECT * FROM {name_VL}'
    # Ler dados do banco de dados e armazenar em um DataFrame
    VL[df_name] = pd.read_sql(query, con=engine)

    for key in VL:
        if 'id' in VL[key].columns:
            VL[key] = VL[key].drop(columns=['id'])
        if 'Seconds' in VL[key].columns:
            VL[key] = VL[key].drop(columns=['Seconds'])

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

    for key in path_matriz:
        if 'id' in path_matriz[key].columns:
            path_matriz[key] = path_matriz[key].drop(columns=['id'])
        if 'Seconds' in path_matriz[key].columns:
            path_matriz[key] = path_matriz[key].drop(columns=['Seconds'])

    grouped_dataframes = {}
    grouped_matriz = {}

    # Agrupar os DataFrames por prefixo
    for key, df in path_calibration.items():
        prefix_calib = key.split('_')[0]  # Obter o prefixo (e.g., "400u" ou "500u")
        if prefix_calib not in grouped_dataframes:
            grouped_dataframes[prefix_calib] = {}
        grouped_dataframes[prefix_calib][key] = df

    # Agrupar os DataFrames por prefixo
    for key, df in path_matriz.items():
        prefix = "_".join(key.split('_')[:2])
        if prefix not in grouped_matriz:
            grouped_matriz[prefix] = {}
        grouped_matriz[prefix][key] = df

    fre=1000 # Frames by second #1000#

    #Carrega cada elemento da lista de paths e divide pelo VHmax
    conv = 2/(2**16-1)

    VH_2200 = VH[name_VH].multiply(-1).multiply(conv)
    VHMax, not_concatened_VH = mean_3(VH_2200)# a informação na verdade é 32x16x25000 e querem a média na terceira dimenção

    VL_2200 = VL[name_VL].multiply(-1).multiply(conv)
    VLMax, not_concatened_VL = mean_3(VL_2200)# a informação na verdade é 32x16x25000 e querem a média na terceira dimenção

    matriz_transf = {col: pd.DataFrame(index=range(len(grouped_matriz['Matriz_calib'])), columns=[f'Rx{str(i).zfill(2)}' for i in range(len(grouped_matriz['Matriz_calib']['Matriz_calib_01']))]) for col in ['a', 'b', 'c', 'd', 'e']}

    for i, val in enumerate(grouped_matriz['Matriz_calib']):  # Percorre as tabelas originais
        for col in ['a', 'b', 'c', 'd', 'e']:  # Percorre as colunas
            matriz_transf[col].loc[i] = grouped_matriz['Matriz_calib'][val][col].values

    #from collections import ChainMap
    x_axis_original = 32

    # USAREI E REMOVO for i, key in enu... absolute_folder = calibrations_dict_imported['400u']
    files_path = {}
    for idx,value in enumerate(grouped_dataframes[prefix_calib]):
        files_path[value] = grouped_dataframes[prefix_calib][value]

    # files_path = grouped_dataframes[names_path]
    #files_path = absoluteFilePaths(absolute_folder)
    Media_dict = {}
    fr_all = {}
    plt.close('all')
    for idx,files in enumerate(files_path): # Se for concatenado vai ficar bem mais rápido
    #name_matriz = files.split('_')[0]  # Obter o prefixo (e.g., "400u" ou "500u")
        dd = files_path[files].multiply(-1).multiply(conv)
        ddMax, not_concatened_dd = mean_3(dd)
        [x,y] = dd.shape
        z = int(x/x_axis_original)
        x = int(x_axis_original)
        cm = [None]*z#np.zeros(z)
        for m in range(z): # matlab começa do 1 e python do zero
            cm[m] = not_concatened_dd[m].copy().div(VHMax) #not_concatened_dd[m]/VHMax
        RC = [None]*z # append não funcionou >? talvez porque usei o tamanho inteiro da array > TypeError: 'NoneType' object is not subscriptable
        for contador in range(len(cm)):#
            RC[contador] = cm[contador][10:23].copy() # 1 MIN para cada tdms
        Media_dict,fr = pos_calibracao(fre,RC,Media_dict,files,matriz_transf)
        fr_all[files] = fr

    # plot_color_map(fr1.apply(pd.to_numeric, errors='coerce'),files)

    VL_COMPARACAO = VHMax - VLMax

    VL_COMPARACAO =  VLMax.div(VHMax)

    return fr_all,VL_COMPARACAO

def min_max(fr_all):
    fr_max = 0
    fr_min = 0
    for value in fr_all:
        fr_aux = fr_all[value]['fr1'][0].max().max()
        if fr_aux>fr_max:
            fr_max = fr_aux
        fr_aux = fr_all[value]['fr1'][0].min().min()
        if fr_aux>fr_min:
            fr_min = fr_aux
    return fr_min,fr_max