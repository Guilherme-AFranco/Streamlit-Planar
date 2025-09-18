from packs import *

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
            time = 313*1/50e6
            if df is not None:
                df.insert(0, 'Seconds', np.arange(0, len(df) * time, time)[:len(df)])
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
                            'Rx01 FLOAT, Rx02 FLOAT, Rx03 FLOAT, Rx04 FLOAT, '
                            'Rx05 FLOAT, Rx06 FLOAT, Rx07 FLOAT, Rx08 FLOAT, '
                            'Rx09 FLOAT, Rx10 FLOAT, Rx11 FLOAT, Rx12 FLOAT, '
                            'Rx13 FLOAT, Rx14 FLOAT, Rx15 FLOAT, Rx16 FLOAT'
                            ') '
                        )
                        cursor.execute(sql)
                    connection.commit()
            for index, valor in enumerate(dirDict):
                statusMessage.write(f"Arquivo {index} de {len(dirDict)} alocado no banco de dados.")
                for k in range(len(dirDict[valor])):
                    if '-' in dirDict[valor][k].split('\\')[-1]:
                        table_name = f'{valor}_{dirDict[valor][k][-7:-5]}'
                    else:
                        table_name = f'{valor}'
                    varList[index][k] = varList[index][k].fillna(0).rename(columns=lambda x: x.replace("/'Data'/", "").replace("'", ""))
                    # data_list = []
                    # for _, row in varList[index][k].iterrows():
                    #     data = (row['Seconds'], *[row[f'Rx{str(i).zfill(2)}'] for i in range(16)])
                    #     data_list.append(data)
                    data_list = [(row.Seconds, *[getattr(row, f'Rx{str(i).zfill(2)}') for i in range(16)]) for row in varList[index][k].itertuples(index=False)]

                    with connection.cursor() as cursor:
                        sql = (
                            f'INSERT INTO {table_name} '
                            '(Seconds, Rx01, Rx02, Rx03, Rx04, Rx05, Rx06, Rx07, Rx08, Rx09, Rx10, Rx11, Rx12, Rx13, Rx14, Rx15, Rx16) '
                            'VALUES '
                            '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) '
                        )
                        cursor.executemany(sql, data_list)
                    statusMessage.empty()
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

