from packs import *
from auxiliary_functions import *
from calibration_functions import *

st.set_page_config(
    page_title='DASHBOARD - Sensor Planar',
    page_icon='💲',
    layout='wide',
    initial_sidebar_state='expanded',
    menu_items={
        'Get Help': 'https://br.linkedin.com/in/guilherme-aparecido',
        'Report a bug': "https://br.linkedin.com/in/guilherme-aparecido",
        'About': "App desenvolvido para inspeção do sensor planar."
    }
)

engine = SQLEngine()

sql = 'SHOW TABLES'
statusMessage = st.empty()
while True:
    try:
        df = pd.read_sql(sql, con=engine)
        break
    except Exception as e:
        statusMessage.write(f"O aplicativo Docker ainda está processando. Tentando novamente em 5 segundos... {e}")
        time.sleep(4)
        statusMessage.empty()
        time.sleep(1)
with st.sidebar:
    logo = Image.open('./Imagens/Lemi-Logo.png')
    st.image(logo, width=300)
    st.subheader('Navegação - Planar')
    st.markdown("---")
    page = st.radio(
        "Selecione a função desejada:", 
        (
            "📂 Inclusão/Exclusão de arquivos", 
            "⚙️ Gerador de matriz de calibração", 
            "🔍 Análise dos dados adquiridos", 
            "📈 Análise em função do polinômio"
        )
    )
    st.sidebar.markdown("---")
    if st.sidebar.button('Exit'):
        st.write("Aplicativo está sendo fechado...")
        closeStream()

# PÁGINA 1
if page == "📂 Inclusão/Exclusão de arquivos":
    cols = st.columns(3)
    with cols[0]:
        folderPath = st.text_input("Digite o caminho para inserir os arquivos (ex.: E:\\Planar\\Calib):")
        if st.button('Incluir arquivos') and folderPath:
            try:
                statusMessage = st.empty()
                statusMessage.write("Realizando inclusão dos arquivos selecionados...")
                insertFiles(folderPath)
                statusMessage.empty()
                st.write("Arquivos carregados corretamente.")
            except:
                st.write("Ocorreu um erro na importação. Verifique se os dados estão no formato correto.")
    with cols[1]:
        df['Arquivos alocados'] = df['Tables_in_base_de_dados']
        deletFile = st.multiselect('Selecione os arquivos para exclusão (essa exclusão é irreversível).', df['Arquivos alocados'])        
        if st.button('Excluir arquivos') and deletFile:
            statusMessage = st.empty()
            statusMessage.write("Realizando exclusão do(s) arquivo(s) selecionado(s)...")
            for arquivo in deletFile:
                excludeFiles(arquivo)
            statusMessage.empty()
            st.write("Exclusão concluída")
        else:
            st.write("Nenhum arquivo selecionado.")
    with cols[2]:
        st.write(df['Arquivos alocados'])
    st.write('''
    Obs. 1: Os nomes dos arquivos de calibração a incluir devem ser no formato \'XXXXu-YY\'. \n
    Onde XXXX é a espessura do cilindro de calibração (0400, 0520, ...) e YY é a coleta da faixa realizada (00, 01, 02, 03, ...) para o caso de calibração por faixas, ou amostra realizada (a1, a2, ...) para a calibração por deslizamento dos cilíndros. \n
    ''')
    # Obs. 2: Para inclusão de arquivos de calibração por faixa, é necessário a inclusão da quantidade de arquivos referente à quantidade de canais de recepção (Rx) do projeto. \n
    # Isso se deve à necessidade de obter uma curva de calibração para cada canal (ou seja, cada arquivo refere-se ao teste onde o cilindro está posicionado na faixa de recepção.

