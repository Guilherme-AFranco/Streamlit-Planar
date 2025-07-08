from packs import *
from db_functions import *

# Análise de dados para geração ds curvas de calibração e obtenção dos parâmetros de média e minimo da calibração.
def calibGenerator(thickName,vhName,tx,rx=None,extraAnalisys=None,type=None):
    thick = importData(thickName)
    vhMax, conv, vhRx = vhData(vhName)
    # if rx != vhRx:
    if rx and rx != vhRx:
        st.write("Arquivos de calibração com Rx diferente do VH.")
        return
    minRx, data = getParameters(thick, vhMax, vhRx, tx, type)
    if extraAnalisys == 'Poly':
        calPixel, Volt, thick, pix = calCurve1(minRx, tx, vhRx)
        return calPixel, Volt, thick, pix
    else:
        return minRx, data, conv
    
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