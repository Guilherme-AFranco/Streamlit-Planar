# Dashboard - Sensor Planar
## Laboratório de Escoamento Multifásico Industrial - LEMI-USP

### Desempenho Computacional Recomendado
- Windows 10 ou superior;
- 8 gb de memória RAM;
- Intel Core i3 ou superior;

### Instalação e configuração de softwares

**Python**
- Para instalação do pacote Python, entrar no site oficial do [Python](https://www.python.org/downloads/windows/) e realizar a instalação. Quando instalar, selecione "Add python.exe to PATH" no instalador.

**VSCode**
- Para instalação do software, entrar no site oficial do [Visual Studio](https://code.visualstudio.com/) e seguir o procedimento de instalação descrito.
- Após a instalação, abra o PowerShell no Windows (como administrador) e execute o comando "Set-ExecutionPolicy AllSigned -Force" para que possa ser usado o ambiente virtual dentro do VSCode.
- Inicie o VSCode, na aba esquerda, abra as configurações.
- Com as configurações abertas, no canto superior esquerdo aparecerá um item selecionavel "Open Settiongs (JSON)". Aba-o.
- (Opcional) Na aba esquerda do VSCode, encontre o icone "Extensions" e selecione-o. Dentro da aba, instale as extensões abaxo:
  - Code Runner;
  - Material Icon Theme;
  - Om Theme;
  - Pylance;
  - Python;
  - Python Debugger.
- (Opcional) Copie o código `JSON_config.txt` e cole no JSON que está aberto. Esta é apenas uma configuração de setup do VSCode.

**Git**
- Faça a instalação do Git a partir do site oficial [Git](https://git-scm.com/downloads) seguindo as recomendações descritas.

**Clonagem dos arquivos do Github para o VSCode**
- Dentro do VSCode, abra uma pasta onde deseja realizar a cópia dos arquivos do GitHub.
- Abra o terminal novamente e faça a clonagem dos arquivos do Github com o comando "git clone https://github.com/Guilherme-AFranco/Streamlit-Planar.git" (apenas para o primeiro uso)
- (Opcional) Caso queira sincronizar as possíveis alterações que você venha a realizar dentro do seu GitHub, crie uma pasta no GitHub para alocar os arquivos do Dashboard.
- (Opcional) Dentro desta pasta do GitHub, copie o HTTPS que está na caixa verde escrita "<> Code".
- (Opcional) Dentro do VSCode, faça login com suas credenciais do Github a partir dos códigos abaixo dentro do terminal:
  - git config --global user.name "nome_de_usuario"
  - git config --global user.email "email@dominio.com"
- (Opcional) Abra agora o item "Source Control (Ctrl+Shift+G)" no VSCode (que está no painel da esquerda).
- (Opcional) Clique em "Initialize Repository" e então nas opcões adicionais que apareceu dentro do painel lateral esquerdo, escolha "Show Git Output" -> Terminal.
- (Opcional) Inclua o código "git remote add origin URL_Copiada" onde "URL_Copiada" é o url que você copiou dentro do GitHub (isso é feito apenas uma vez).
- (Opcional) Sempre que tiver alguma alteração nos códigos dentro do VSCode, você deverá fazer o Commit na aba "Source Control" para que a atualização seja realizada dentro do GitHub também.

**Docker Desktop**
- Instale o Docker a partir do site oficial [Docker Desktop](https://www.docker.com/products/docker-desktop/) e siga os passos recomendados.
- Sempre que utilizar o Dashboard, será necessário deixar o Docker aberto no desktop.

**Criação e uso do ambiente virtual**
- Abra o VSCode e entre na pasta onde estão os arquivos do Dashboard.
- No canto superior direito da tela haverá uma opção "Toggle Panel (Ctrl + J)". Abra-o.
- Dentro do terminal que será aberto, digite "python -m venv venv" para criação do seu ambiente virtual na pasta em que estiver selecionada (faça isso apenas no primeiro acesso)
- Acesse-o utilizando o comando "\venv\Scripts\activate" e digite r para permitir (faça isso sempre que abrir o VSCode).
- Instale o arquivo `requirements.txt` dentro do seu ambiente virtual a partir do comando "pip install -r .\requirements.txt" (faça isso apenas no primeiro acesso).

### Criação do Container (Realizar apenas uma vez)
- Abra o VSCode
- Antes de criar o Container, é necessário abrir o arquivo `docker-compose.yml` e alterar o diretório para aquele que você deseja que fique salvo o Container dentro do desktop.
- Utilize o arquivo `.env-example` para criar os dados de login do usuário que voce deseja. Para isso, copie o conteúdo deste arquivo e crie um novo arquivo com o nome `.env`, onde você incluirá estes dados copiados e alterará para os dados que deseja.
- No terminal, execute "docker-compose up -d" para criação do Container que será utilizado.
- Para isso, é necessário que o arquivo `docker-compose.yml` esteja na pasta em que se está com o terminal aberto.
- Após a criação do banco de dados, digite o comando "docker ps" dentro do terminal para visualizar o CONTAINER ID. Copie-o, inclua-o em MYSQL_ID dentro do arquivo `.env` e descomente esta linha específica.

### Atalho para abertura do Dashboard
- Na sua área de trabalho, crie um atalho.
- Digite o caminho "powershell.exe -ExecutionPolicy Bypass -File "C:\caminho\para\Iniciar_streamlit.ps1"" e inclua o diretório onde se encontra o arquivo `Iniciar_streamlit.ps1`. Clique em avançar.
- Adicione o nome que desejar para o atalho (por exemplo, "Abertura Streamlit").
- Altere as primeiras 6 linhas do arquivo `Iniciar_streamlit.ps1` para seu uso específico.

### Abertura do Dashboard

**Opção 1**
- Abra o atalho criado na sua área de trabalho e siga as instruções descritas nele.

**Opção 2**
- Com toda a configuração realizada, basta abrir o terminal na pasta onde os arquivos estão alocados e digitar o comando "streamlit run Planar.py".
- Note que Planar.py pode estar com nomes semelhantes a depender da versão final que foi criada. Até o momento estou utilizando a versão `Planar-v4.py`, então o código usado seria "streamlit run Planar-v4.py".

### Licença
Este projeto está licenciado sob a licença MIT. Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