# PÁGINA 2
elif page == "⚙️ Gerador de matriz de calibração":
    col1 = st.columns(3)
    selectedVh = []
    with col1[0]:
        thicknessFilter = df[df['Tables_in_base_de_dados'].str.contains(r'^\d')]['Tables_in_base_de_dados']
        thicknessSelect = st.multiselect('Selecione a(s) espessura(s) de cilindros usados para calibração.', thicknessFilter.apply(lambda x: valueExtract(x)).unique().tolist())
    filteredThickness = {}
    try:
        for value in thicknessSelect:
            filteredThickness[value] = df[df['Tables_in_base_de_dados'].apply(lambda x: x.startswith(value))]['Tables_in_base_de_dados'].tolist()
    except:
        st.write("Verifique se há arquivos para análise.")
    with col1[1]:
        vhFilter = df[df['Tables_in_base_de_dados'].str.startswith('VH')]['Tables_in_base_de_dados']
        selectedVh.append(st.selectbox('Selecione o VH inicial coletado.', vhFilter))
        selectedVh.append(st.selectbox('Selecione o VH final coletado.', vhFilter))
    with col1[2]:
        analise = st.selectbox('Selecione o tipo de análise a realizar.', ['Faixas', 'Amostras'])
        tx = st.number_input("Digite o valor de Tx usado no sensor planar:", step=1, value=0)
    if 'calPixel' not in st.session_state:
        st.session_state.calPixel = st.session_state.matrix1Fig = None
    if st.button('Gerar Matriz'):
        if thicknessSelect and selectedVh and tx!=0:
            statusMessage = st.empty()
            statusMessage.write("Gerando matriz de calibração...")
            try:
                st.session_state.calPixel, voltage, thickValue, pixelValue = calibGenerator(filteredThickness, selectedVh, tx, extraAnalisys='Poly', type=analise)
                statusMessage.empty()
                st.write("Curvas de calibração geradas")
            except Exception as e:
                st.write("Erro na geração de calibração, verifique se os dados estão corretos.", e)
            st.session_state.matrix1Fig = plotCalib(st.session_state.calPixel)
        else:
            st.write("Coeficientes inválidos / não selecionados.")
    if st.session_state.matrix1Fig:
        col2 = st.columns(2)
        with col2[0]:
            st.plotly_chart(st.session_state.matrix1Fig, use_container_width=True)
        with col2[1]:
            with st.form(key='save_form'):
                calName = st.text_input("Nome do arquivo de calibração (ex.: Matriz_calibXX)")
                submit = st.form_submit_button(label='Salvar equação no banco de dados')
                if submit and calName:
                    statusMessage = st.empty()
                    statusMessage.write("Incluindo matriz no banco de dados...")
                    try:
                        insertMatrix(st.session_state.calPixel, calName)
                        statusMessage.empty()
                        st.write("Matriz incluida.")
                    except:
                        st.write("Nome incluso incorretamente.")
    else:
        st.write("Gere as curvas antes.")
    col3 = st.columns(3)
    with col3[0]:
        matrixNames = df[df['Tables_in_base_de_dados'].str.startswith('Matriz')]['Tables_in_base_de_dados'].reset_index(drop=True)
        matrixThickness = st.selectbox('Selecione a matriz de calibração', matrixNames.apply(lambda x: valueExtract(x,"matrix")).unique().tolist())

    if 'curves' not in st.session_state:
        st.session_state.curves = False
    if 'rxSelected' not in st.session_state:
        st.session_state.rxSelected = None
    if 'txSelected' not in st.session_state:
        st.session_state.txSelected = None
    if st.button("Analise"):
        calFiltered = df[df['Tables_in_base_de_dados'].str.startswith(matrixThickness)]['Tables_in_base_de_dados'].tolist()
        try:
            matrixCal, rxValues, txValues = importCal(calFiltered)
            st.session_state.txValues = txValues
            st.session_state.rxValues = rxValues
            st.session_state.matrixCal = matrixCal
        except:
            st.write("Erro na análise da matriz.")
        st.session_state.curves = True
    if st.session_state.curves:
        if st.session_state.rxSelected:
            planar = Image.open(f'./Imagens/Rx{st.session_state.rxSelected:02d}.png')
        else:
            planar = Image.open(f'./Imagens/Sensor_Planar.jpg')
        col4 = st.columns(2)
        with col4[0]:
            st.write('Faixa de seleção da curva de calibração')
            st.markdown("<br>", unsafe_allow_html=True)
            st.image(planar)
            col5 = st.columns(4)
            with col5[0]:
                rx_option = st.selectbox("Selecione um canal Rx:", st.session_state.rxValues)
                rxSelected = st.session_state.rxValues.index(rx_option)
                tx_option = st.selectbox("Selecione um canal Tx:", st.session_state.txValues)
                txSelected = st.session_state.txValues.index(tx_option)
            with col5[1]:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"Gerar curvas par Tx-Rx"):
                    st.session_state.rxSelected = rxSelected+1
                    st.session_state.txSelected = txSelected+1
                    st.experimental_rerun()
                if st.button(f"Gerar curvas Rx"):
                    st.session_state.rxSelected = rxSelected+1
                    st.experimental_rerun()
                if st.button(f"Gerar curvas Tx"):
                    st.session_state.txSelected = txSelected+1
                    st.experimental_rerun()
            with col5[2]:
                if st.button(f"Mostrar todas as curvas Rx"):
                    st.session_state.rxSelected = None
                    st.experimental_rerun()
                if st.button(f"Mostrar todas as curvas Tx"):
                    st.session_state.txSelected = None
                    st.experimental_rerun()
        with col4[1]:
            # thickValue, voltage = calCurve2(st.session_state.matrixCal)
            fit = calCurve2(st.session_state.matrixCal)
            if st.session_state.rxSelected and not st.session_state.txSelected:
                # matrix2Fig = plotCalib(thickValue, voltage[:,st.session_state.rxSelected-1,:],st.session_state.rxSelected)
                # matrix2Fig = plotCalib(thickValue[:,st.session_state.rxSelected-1,:], voltage,st.session_state.rxSelected)
                matrix2Fig = plotCalib(fit[:,st.session_state.rxSelected,:],rx=st.session_state.rxSelected)
            elif st.session_state.txSelected and not st.session_state.rxSelected:
                matrix2Fig = plotCalib(fit[st.session_state.txSelected,:,:],tx=st.session_state.txSelected)
            elif st.session_state.rxSelected and st.session_state.txSelected:
                matrix2Fig = plotCalib(fit[st.session_state.txSelected,st.session_state.rxSelected,:],rx=st.session_state.rxSelected, tx=st.session_state.txSelected)
            else:
                # matrix2Fig = plotCalib(thickValue, voltage)
                matrix2Fig = plotCalib(fit)
            st.session_state.matrix2Fig = matrix2Fig
            st.plotly_chart(st.session_state.matrix2Fig, use_container_width=True)
            if 'matrixCal' in st.session_state and st.session_state.rxSelected and st.session_state.txSelected:
                st.write('Equação da curva:')
                matrixFilteredNames = [value for value in matrixNames if value.startswith(matrixThickness)]
                rxName = f'Rx{st.session_state.rxSelected:02d}'
                txName = st.session_state.txSelected
                st.write(f'δ = {st.session_state.matrixCal[matrixFilteredNames[4]][rxName][txName].mean():.2e}.U_dl^4+{st.session_state.matrixCal[matrixFilteredNames[3]][rxName][txName].mean():.2e}.U_dl^3+{st.session_state.matrixCal[matrixFilteredNames[2]][rxName][txName].mean():.2e}.U_dl^2+{st.session_state.matrixCal[matrixFilteredNames[1]][rxName][txName].mean():.2e}.U_dl+{st.session_state.matrixCal[matrixFilteredNames[0]][rxName][txName].mean():.2e}')
                st.write('Onde:')
                # st.write('x: espessura de filme; f(x): tensão.')
                st.write('U_dl: tensão adimensional; δ: espessura de filme.')
                st.write(f'Linha de transmissão: Tx{txName:02d}')
                st.write(f'Linha de recepção: {rxName}')
                # st.latex(r'x\text{: tensão; }\delta\text{: espessura de filme}')