# Obtenção dos parametros de mínimo e média de calibração
def getParameters(data, vhMax, rx, tx, type):
    try:
        meanRc = {}
        minRx = {}
        df_minRx = None
        RCdata = {}
        if type=='Analise':
            vhMax1 = vhMax
        for dataName in data:
            minRx.setdefault(dataName, {})
            RCdata.setdefault(dataName, {})
            if type == 'Faixas':
                meanRc.setdefault(dataName, {})
                try:
                    vhAux1 = data[dataName][f'{dataName}_02']
                    vhAux2 = data[dataName][f'{dataName}_15']
                except:
                    st.write('Arquivo de entrada deve ter nome XXXXu_XX.')
                vhAux1 = np.abs(vhAux1)
                vhAux2 = np.abs(vhAux2)
                vhAux1 = np.double(np.transpose(vhAux1.values.reshape(int(len(vhAux1)/16),16,16),(1,2,0)))
                vhAux2 = np.double(np.transpose(vhAux2.values.reshape(int(len(vhAux2)/16),16,16),(1,2,0)))
                vhMax1 = np.zeros(vhMax.shape)
                vhMax1[:,:8] = np.mean(vhAux2[:,:8,:],axis=2)
                vhMax1[:,8:] = np.mean(vhAux1[:,8:,:],axis=2)
            else:
                matrixMin = None
            for index, thickDF in enumerate(data[dataName]):
                data[dataName][thickDF] = np.abs(data[dataName][thickDF])
                data[dataName][thickDF] = np.transpose(data[dataName][thickDF].values.reshape(int(len(data[dataName][thickDF])/16),16,16),(1,2,0))
                data[dataName][thickDF] = np.double(data[dataName][thickDF])
                x, y, z = data[dataName][thickDF].shape
                cm = np.zeros((x,y,z)) 
                RCdata[dataName][thickDF] = np.zeros((tx,y,z))
                if type == 'Amostras':
                    vhMax1 = np.mean(np.sort(data[dataName][thickDF],axis=2)[:,:,-int(z*0.75):],axis=2)
                for z_i in np.arange(z):
                    cm[:,:,z_i] = data[dataName][thickDF][:,:,z_i]/vhMax1
                RCdata[dataName][thickDF] = cm[0:13,:,:]
                RCdata[dataName][thickDF][RCdata[dataName][thickDF]>1] = 1
                RCmin = [np.mean(RCdata[dataName][thickDF][:, :, i:i+20], axis=2) for i in range(0, RCdata[dataName][thickDF].shape[2], 20) if i+20 <= RCdata[dataName][thickDF].shape[2]]
                RCmin = np.stack(RCmin, axis=2)
                if type == 'Faixas':
                    min_Rx = np.min(RCmin[:,index,:],axis=1)
                    minRx[dataName][f'Rx{index+1:02d}'] = min_Rx
                else:
                    min_Rx = np.min(RCmin,axis=2)
                    if matrixMin is not None:
                        matrixMin += min_Rx/len(data[dataName])
                    else:
                        matrixMin = min_Rx/len(data[dataName])
            if type == 'Amostras':
                for i in range(rx):
                    minRx[dataName][f'Rx{i+1:02d}'] = matrixMin[:, i]
        df_minRx = pd.DataFrame.from_dict(minRx,orient='index')
        df_minRx = df_minRx.T
    except Exception as e:
        st.write('Ocorreu um erro ao obter os valores de mínimo e média', e)
    if type == 'Faixas':
        return df_minRx, data
    else:
        return df_minRx, RCdata

# Obtenção do polinomio de 4o grau
def polyFit(minRx, thickness, nPoints, txIdx, rxIdx):
    voltage = []
    for thick in minRx.keys():
        voltage.append(minRx[thick][rxIdx][txIdx].mean())
    voltage = np.array(voltage)
    thickValues = np.linspace(thickness.min(), thickness.max(), nPoints)
    fit = np.polyfit(thickness,voltage, deg=4)
    fit = np.poly1d(fit)
    voltageValues = fit(thickValues)
    return fit, voltageValues, thickValues, voltage

# Obtenção das curvas de calibração a partir dos valores mínimos
def calCurve1(minRx, tx, rx):
    calPixel = np.zeros((tx, rx, 5))
    nPoints = 100
    thick = np.zeros((tx,rx,nPoints))
    voltageValues = np.zeros((tx,rx,nPoints))
    thickness = []
    try:
        for thickName in minRx.keys():
            valor = int(thickName.replace('u', ''))
            thickness.append(valor)
        thickness = np.array(thickness)
        volt = np.zeros((tx,rx,len(thickness)))
        for txIdx in range(tx):
            for rxIdx in range(rx):
                fit, voltValues, thickValues, voltage = polyFit(minRx,thickness,nPoints,txIdx,rxIdx)
                calPixel[txIdx,rxIdx,:5] = fit
                thick[txIdx, rxIdx, :] = thickValues
                voltageValues[txIdx, rxIdx, :] = voltValues
                volt[txIdx,rxIdx,:] = voltage
    except:
                st.write(f'Ocorreu um erro na geração das curvas de ajuste')
    return calPixel, voltageValues, thick, volt

# Curvas de calibração a partir dos coeficientes de calibração
def calCurve2(matrix):
    matrixNames = list(matrix.keys())
    rxNames = list(matrix[matrixNames[0]])
    tx = len(matrix[matrixNames[0]][rxNames[0]])
    fit = np.zeros([tx, len(rxNames), 5])
    for rxValue, rxName in enumerate(rxNames):
        fit[:, rxValue, :] = np.column_stack([matrix[matrixNames[i]][rxName] for i in range(5)])
    return fit

