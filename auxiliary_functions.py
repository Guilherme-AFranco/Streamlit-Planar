from nptdms import TdmsFile
from plotly.subplots import make_subplots
import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import concurrent.futures
import re

from db_functions import *

# Lê todos os arquivos em uma pasta e retorna o full path
def dirList(directory):
    all_files = []
    for dirpath,_,filenames in os.walk(directory):
        for f in filenames:
            all_files.append(os.path.abspath(os.path.join(dirpath, f)))
    return all_files

# Transforma a lista de arquivos em dicionário e organiza por número
def dirDict(dirList, Rx):
    dirDict = {}
    i = 0
    for value in dirList:
        if value.endswith(".tdms"):
            i+=1
            valueName = value.split("\\")[-1]
            if "-" in valueName:
                valueSize = valueName.split("-")[0]
            else:
                valueSize = valueName.split(".")[0]
            if not valueSize in dirDict:
                dirDict[valueSize] = [value]
            else:
                dirDict[valueSize].append(value)
    if Rx is not None:
        if i!=Rx:
            st.write("Inclua uma quantidade de arquivos igual a quantidade de faixa Rx para a calibração")
            return None
    for value in dirDict:
        dirDict[value].sort()
    return dirDict

# Captura os dados de cada arquivo e inclui em um dataframe
def processFile(file):
    try:
        if file.endswith("tdms"):
            df = TdmsFile.read(file).as_dataframe()
            conv = 2 / (2**16 - 1)
            if df is not None:
                df.insert(0, 'Seconds', np.arange(0, len(df) * conv, conv)[:len(df)])
    except:
        st.write(f"Erro na coleta dos arquivos.")
    return df
def catchData(file):
    dfList = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(processFile, file)
        for result in results:
            if result is not None:
                dfList.append(result)
    return dfList




#Corrigir para que aceite MAIS DO QUE 16 Rx
# Insere os dados do sensor planar no banco de dados
def DBInsert(connection,dirDict,varList):
    try:
        statusMessage = st.empty()
        with connection:
            for valor in dirDict:
                for k in range(len(dirDict[valor])):
                    if '-' in dirDict[valor][k].split('\\')[-1]:
                        table_name = f'{valor}_{k+1:02d}'
                    else:
                        table_name = f'{valor}'
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
            for index, valor in enumerate(dirDict):
                for k in range(len(dirDict[valor])):
                    if '-' in dirDict[valor][k].split('\\')[-1]:
                        table_name = f'{valor}_{dirDict[valor][k][-7:-5]}'
                    else:
                        table_name = f'{valor}'
                    varList[index][k] = varList[index][k].fillna(0).rename(columns=lambda x: x.replace("/'Data'/", "").replace("'", ""))
                    data_list = []
                    for _, row in varList[index][k].iterrows():
                        data = (row['Seconds'], *[row[f'Rx{str(i).zfill(2)}'] for i in range(16)])
                        data_list.append(data)
                    with connection.cursor() as cursor:
                        sql = (
                            f'INSERT INTO {table_name} '
                            '(Seconds, Rx00, Rx01, Rx02, Rx03, Rx04, Rx05, Rx06, Rx07, Rx08, Rx09, Rx10, Rx11, Rx12, Rx13, Rx14, Rx15) '
                            'VALUES '
                            '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
                        )
                        cursor.executemany(sql, data_list)
                    statusMessage.empty()
                    statusMessage.write(f"Arquivo {k+1} alocado no banco de dados.")
                    connection.commit()
                statusMessage.empty()
    except:
        st.write("Conexão com o banco de dados interrompida.")

# Obtém nome dos arquivos segmentados
def valueExtract(valor, stringFormat="simple"):
    if stringFormat == "simple":
        return valor.split('_')[0]
    elif stringFormat == "matrix":
        return '_'.join(valor.split('_')[:2])
    elif stringFormat == "end":
        return valor.split('_', 1)[1]
    elif stringFormat == "regex":
        match = re.match(r'^(.*)_\d{2}$', valor)
        if match:
            return match.group(1)
        return valor
    else:
        return valor

# Coleta dos dados dos cilindros para calibração
def importData(data):
    engine = SQLEngine()
    for value in data:
        data[value] = {item: None for item in data[value]}
    for dataName in data:
        for dataDF in data[dataName]:
            query = f'SELECT * FROM {dataDF}'
            data[dataName][dataDF] = pd.read_sql(query, con=engine)
            data[dataName][dataDF] = data[dataName][dataDF][[col for col in data[dataName][dataDF].columns if col.startswith('Rx')]]
    return data