# PÁGINA 3
elif page == "🔍 Análise dos dados adquiridos":
    st.write("A análise dessa seção será realizada sem a presença do ajuste pelo polinômio de calibração.")
    cols = st.columns(4)
    names = df[df['Tables_in_base_de_dados'].str.contains(r'^\d')]['Tables_in_base_de_dados']
    with cols[0]:
        filteredThickness = {}
        thicknessSelect = [st.selectbox('Selecione a coleta de análise', names.apply(lambda x: valueExtract(x)).unique().tolist())]
        analysisType = st.radio("Análise de arquivos para:", ("Calibração por faixas", "Calibração por deslizamento", "Amostra"))
        try:
            for value in thicknessSelect:
                filteredThickness[value] = df[df['Tables_in_base_de_dados'].apply(lambda x: x.startswith(value))]['Tables_in_base_de_dados'].tolist()
        except:
            st.write("Verifique se há arquivos para análise")
    vhNames = df[df['Tables_in_base_de_dados'].str.startswith('VH')]['Tables_in_base_de_dados']
    with cols[1]:
        selectedVh = []
        selectedVh.append(st.selectbox('Selecione o VH inicial', vhNames))
        selectedVh.append(st.selectbox('Selecione o VH final', vhNames))
    with cols[2]:
        tx = st.number_input("Digite o valor de Tx usado no sensor planar:", step=1, value=0)
    with cols[3]:
        rx = st.number_input("Digite o número de canais Rx usado no sensor planar:", step=1, value=0)
    if st.button('Gerar gráficos'):
        if thicknessSelect and selectedVh and tx!=0 and rx!=0:
            statusMessage = st.empty()
            statusMessage.write("Gerando gráficos...")
            try:
                if analysisType == "Calibração por faixas":
                    minRx, thick, conv = calibGenerator(filteredThickness, selectedVh, tx, type='Faixas')
                elif analysisType == "Calibração por deslizamento":
                    minRx, thick, conv = calibGenerator(filteredThickness, selectedVh, tx, type='Amostras')
                else:
                    minRx, thick, conv = calibGenerator(filteredThickness, selectedVh, tx, type='Analise')
            except:
                st.write("Erro na análise, verifique se a espessura, VH e valor de tx estão coerentes.")
            statusMessage.empty()
            cols = st.columns(2)
            for value in thick[next(iter(thick))].keys():
                fig1 = basicPlot(thick[next(iter(thick))][next(iter(thick[next(iter(thick))]))]*conv,rx,f'Dados pré-processados: {value}',"Tensão (V)")
                fig2 = basicPlot3D_animado(thick[next(iter(thick))][next(iter(thick[next(iter(thick))]))]*conv,rx,tx,(thick[next(iter(thick))][next(iter(thick[next(iter(thick))]))]*conv).max(),f'Dados pré-processados: {value}',"Tensão (V)")
                with cols[0]:
                    st.plotly_chart(fig1)
                with cols[1]:
                    st.plotly_chart(fig2)
        else:
            st.write("Erro: Arquivos não selecionados.")