# Representação gráfica das curvas de calibração
def plotCalib(calPixel, rx=None, tx=None):
    x = np.linspace(400, 2200, 200)
    fig = go.Figure()
    colors = [
        f'rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {a})'
        for r, g, b, a in plt.cm.tab20(np.linspace(0, 1, 16))
    ]
    dim = len(calPixel.shape)
    if dim == 3:
        for idxRx in range(calPixel.shape[1]):
            for idxTx in range(calPixel.shape[0]):
                polinomio = np.poly1d(calPixel[idxTx, idxRx])
                y_novo = polinomio(x)
                fig.add_trace(go.Scatter(x=x,y=y_novo,mode='lines',line=dict(color=colors[idxRx]),name=f'Rx{idxRx+1:02d}' if idxTx == 0 else None,showlegend=(idxTx == 0)))
    elif dim == 2:
        for idx in range(calPixel.shape[0]):
            if rx is not None:
                polinomio = np.poly1d(calPixel[idx,:])
                y_novo = polinomio(x)
                fig.add_trace(go.Scatter(x=x,y=y_novo,mode='lines',line=dict(color=colors[idx]),name=f'Tx{idx+1:02d}'))
            else:
                polinomio = np.poly1d(calPixel[idx,:])
                y_novo = polinomio(x)
                fig.add_trace(go.Scatter(x=x,y=y_novo,mode='lines',line=dict(color=colors[idx]),name=f'Rx{idx+1:02d}'))
    else:
        polinomio = np.poly1d(calPixel)
        y_novo = polinomio(x)
        fig.add_trace(go.Scatter(x=x,y=y_novo,mode='lines',line=dict(color=colors[rx]),name=f'Rx{rx+1:02d}, Tx{tx+1:02d}'))
    title = f'Curvas de Grau 4'
    fig.update_layout(title=title,xaxis_title='Espessura (10⁻⁶ m)',yaxis_title='Tensão (V)',showlegend=True,template='plotly_white',width=800)
    return fig

