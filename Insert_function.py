import os
import pymysql
import dotenv
from tqdm import tqdm
import pandas as pd
from nptdms import TdmsFile

from planar_functions import *

def insert_calibration(file_path):
    dotenv.load_dotenv()

    connection = pymysql.connect(
        host=os.environ['MYSQL_HOST'],
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
        database=os.environ['MYSQL_DATABASE'],
    )

    lista_tdms = absoluteFilePaths(file_path)
    calibrations_dict_path = dict_por_espessura(lista_tdms)
    #display(calibrations_dict_path)

    lista_medias_por_espessura = []

    lista_varcalib = []

    for elements in calibrations_dict_path:
        lista_df = calibrations_tdsm(calibrations_dict_path[elements])
        lista_varcalib.append(lista_df)

    #Criar um with pra cada um
    with connection:
        for index, valor in enumerate(calibrations_dict_path):
            for k, l in enumerate(calibrations_dict_path[valor]):
                table_name = f'{valor}_{calibrations_dict_path[valor][k][-7:-5]}'
                st.write(table_name)
                with connection.cursor() as cursor:
                    sql = (
                        f'CREATE TABLE IF NOT EXISTS {table_name} ('
                        'id INT AUTO_INCREMENT PRIMARY KEY, '
                        'Seconds FLOAT, '
                        'Rx00 FLOAT, Rx01 FLOAT, Rx02 FLOAT, Rx03 FLOAT, '
                        'Rx04 FLOAT, Rx05 FLOAT, Rx06 FLOAT, Rx07 FLOAT, '
                        'Rx08 FLOAT, Rx09 FLOAT, Rx10 FLOAT, Rx11 FLOAT, '
                        'Rx12 FLOAT, Rx13 FLOAT, Rx14 FLOAT, Rx15 FLOAT'
                        ') '
                    )
                    cursor.execute(sql)
                connection.commit()

        for index, valor in enumerate(calibrations_dict_path):
            for k, l in enumerate(calibrations_dict_path[valor]):
                table_name = f'{valor}_{calibrations_dict_path[valor][k][-7:-5]}'
                # Renomear colunas para remover partes indesejadas
                lista_varcalib[index][k] = lista_varcalib[index][k].fillna(0)
                lista_varcalib[index][k].columns = lista_varcalib[index][k].columns.str.replace("/'Data'/", "")
                lista_varcalib[index][k].columns = lista_varcalib[index][k].columns.str.replace("'", "")
                
                data_list = []
                for idx, row in lista_varcalib[index][k].iterrows():
                    data = (row['Seconds'], row['Rx00'], row['Rx01'], row['Rx02'], row['Rx03'], row['Rx04'], row['Rx05'], row['Rx06'], row['Rx07'], row['Rx08'], row['Rx09'], row['Rx10'], row['Rx11'], row['Rx12'], row['Rx13'], row['Rx14'], row['Rx15'])
                    data_list.append(data)

                with connection.cursor() as cursor:
                    sql = (
                        f'INSERT INTO {table_name} '
                        '(Seconds, Rx00, Rx01, Rx02, Rx03, Rx04, Rx05, Rx06, Rx07, Rx08, Rx09, Rx10, Rx11, Rx12, Rx13, Rx14, Rx15) '
                        'VALUES '
                        '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
                    )
                    cursor.executemany(sql, data_list)
                connection.commit()

def exclude_calibration(file_path):
    dotenv.load_dotenv()

    connection = pymysql.connect(
        host=os.environ['MYSQL_HOST'],
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
        database=os.environ['MYSQL_DATABASE'],
    )

    table_name = file_path
    with connection:
        with connection.cursor() as cursor:
            sql = (
                f'DROP TABLE {table_name}'
            )
            cursor.execute(sql)
        connection.commit()

def insert_matriz(matriz, matriz_name):
    dotenv.load_dotenv()

    connection = pymysql.connect(
        host=os.environ['MYSQL_HOST'],
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
        database=os.environ['MYSQL_DATABASE'],
    )

    #Criar um with pra cada um
    with connection:
        for index, valor in enumerate(matriz):
            for idx, linha in enumerate(valor):
                if index<10:
                    table_name = f'{matriz_name}_0{index}'
                else:
                    table_name = f'{matriz_name}_{index}'
                with connection.cursor() as cursor:
                    sql = (
                        f'CREATE TABLE IF NOT EXISTS {table_name} ('
                        'id INT AUTO_INCREMENT PRIMARY KEY, '
                        'a FLOAT, b FLOAT, c FLOAT, d FLOAT, e FLOAT'
                        ') '
                    )
                    cursor.execute(sql)
                connection.commit()

        for index, valor in enumerate(matriz):
            for idx, row in enumerate(valor):
                if index<10:
                    table_name = f'{matriz_name}_0{index}'
                else:
                    table_name = f'{matriz_name}_{index}'
                data_list = []
                data = (row[0], row[1], row[2], row[3], row[4])
                data_list.append(data)

                with connection.cursor() as cursor:
                    sql = (
                        f'INSERT INTO {table_name} '
                        '(a, b, c, d, e) '
                        'VALUES '
                        '(%s, %s, %s, %s, %s) '
                    )
                    cursor.executemany(sql, data_list)
                connection.commit()