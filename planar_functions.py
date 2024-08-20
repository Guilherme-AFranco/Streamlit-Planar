from nptdms import TdmsFile
import concurrent.futures
from IPython.display import display
import pandas as pd
import os
import numpy as np
import streamlit as st

import matplotlib.pyplot as plt

#Desconcatena e Realiza a média da matriz na terceira dimensão
def mean_3(dataframe): #Versão atualizada no mean_3
  x_axis_atual = dataframe.shape[0]
  x_axis_original = 32 ## Número no tdms original // x = rows
  z_axis_original = x_axis_atual/x_axis_original

  not_concatened_df = []
  for i in range(int(z_axis_original)):
    not_concatened_df.append(dataframe.iloc[32*(i):32*(i+1)].copy().reset_index().drop(columns=['index']))

  df = not_concatened_df[0].copy()
  for elements in not_concatened_df[1:]:
    df += elements.values
  df = df/len(not_concatened_df)

  return df, not_concatened_df

#Lê todos os arquivos em uma pasta e retorna o full path
def absoluteFilePaths(directory):
    all_files = []
    for dirpath,_,filenames in os.walk(directory):
        for f in filenames:
            all_files.append(os.path.abspath(os.path.join(dirpath, f)))
    return all_files

#Plota individualmente um colormap dando um path de um arquivo tdms ou a partir dataframe
def plot_color_map(path_calib_tdsm, name_file, v_min, v_max):
  # fig, axs = plt.subplots(1, 1)
  # fig.suptitle('Média Temporal: ' + name_file)
  # graf = axs.matshow(path_calib_tdsm.to_numpy(), cmap='Blues', aspect='auto', vmin=v_min, vmax=v_max)
  # plt.colorbar(graf)
  # plt.show()
  fig, axs = plt.subplots(1, 1)
  fig.suptitle('Média Temporal: ' + name_file)
  graf = axs.matshow(path_calib_tdsm.to_numpy(), cmap='Blues', aspect='auto', vmin=v_min, vmax=v_max)
  plt.colorbar(graf)
  
  # Exibe o gráfico no Streamlit
  st.pyplot(fig)
  plt.close()

def plot_color_map_duo(path_calib_tdsm,media_total_calibrations,current_directory, save_path=""):
  name_file = path_calib_tdsm.split("\\")[-1]
  fig, axs = plt.subplots(1, 2)
  fig.suptitle('Média Temporal e Diferença da média: '+name_file)

  conv = 2/(2**16-1)
  calib_tdsm = TdmsFile.read(path_calib_tdsm).as_dataframe().multiply(-1).multiply(conv)
  abc, cdf = mean_3(calib_tdsm)
  #colormap 1
  graf = axs[0].matshow(abc, cmap='Blues', aspect='auto')
  #colormap 2
  graf = axs[1].matshow(abc-media_total_calibrations, cmap='Blues', aspect='auto')

  if not os.path.exists(current_directory+"\\Resultados"):
    os.makedirs(current_directory+"\\Resultados")

  if save_path == "":
    plt.savefig(current_directory+"\\Resultados\\"+name_file+".png")
  else:
    if not os.path.exists(current_directory+"\\Resultados\\"+save_path):
      os.makedirs(current_directory+"\\Resultados\\"+save_path)
    plt.savefig(current_directory+"\\Resultados\\"+save_path+"\\"+name_file+".png")

#Plota 3 colormaps (média temporal e diferença da média das calibrações) dando um path de um arquivo tdms
#alt 1: printar junto a média total
#alt 2: dividir pela média total ao invés de subtrair
#alt 3: dividir pelo vhmax
def plot_color_map_trio(path_calib_tdsm,name_file,media_total_calibrations):
  fig, axs = plt.subplots(1, 3, figsize=(18, 6))
  fig.suptitle('Média Temporal, V-MED ou V-Max, Div da média: '+name_file)

  conv = 2/(2**16-1)
  calib_tdsm = path_calib_tdsm.multiply(-1).multiply(conv)
  abc, cdf = mean_3(calib_tdsm)
  #colormap 1
  graf = axs[0].matshow(abc, cmap='Blues', aspect='auto')
  #colormap 2
  graf = axs[1].matshow(media_total_calibrations, cmap='Blues', aspect='auto')
  #colormap 3
  graf = axs[2].matshow(abc.div(media_total_calibrations), cmap='Blues', aspect='auto')
  
  #https://stackoverflow.com/questions/13784201/how-to-have-one-colorbar-for-all-subplots
  fig.subplots_adjust(right=0.8)
  cbar_ax = fig.add_axes([0.85, 0.15, 0.05, 0.7])
  fig.colorbar(graf, cax=cbar_ax)
  return fig

def plot_color_map_together(path_calib_tdsm_list): #Plota em conjunto uma lista de path de arquivo tdms (precisa da lista já filtrada)
  fig, axs = plt.subplots(1, len(path_calib_tdsm_list))
  fig.suptitle('Média Temporal')
  contador = 0
  for elements in path_calib_tdsm_list:
    conv = 2/(2**16-1)
    calib_tdsm = TdmsFile.read(elements).as_dataframe().multiply(-1).multiply(conv)
    abc, cdf = mean_3(calib_tdsm)

    graf = axs[contador].matshow(abc.to_numpy(), cmap='Blues', aspect='auto')
    plt.colorbar(graf)
    contador += 1

