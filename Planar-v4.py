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
        analysisType = st.radio("Inclusão de arquivos para:", ("Análise", "Calibração"),horizontal=True)
        if analysisType == "Calibração":
            Rx = st.number_input("Digite o número de canais Rx usado no sensor planar:", step=1, value=0)
        folderPath = st.text_input("Digite o caminho para inserir os arquivos (ex.: E:\\Planar\\Calib):")
        if st.button('Incluir arquivos') and folderPath:
            try:
                statusMessage = st.empty()
                statusMessage.write("Realizando inclusão dos arquivos selecionados...")
                if analysisType=="Calibração":
                    insertFiles(folderPath, Rx)
                else:
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
    Obs. 1: Os nomes dos arquivos de calibração a incluir devem ser no formato \'XXXu-YY\'. \n
    Onde XXX é a espessura do cilindro de calibração (400, 520, ...) e YY é a coleta realizada (00, 01, 02, 03, ...). \n
    Obs. 2: Para inclusão de arquivos de calibração, é necessário a inclusão da quantidade de arquivos referente à quantidade de canais de recepção (Rx) do projeto. \n
    Isso se deve à necessidade de obter uma curva de calibração para cada canal (ou seja, cada arquivo refere-se ao teste onde o cilindro está posicionado na faixa de recepção.
    ''')

# PÁGINA 2
elif page == "⚙️ Gerador de matriz de calibração":
    col1 = st.columns(3)
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
        selectedVh = st.selectbox('Selecione o VH coletado.', vhFilter)
        tx = st.number_input("Digite o valor de Tx usado no sensor planar:", step=1, value=0)
    if 'calPixel' not in st.session_state:
        st.session_state.calPixel = st.session_state.matrix1Fig = None
    if st.button('Gerar Matriz'):
        if thicknessSelect and selectedVh and tx!=0:
            statusMessage = st.empty()
            statusMessage.write("Gerando matriz de calibração...")
            try:
                st.session_state.calPixel, thickValue, voltage = calibGenerator(filteredThickness, selectedVh, tx, extraAnalisys='Poly')
                statusMessage.empty()
                st.write("Curvas de calibração geradas")
            except:
                st.write("Erro na geração de calibração, verifique se os dados estão corretos.")
            st.session_state.matrix1Fig = plotCalib(thickValue, voltage)
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
    if "rxSelected" not in st.session_state and "rxValues" not in st.session_state:
        st.session_state.rxValues = st.session_state.rxSelected = None
    if st.button("Analise"):
        calFiltered = df[df['Tables_in_base_de_dados'].str.startswith(matrixThickness)]['Tables_in_base_de_dados'].tolist()
        try:
            matrixCal, st.session_state.rxValues = importCal(calFiltered)
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
            with col5[1]:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(f"Gerar curva"):
                    st.session_state.rxSelected = rxSelected+1
                    st.experimental_rerun()
            with col5[2]:
                if st.button(f"Mostrar todas as curvas"):
                    st.session_state.rxSelected = None
                    st.experimental_rerun()
        with col4[1]:
            thickValue, voltage = calCurve2(st.session_state.matrixCal)
            if st.session_state.rxSelected:
                matrix2Fig = plotCalib(thickValue, voltage[:,st.session_state.rxSelected-1,:],st.session_state.rxSelected)
            else:
                matrix2Fig = plotCalib(thickValue, voltage)
            st.session_state.matrix2Fig = matrix2Fig
            st.plotly_chart(st.session_state.matrix2Fig, use_container_width=True)
            if 'matrixCal' in st.session_state and st.session_state.rxSelected:
                st.write('Equação da curva:')
                matrixFilteredNames = [value for value in matrixNames if value.startswith(matrixThickness)]
                rxName = [f'Rx{st.session_state.rxSelected:02d}']
                st.write(f'f(x) = {st.session_state.matrixCal[matrixFilteredNames[4]][rxName].mean().values[0]:.2e}.x^4+{st.session_state.matrixCal[matrixFilteredNames[3]][rxName].mean().values[0]:.2e}.x^3+{st.session_state.matrixCal[matrixFilteredNames[2]][rxName].mean().values[0]:.2e}.x^2+{st.session_state.matrixCal[matrixFilteredNames[1]][rxName].mean().values[0]:.2e}.x+{st.session_state.matrixCal[matrixFilteredNames[0]][rxName].mean().values[0]:.2e}')
                st.write('Onde:')
                st.write('x: espessura de filme; f(x): tensão.')

# PÁGINA 3
elif page == "🔍 Análise dos dados adquiridos":
    st.write("A análise dessa seção será realizada sem a presença do ajuste pelo polinômio de calibração.")
    cols = st.columns(4)
    names = df[df['Tables_in_base_de_dados'].str.contains(r'^\d')]['Tables_in_base_de_dados']
    with cols[0]:
        filteredThickness = {}
        thicknessSelect = [st.selectbox('Selecione a coleta de análise', names.apply(lambda x: valueExtract(x)).unique().tolist())]
        try:
            for value in thicknessSelect:
                filteredThickness[value] = df[df['Tables_in_base_de_dados'].apply(lambda x: x.startswith(value))]['Tables_in_base_de_dados'].tolist()
        except:
            st.write("Verifique se há arquivos para análise")
    vhNames = df[df['Tables_in_base_de_dados'].str.startswith('VH')]['Tables_in_base_de_dados']
    with cols[1]:
        selectedVh = st.selectbox('Selecione o VH', vhNames)
    with cols[2]:
        tx = st.number_input("Digite o valor de Tx usado no sensor planar:", step=1, value=0)
    with cols[3]:
        rx = st.number_input("Digite o número de canais Rx usado no sensor planar:", step=1, value=0)
    if st.button('Gerar gráficos'):
        if thicknessSelect and selectedVh and tx!=0 and rx!=0:
            statusMessage = st.empty()
            statusMessage.write("Gerando gráficos...")
            try:
                minRx, meanRc, thick = calibGenerator(filteredThickness, selectedVh, tx)
            except:
                st.write("Erro na análise, verifique se a espessura, VH e valor de tx estão coerentes.")
            statusMessage.empty()
            for _ in range(len(minRx.keys())):
                fig = basicPlot(thick[next(iter(thick))],minRx[next(iter(minRx))],meanRc[next(iter(meanRc))],rx,tx,type='min')
                st.plotly_chart(fig)
        else:
            st.write("Erro: Arquivos não selecionados.")

# PÁGINA 4
elif page == "📈 Análise em função do polinômio":
    names = df['Tables_in_base_de_dados']
    vhNames = df[df['Tables_in_base_de_dados'].str.startswith('VH')]['Tables_in_base_de_dados']
    matrixNames = df[df['Tables_in_base_de_dados'].str.startswith('Matriz')]['Tables_in_base_de_dados']
    cols = st.columns(3)
    filteredAnalysis = {}
    with cols[0]:
        generalName = st.selectbox('Selecione o nome geral da análise', names.apply(lambda x: valueExtract(x,"regex")).unique().tolist())
        filteredName = names[names.str.startswith(generalName)]
        filteredAnalysis[generalName] = st.multiselect(f'Selecione o(s) arquivo(s) da série "{generalName}"', filteredName.tolist())
    with cols[1]:
        matrixSelected = st.selectbox('Selecione a matriz de calibração', matrixNames.apply(lambda x: valueExtract(x,'matrix')).unique().tolist())
        vhFiltered = st.selectbox('Selecione o VH', vhNames)
    with cols[2]:
        tx = st.number_input("Digite o valor de Tx usado no sensor planar:", step=1, value=0)
    try:
        matrixFiltered = df[df['Tables_in_base_de_dados'].str.startswith(matrixSelected)]['Tables_in_base_de_dados'].tolist() # Obtendo todos os arquivos da espessura selecionada
    except:
        st.write("Verifique se há arquivos para análise")
    if 'analysis' not in st.session_state:
        st.session_state.analysis = st.session_state.fitAnalysis = st.session_state.meanRc = st.session_state.rx = None
    if st.button('Gerar análise'):
        if filteredAnalysis and vhFiltered and matrixFiltered:
            st.write("Gerando análise...")
            try:
                st.session_state.analysis,st.session_state.fitAnalysis, st.session_state.meanRc, st.session_state.rx = analysisGenerator(filteredAnalysis,vhFiltered,matrixFiltered,tx)
            except Exception as e:
                st.write("Erro na análise, verifique se as variáveis inclusas acima estão corretas.",e)
            st.write("Análise gerada")
        else:
            st.write("Selecione todas as caixas de seleção.")
    if st.session_state.analysis is not None and st.button("Gerar gráficos"):
        if st.session_state.analysis and not st.session_state.fitAnalysis.empty and not st.session_state.meanRc.empty and st.session_state.rx:
            try:
                for value in st.session_state.meanRc:
                    fig = basicPlot(st.session_state.analysis[next(iter(st.session_state.analysis))][value],st.session_state.fitAnalysis[value],st.session_state.meanRc[value],st.session_state.rx,tx,type='fit')
                    st.plotly_chart(fig)
            except:
                st.write("Erro na plotagem, verifique se a análise é coerente.")