def basicPlot(data, rx, nome,ylab=""):
    rótulos_x = [f'R{i:02}' for i in range(1, rx+1)]
    rótulos_y = [f'T{i:02}' for i in range(1, 16)]
    fig = make_subplots(rows=1, cols=1, shared_yaxes=False, horizontal_spacing=0.05)
    fig.add_trace(go.Heatmap(z=data[:, :, 0],zmin=data.min(),zmax=data.max(),x=rótulos_x,y=rótulos_y,
                             colorscale='Blues',colorbar=dict(title=ylab, thickness=10, len=1.1, x=1.1, tickformat=".2f")), row=1, col=1)
    frames = []
    num_coletas = data.shape[2]
    for fValue in range(1,num_coletas,1):
        frame_data = data[:, :, fValue]
        frames.append(go.Frame(data=[go.Heatmap(z=frame_data,x=rótulos_x,y=rótulos_y,colorscale='Blues')]))
    fig.update(frames=frames)
    fig.update_layout(
        width=600,height=400,title={'text': nome,'y': 0.9,'x': 0.5,'xanchor': 'center','yanchor': 'top'},
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="gray", yaxis2=dict(showticklabels=False), yaxis3=dict(showticklabels=False),
        updatemenus=[{"buttons": [{"args": [None, {"frame": {"duration": 200, "redraw": True}, "fromcurrent": True}], "label": "Play", "method": "animate"},
            {"args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}], "label": "Pause", "method": "animate"}], "direction": "left", "pad": {"r": 10, "t": 87}, "showactive": False, "type": "buttons", "x": 0.1, "xanchor": "right", "y": 0, "yanchor": "top"}])
    return fig

def basicPlot3D_animado(data, rx, tx, rangeMax, nome,ylab=""):
    rótulos_x = [f'R{i:02}' for i in range(1, rx+1)]
    rótulos_y = [f'T{i:02}' for i in range(1, tx+1)]
    z_data = data[:, :, 0]
    fig = go.Figure(
        data=[go.Surface(
            z=z_data, x=np.arange(rx), y=np.arange(tx), colorscale='Blues', cmin=0, cmax=rangeMax, colorbar=dict(title="", thickness=10, len=1.1, x=1.1, tickformat=".2f"))],
        frames=[
            go.Frame(data=[go.Surface(z=data[:, :, i], x=np.arange(rx), y=np.arange(tx), colorscale='Blues', cmin=0, cmax=rangeMax)]) for i in range(0, data.shape[2], 1)
        ])
    fig.update_layout(
        width=700,height=425,
        title={'text': nome,'y': 0.9,'x': 0.5,'xanchor': 'center','yanchor': 'top'}, scene=dict(
            xaxis=dict(title=dict(text='Rx'),tickvals=list(range(rx)),ticktext=rótulos_x),
            yaxis=dict(title=dict(text='Tx'),tickvals=list(range(tx)),ticktext=rótulos_y),
            zaxis=dict(title=dict(text=ylab),range=[0, rangeMax]),
            aspectratio=dict(x=1, y=1, z=0.6),
            camera=dict(eye=dict(x=1.5, y=1.5, z=0.8)),
        ),
        margin=dict(l=0, r=80, t=50, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="gray",
        updatemenus=[{
            "buttons": [
                {"args": [None, {"frame": {"duration": 100, "redraw": True}, "fromcurrent": True}],"label": "Play","method": "animate"},
                {"args": [[None], {"frame": {"duration": 0, "redraw": True},"mode": "immediate","transition": {"duration": 0}}],"label": "Pause","method": "animate"}
            ],
            "direction": "left","pad": {"r": 10, "t": 87},"showactive": False,"type": "buttons","x": 0.1,"xanchor": "right","y": 0,"yanchor": "top"
        }]
    )
    return fig

def resolver_um(tx, rx, z, calPixel, teste1_val):
    try:
        coef = calPixel[tx, rx].copy()
        coef[-1] -= teste1_val
        raizes = np.roots(coef)
        raizes_reais = raizes[np.isreal(raizes)].real
        raizes_validas = raizes_reais[(raizes_reais >= 0) & (raizes_reais <= 2200)]
    except Exception as e:
        st.write('Erro no resolver_um',e)
    return raizes_validas.max() if len(raizes_validas) > 0 else 2200

def analysisParameters(data, matrixCal, vhMax1):
    posAnalysis = {}
    for dataName in data:
        for thickDF in data[dataName]:
            coleta = np.abs(data[dataName][thickDF])
            coleta = np.transpose(coleta.values.reshape(coleta.shape[0]//16,16,16),(1,2,0))
            coleta = np.double(coleta)
            coleta = np.stack([np.mean(coleta[:, :, i:i+20], axis=2) for i in range(0, coleta.shape[2], 20) if i+20 <= coleta.shape[2]], axis=2)
            vhMax = np.mean(np.sort(coleta,axis=2)[:,:,-int(coleta.shape[2]*0.05):],axis=2)
            teste1 = np.zeros(coleta.shape)
            teste1 = np.abs(coleta) / np.abs(vhMax[:, :, np.newaxis])
            teste1[teste1 > 1] = 1
            teste1 = teste1[:13, :, :]
            x, y, z = teste1.shape
            resultados = Parallel(n_jobs=-1)(
                delayed(resolver_um)(tx, rx, zx, matrixCal, teste1[tx, rx, zx])
                for tx in range(x)
                for rx in range(y)
                for zx in range(z)
            )
            analysis = np.array(resultados).reshape(x, y, z)
            posAnalysis[thickDF] = np.stack([np.mean(np.transpose(analysis[:,:,:],(0,1,2))[:, :, i:i+5], axis=2) for i in range(0, np.transpose(analysis[:,:,:],(0,1,2)).shape[2], 5) if i+5 <= np.transpose(analysis[:,:,:],(0,1,2)).shape[2]], axis=2)
    return posAnalysis