# PÁGINA 4
elif page == "📈 Análise em função do polinômio":
    names = df['Tables_in_base_de_dados']
    vhNames = df[df['Tables_in_base_de_dados'].str.startswith('VH')]['Tables_in_base_de_dados']
    matrixNames = df[df['Tables_in_base_de_dados'].str.startswith('Matriz')]['Tables_in_base_de_dados']
    cols = st.columns(3)
    filteredAnalysis = {}
    vhFiltered = []
    with cols[0]:
        generalName = st.selectbox('Selecione o nome geral da análise', names.apply(lambda x: valueExtract(x,"regex")).unique().tolist())
        filteredName = names[names.str.startswith(generalName)]
        filteredAnalysis[generalName] = st.multiselect(f'Selecione o(s) arquivo(s) da série "{generalName}"', filteredName.tolist())
    with cols[1]:
        matrixSelected = st.selectbox('Selecione a matriz de calibração', matrixNames.apply(lambda x: valueExtract(x,'matrix')).unique().tolist())
        tx = st.number_input("Digite o valor de Tx usado no sensor planar:", step=1, value=0)
    with cols[2]:
        vhFiltered.append(st.selectbox('Selecione o VH inicial', vhNames))
        vhFiltered.append(st.selectbox('Selecione o VH final', vhNames))
    try:
        matrixFiltered = df[df['Tables_in_base_de_dados'].str.startswith(matrixSelected)]['Tables_in_base_de_dados'].tolist() # Obtendo todos os arquivos da espessura selecionada
    except:
        st.write("Verifique se há arquivos para análise")
    if 'fitAnalysis' not in st.session_state:
        st.session_state.fitAnalysis = st.session_state.rxValues = None
    if st.button('Gerar análise'):
        if filteredAnalysis and vhFiltered and matrixFiltered:
            st.write("Gerando análise...")
            try:
                st.session_state.fitAnalysis, st.session_state.rxValues = analysisGenerator(filteredAnalysis,vhFiltered,matrixFiltered,tx)
            except Exception as e:
                st.write("Erro na análise, verifique se as variáveis inclusas acima estão corretas.",e)
            st.write("Análise gerada")
        else:
            st.write("Selecione todas as caixas de seleção.")
    cols = st.columns(2)
    if st.session_state.fitAnalysis is not None and st.button("Gerar gráficos"):
        if st.session_state.fitAnalysis and st.session_state.rxValues:
            try:
                for value in st.session_state.fitAnalysis:
                    fig1 = basicPlot(st.session_state.fitAnalysis[value],len(st.session_state.rxValues),value, "Espessura de filme")
                    fig2 = basicPlot3D_animado(st.session_state.fitAnalysis[value],len(st.session_state.rxValues),tx,2200,value, "Espessura de filme")
                    with cols[0]:
                        st.plotly_chart(fig1)
                    with cols[1]:
                        st.plotly_chart(fig2)
            except Exception as e:
                st.write("Erro na plotagem, verifique se a análise é coerente.",e)