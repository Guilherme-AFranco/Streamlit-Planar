from packs import *
from auxiliary_functions import *

# Cria a conecção com o banco de dados a partir da biblioteca sqlalchemy (facilita a interação com o DB - consultas complexas)
def SQLEngine():
    dotenv.load_dotenv()
    host=os.environ['MYSQL_HOST']
    user=os.environ['MYSQL_USER']
    password=os.environ['MYSQL_PASSWORD']
    database=os.environ['MYSQL_DATABASE']
    port=int(os.environ['MYSQL_PORT'])
    try:
        connection = f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'
        engine = create_engine(connection) # Engine de conexão
    except:
        st.write("O aplicativo Docker ainda está processando. Tente recarregar a página (F5).")
    return engine

# Cria a conecção com o banco de dados a partir da biblioteca pymysql (consultas simples)
def SQLConnection():
    dotenv.load_dotenv()

    connection = pymysql.connect(
        host=os.environ['MYSQL_HOST'],
        user=os.environ['MYSQL_USER'],
        password=os.environ['MYSQL_PASSWORD'],
        database=os.environ['MYSQL_DATABASE'],
    )
    return connection

# Encerrar o Streamlit e Docker
def closeStream():
    dotenv.load_dotenv()
    cont_ID=os.environ['MYSQL_ID']
    os.system(f'docker stop {cont_ID}')
    os._exit(0)

# Inserção de arquivos locais para o banco de dados
def insertFiles(filePath, Rx=None):
    connection = SQLConnection()
    list_dir = dirList(filePath)
    dict_dir = dirDict(list_dir, Rx)
    varList = []
    for elements in dict_dir:
        dfList = catchData(dict_dir[elements])
        varList.append(dfList)
    DBInsert(connection,dict_dir,varList)

# Exclusão de arquivos do banco de dados
def excludeFiles(filePath):
    connection = SQLConnection()
    table_name = filePath
    with connection:
        with connection.cursor() as cursor:
            sql = (
                f'DROP TABLE {table_name}'
            )
            cursor.execute(sql)
        connection.commit()

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
    query = f'SELECT * FROM {vhName[0]}'
    vh1 = {f"{vhName[0]}": pd.read_sql(query, con=engine)}
    query = f'SELECT * FROM {vhName[1]}'
    vh2 = {f"{vhName[1]}": pd.read_sql(query, con=engine)}
    vh1[vhName[0]] = np.abs(vh1[vhName[0]][[col for col in vh1[vhName[0]].columns if col.startswith('Rx')]])
    vh2[vhName[1]] = np.abs(vh2[vhName[1]][[col for col in vh2[vhName[1]].columns if col.startswith('Rx')]])
    rx = len(vh1[vhName[0]].keys())
    vhMax = (vh1[vhName[0]] + vh2[vhName[1]])/2
    vhMax = np.transpose(vhMax.values.reshape(int(len(vhMax)/rx),rx,16),(1,2,0))
    conv = 2 / (2**rx - 1)
    vhMax = np.double(np.mean(vhMax, axis=2))
    return vhMax,conv,rx

# Coleta do valor de saturação da fase gasosa
def vlData(vlName):
    engine = SQLEngine()
    query = f'SELECT * FROM {vlName[0]}'
    vl = {f"{vlName[0]}": pd.read_sql(query, con=engine)}
    vl[vlName[0]] = np.abs(vl[vlName[0]][[col for col in vl[vlName[0]].columns if col.startswith('Rx')]])
    vlMax = np.double(np.mean(vl[vlName[0]], axis=2))
    return vlMax

# Insere os coeficientes de calibração no banco de dados
def insertMatrix(calPixel, matrixName):
    connection = SQLConnection()
    coefs = ["a","b","c","d","e"]
    placeholders = ", ".join(["%s"] * len(calPixel[0,:,0]))
    with connection:
        rxColumns = ", ".join([f"Rx{i+1:02} DOUBLE" for i in range(len(calPixel[0,:,0]))])
        for idx, coef in enumerate(coefs):
            table_name = f'{matrixName}_{coefs[idx]}'
            with connection.cursor() as cursor:
                sql = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INT AUTO_INCREMENT PRIMARY KEY, 
                        {rxColumns}
                    )
                """
                cursor.execute(sql)
            connection.commit()
        rxColumns = ", ".join([f"Rx{i+1:02}" for i in range(len(calPixel[0, :, 0]))])
        for idx, coef in enumerate(coefs):
            table_name = f'{matrixName}_{coef}'
            data_list = [
                tuple(calPixel[TxIdx, :, idx]) for TxIdx in range(len(calPixel[:, 0, idx]))
            ]
            with connection.cursor() as cursor:
                sql = f"INSERT INTO {table_name} ({rxColumns}) VALUES ({placeholders})"
                cursor.executemany(sql, data_list)
            connection.commit()

# Coleta dos dados dos coeficientes das curvas de calibração do banco de dados
def importCal(data):
    engine = SQLEngine()
    matrix = {}
    for value in data:
        query = f'SELECT * FROM {value}'
        matrix[value] = pd.read_sql(query, con=engine)
        rxValues = [col for col in matrix[value].columns if col.startswith('Rx')]
        txValues = [f'Tx{i+1:02d}' for i in range(13)]
        matrix[value] = matrix[value][rxValues]
    return matrix, rxValues, txValues