#inserir a lista de paths tdms e retorna um dict apenas com os necessários
def dict_por_espessura(lista_tdms):
    calibrations_dict_path = {}
    for elements in lista_tdms: #Cria um dict com key = espessura do filme, e os valores os paths
        if elements.endswith(".tdms"):
            elements_name = elements.split("\\")[-1]
            if "_" in elements_name:
                elements_size = elements_name.split("_")[1]
            elif "-" in elements_name:
                elements_size = elements_name.split("-")[0]
            else:
                elements_size = elements_name # Se não houver "_" ou "-", usa o nome do arquivo inteiro como chave

            if not elements_size in calibrations_dict_path:
                calibrations_dict_path[elements_size] = [elements]
            else:
                calibrations_dict_path[elements_size].append(elements)
        
    for elements in calibrations_dict_path: # Sort especial para deixar em ordem pois o sort normal não funciona (testar caso tenha mais de 20)
        for i in range(len(calibrations_dict_path[elements])-9):
            calibrations_dict_path[elements] += [calibrations_dict_path[elements].pop(1)]

    #display(calibrations_dict_path)
    for elements in calibrations_dict_path: # remove os elementos repetidos no caso 1,2... quando maior que 16 // agora pode ser simplificado já que crie o sort, mas contua rápido e elaborado caso mude no futuro
        if len(calibrations_dict_path[elements]) > 16:
            for i in range(len(calibrations_dict_path[elements])-16):
                contador = 0
                for j in calibrations_dict_path[elements]:
                    if "-"+str(i+1)+"." in j:
                        calibrations_dict_path[elements].pop(contador)
                    elif "_"+str(i+1)+"." in j:
                        calibrations_dict_path[elements].pop(contador)
                    contador+=1
    return calibrations_dict_path

def media_calibrations_tdsm(path_calib): #Retorna e plota a média de um conjuto de arquivos tdsm
  mean_list = []
  for elements in path_calib:
    conv = 2/(2**16-1)
    calib_tdsm = elements.multiply(-1).multiply(conv)
    abc, cdf = mean_3(calib_tdsm)
    mean_list.append(abc)
  mean_list = pd.concat(mean_list).groupby(level=0).mean()
  return mean_list

def process_file(file):
    if file.endswith("tdms"):
      df = TdmsFile.read(file).as_dataframe()
      if df is not None:
        # Calcula os valores da coluna de segundos
        num_rows = len(df)
        interval = 2 / (2**16 - 1)
        seconds = np.arange(0, num_rows * interval, interval)[:num_rows]
        # Adiciona a coluna de segundos ao DataFrame
        df.insert(0, 'Seconds', seconds)
      return df

def calibrations_tdsm(calib_tdsm_file): 
    mean_list = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(process_file, calib_tdsm_file)
        for result in results:
            if result is not None:
                mean_list.append(result)
    return mean_list

def pos_calibracao(fre,RC,Media_dict,tdms_files,B5): #rotina que segue depois do importe do arquivo de calibração
  # Film Thickness
  delta = [None]*(fre)#-1000
  for m in range(fre):#-1000
    # T1=RC[m].copy().pow(4).multiply(B5[:,:,0]) # acho que não precisa de copy aqui
    # T2=RC[m].copy().pow(3).multiply(B5[:,:,1])
    # T3=RC[m].copy().pow(2).multiply(B5[:,:,2])
    # T4=RC[m].copy().multiply(B5[:,:,3])
    # T5=B5[:,:,4].copy()
    T1=RC[m].copy().pow(4).reset_index(drop=True).multiply(B5['a']) # acho que não precisa de copy aqui
    T2=RC[m].copy().pow(3).reset_index(drop=True).multiply(B5['b'])
    T3=RC[m].copy().pow(2).reset_index(drop=True).multiply(B5['c'])
    T4=RC[m].copy().reset_index(drop=True).multiply(B5['d'])
    T5=B5['e'].copy()
    delta[m] = (T1.add(T2).add(T3).add(T4).add(T5))#.astype("uint16")
    delta[m][delta[m]<0]=0
    delta[m][delta[m]>2200]=2200 # acho que aqui era para ser 2200 e colocaram errado no original

  # Mean film thickness
  MeanMean = 0
  for element in delta:
    MeanMean += element.mean(axis=None)#element.stack().std() # confirmar se std é mean()
  MeanMean = MeanMean/len(delta)
  Media_dict[tdms_files] = MeanMean
  MeanFra = mean_3(pd.concat(delta))

  fr1=delta[199]
  fr2=delta[200]
  fr3=delta[201]
  fr4=delta[202]

  fr = {'fr1': [fr1],
        'fr2': [fr2],
        'fr3': [fr3],
        'fr4': [fr4]}
  # display(RC[199])
  # display(fr1)
  # plot_color_map(fr1)
  return Media_dict, fr