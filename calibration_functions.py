from packs import *
from db_functions import *

# Análise de dados para geração ds curvas de calibração e obtenção dos parâmetros de média e minimo da calibração.
def calibGenerator(thickName,vhName,tx,rx=None,extraAnalisys=None):
    for value in thickName:
        if not rx:
            rx = len(thickName[value])
        if rx != len(thickName[value]):
            st.write("Arquivos de calibração de diferentes tamanhos.")
            return
    thick = importData(thickName)
    vhMax, conv, vhRx = vhData(vhName)
    if rx != vhRx:
        st.write("Arquivos de calibração com Rx diferente do VH.")
        return
    minRx, meanRc = getParameters(thick, vhMax, conv, rx, tx)
    if extraAnalisys == 'Poly':
        calPixel, thickValue, voltage = calCurve1(minRx,tx,rx)
        return calPixel, thickValue, voltage
    else:
        return minRx, meanRc, thick
    
# Criação dos dados para média simples e média calibrada para as análises.
def analysisGenerator(analysisName, vhName, matrixName, tx):
    vhMax, conv, rx = vhData(vhName)
    analysis = importData(analysisName)
    matrixCal, rxValues = importCal(matrixName)
    for key in analysisName.keys():
        for value in analysisName[key]:
            if not analysis[key][value].shape[1] == rx:
                st.write('As amostras escolhidas não possuem o mesmo número de canais Rx que o VH.')
                return
            if not analysis[key][value].shape[1] == len(rxValues):
                st.write('As amostras escolhidas não possuem o mesmo número de canais Rx que o polinômio.')
                return
    fitAnalysis, meanRc = analysisParameters(analysis, matrixCal, matrixName, vhMax, rx, tx, conv)
    return analysis, fitAnalysis, meanRc, rx