# Dá pra integrar junto com a parte do código de getParameters
# Coleta dos dados do VH para calibração
def vhData(vhName):
    engine = SQLEngine()
    query = f'SELECT * FROM {vhName}'
    vh = {f"{vhName}": pd.read_sql(query, con=engine)}
    vh[vhName] = -1*vh[vhName][[col for col in vh[vhName].columns if col.startswith('Rx')]]
    rx = len(vh[vhName].keys())
    vhMax = vh[vhName].values.reshape(32, rx, int(len(vh[vhName])/32))  
    conv = 2 / (2**rx - 1)
    vhMax = np.mean(vhMax * conv, axis=2)
    return vhMax,conv,rx

# Obtenção dos parametros de mínimo e média de calibração
def getParameters(data, vhMax, conv, rx, tx):
    try:
        meanRc = {}
        minRx = {}
        df_minRx = pd.DataFrame()
        for dataName in data:
            meanRc[dataName] = {}
            minRx[dataName] = {}
            for index, thickDF in enumerate(data[dataName]):
                data[dataName][thickDF] = -1*data[dataName][thickDF]
                data[dataName][thickDF] = data[dataName][thickDF].values.reshape(32, rx, int(len(data[dataName][thickDF])/32))
                data[dataName][thickDF] = data[dataName][thickDF]*conv
                x, y, z = data[dataName][thickDF].shape
                cm = np.zeros((x,y,z)) 
                for z_i in np.arange(z):
                    cm[:,:,z_i] = data[dataName][thickDF][:,:,z_i]/vhMax
                cm[cm>1] = 1
                RC = cm[10:(10+tx),:,:]
                mean_Rc = np.mean(RC,axis=2)
                RC_i = mean_Rc[:,index]
                min_Rc_i = np.min(RC_i)
                minRx[dataName][f'Rx{index+1:02d}'] = np.array([min_Rc_i] * tx)
                meanRc[dataName][f'Rx{index+1:02d}'] = RC_i
        df_meanRc = pd.DataFrame.from_dict(meanRc,orient='index')
        df_meanRc = df_meanRc.T
        df_minRx = pd.DataFrame.from_dict(minRx,orient='index')
        df_minRx = df_minRx.T
    except:
        st.write('Ocorreu um erro ao obter os valores de mínimo e média')
    return df_minRx, df_meanRc

# Obtenção do polinomio de 4o grau
def polyFit(min, tx, rx, nPoints):
    thickness = []
    pixelValues = []
    for thick in min.keys():
        minRow = np.vstack(min[thick].values).T
        pixelValues.append(minRow[tx-1,rx-1])
        thickness.append(int(thick.replace('u', '')))
    pixelValues = np.array(pixelValues)
    thickness = np.array(thickness)
    fit = np.polyfit(thickness, pixelValues, 4)
    fit = np.poly1d(fit)
    thickValues = np.linspace(0, thickness.max(), nPoints)
    voltage = fit(thickValues)
    return fit, thickValues, voltage

# Obtenção das curvas de calibração a partir dos valores mínimos
def calCurve1(minRx, tx, rx):
    calPixel = np.zeros((tx, rx, 5))
    nPoints = 100
    voltage = np.zeros((tx,rx,nPoints))
    try:
        for txIdx in range(tx):
            for rxIdx in range(rx):
                fit, thickValue, Volt = polyFit(minRx,txIdx,rxIdx,nPoints)
                voltage[txIdx,rxIdx,:] = Volt
                calPixel[txIdx, rxIdx, :5] = fit
    except:
                st.write(f'Ocorreu um erro na geração das curvas de ajuste')
    return calPixel, thickValue, voltage

# Curvas de calibração a partir dos coeficientes de calibração
def calCurve2(matrix):
    matrixNames = list(matrix.keys())
    rxNames = list(matrix[matrixNames[0]])
    tx = len(matrix[matrixNames[0]][rxNames[0]])
    fit = np.zeros([tx, len(rxNames), 5])
    Npoints = 100
    voltage = np.zeros([tx,len(rxNames),Npoints])
    for rxValue, rxName in enumerate(rxNames):
        fit[:, rxValue, :] = np.column_stack([matrix[matrixNames[i]][rxName] for i in range(5)])
    for txIdx in range(tx):
        for rxIdx in range(len(rxNames)):
            fit1 = np.poly1d(fit[txIdx,rxIdx])
            thickValue = np.linspace(0, 2200, Npoints)
            voltage[txIdx,rxIdx,:] = fit1(thickValue)
    return thickValue, voltage

# Representação gráfica das curvas de calibração
def plotCalib(thickValue, voltage,rx=None):
    fig = go.Figure()
    if voltage.ndim == 3:
        for m in range(len(voltage[0,:,0])):
            fig.add_trace(go.Scatter(x=thickValue, y=np.mean(voltage[:,m,:], axis=0), mode='lines', name=f'Rx{m+1:02d}'))
            title = 'Curvas de Grau 4 - Matriz de calibração'
    else:
        fig.add_trace(go.Scatter(x=thickValue, y=np.mean(voltage, axis=0), mode='lines', name=f'Rx{rx:02d}'))
        title = f'Curvas de Grau 4 - Rx{rx:02d}'
    fig.update_layout(
        title=title,
        xaxis_title='Espessura (10^-6 m)',
        yaxis_title='Tensão (V)',
        showlegend=True,
        template='plotly_white'
    )
    return fig

# Criação das figuras representativas de dados brutos de coleta, de dados processados para média e dados de mínimo valor de cada coluna ou média ajustada
def basicPlot(data, minRx, meanRc, rx, tx, type):
    rótulos_x = [f'R{i:02}' for i in range(1, rx+1)]
    rótulos_y = [f'T{i:02}' for i in range(1, tx+1)]
    if type == 'min':
        fig = make_subplots(rows=1, cols=3, subplot_titles=["GIF", "Média", "Mínimo"],shared_yaxes=False, horizontal_spacing=0.05)
    elif type == 'fit':
        fig = make_subplots(rows=1, cols=3, subplot_titles=["GIF", "Média", "Média calibrada"],shared_yaxes=False, horizontal_spacing=0.05)
    fig.add_trace(go.Heatmap(z=data[next(iter(data))][10:(10+tx), :, 0],x=rótulos_x,y=rótulos_y,
                             colorscale='Blues',colorbar=dict(title="", thickness=10, len=1.1, x=0.3, tickformat=".2f")), row=1, col=1)
    frames = []
    for value in data:
        num_coletas = data[value].shape[2]
        for fValue in range(num_coletas):
            frame_data = data[value][10:(10+tx), :, fValue]
            frames.append(go.Frame(data=[go.Heatmap(z=frame_data,x=rótulos_x,y=rótulos_y,colorscale='Blues')]))
    fig.update(frames=frames)
    heatmap2 = go.Heatmap(z=np.vstack(meanRc.values).T, x=rótulos_x, y=rótulos_y,
                          colorscale='Blues',showscale=True, colorbar=dict(title="", thickness=10, len=1.1, x=0.65, tickformat=".2f"))
    fig.add_trace(heatmap2, row=1, col=2)
    heatmap3 = go.Heatmap(z=np.vstack(minRx.values).T, x=rótulos_x, y=rótulos_y,
                          colorscale='Blues',showscale=True, colorbar=dict(title="", thickness=10, len=1.1, x=1, tickformat=".2f"))
    fig.add_trace(heatmap3, row=1, col=3)
    fig.update_layout(
        title={'text': 'Análise visual dos valores para calibração','y': 0.9,'x': 0.5,'xanchor': 'center','yanchor': 'top'},
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white",
        yaxis2=dict(showticklabels=False),
        yaxis3=dict(showticklabels=False),
        updatemenus=[{"buttons": [{
                "args": [None, {"frame": {"duration": 5, "redraw": True}, "fromcurrent": True}],
                "label": "Play",
                "method": "animate"
            },
            {
                "args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}],
                "label": "Pause",
                "method": "animate"
            }],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }]
    )
    return fig

def analysisParameters(data, matrixCal, vhMax, rx, tx, conv):
    meanRc = {}
    fit = {}
    coefName = list(matrixCal.keys())
    for dataName in data:
        meanRc[dataName] = {}
        for thickDF in data[dataName]:
            meanRc[thickDF] = {}
            fit[thickDF] = {}
            data[dataName][thickDF] = -1*data[dataName][thickDF]
            data[dataName][thickDF] = data[dataName][thickDF].values.reshape(32, rx, int(len(data[dataName][thickDF])/32))
            data[dataName][thickDF] = data[dataName][thickDF]*conv
            x, y, z = data[dataName][thickDF].shape
            cm = np.zeros((x,y,z))
            for z_i in np.arange(z):
                cm[:,:,z_i] = data[dataName][thickDF][:,:,z_i]/vhMax
            cm[cm>1] = 1
            RC = cm[10:(10+tx),:,:]
            mean_Rc = np.mean(RC,axis=2)
            fitResult = (sum(matrixCal[coefName[i]] * mean_Rc**i for i in range(5))).values
            for i in range(mean_Rc.shape[1]):
                meanRc[thickDF][f'Rx{i:02d}'] = mean_Rc[:,i]
                fit[thickDF][f'Rx{i:02d}'] = fitResult[:,i]
    df_meanRc = pd.DataFrame.from_dict(meanRc,orient='index')
    df_meanRc = df_meanRc.T
    df_fit = pd.DataFrame.from_dict(fit,orient='index')
    df_fit = df_fit.T
    return df_fit, df_meanRc