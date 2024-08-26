# Dashboard - Sensor Planar
## Laboratório de Escoamento Multifásico Industrial - LEMI-USP

### Desempenho Computacional Recomendado
- Windows 10 ou superior;
- 8 gb de memória RAM;
- Intel Core i3 ou superior;

### Instalação e configuração de softwares

**Python**
- Para instalação do pacote Python, entrar no site oficial do [Python](https://www.python.org/downloads/windows/) e realizar a instalação. Quando instalar, selecione "Add python.exe to PATH" no instalador do VSCode.

**VSCode**
- Para instalação do software, entrar no site oficial do [Visual Studio](https://code.visualstudio.com/) e seguir o procedimento de instalação descrito.
- Após a instalação, abra o PowerShell no Windows (como administrador) executo o comando "Set-ExecutionPolicy AllSigned -Force" para que possa ser usado o ambiente virtual dentro do VSCode.
- Abra o VSCode, na aba esquerda, abra as configurações.
- Com as configurações abertas, no canto superior esquerdo aparecerá um item selecionavel "Open Settiongs (JSON)". Aba-o.
- Copie o código `JSON_config.txt` e cole no JSON que está aberto. Esta é apenas uma configuração de setup do VSCode (não é necessário segui-la).

**Clonagem dos arquivos do Github para o VSCode**
- Dentro do VSCode, abra uma pasta onde deseja realizar a cópia dos arquivos do GitHub.
- Abra o terminal novamente e faça a clonagem dos arquivos do Github com o comando "git clone https://github.com/Guilherme-AFranco/Streamlit-Planar.git" (apenas para o primeiro uso)
- Caso queira sincronizar as possíveis alterações que você venha a realizar dentro do seu GitHub, crie uma pasta no GitHub para alocar os arquivos do Dashboard.
- Dentro desta pasta do GitHub, copie o HTTPS que está na caixa verde escrita "<> Code".
- Abra agora o item "Source Control (Ctrl+Shift+G)" no VSCode (que está no painel da esquerda).
- Clique em "Initialize Repository" e então nas opcões adicionais que apareceu dentro do painel lateral esquerdo, escolha "Show Git Output" -> Terminal.
- Inclua o código "git remote add origin URL_Copiada" onde "URL_Copiada" é o url que você copiou dentro do GitHub (isso é feito apenas uma vez).
- Sempre que tiver alguma alteração nos códigos dentro do VSCode, você deverá fazer o Commit na aba "Source Control" para que a atualização seja realizada dentro do GitHub também.

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

### Abertura do Dashboard
- Com toda a configuração realizada, basta abrir o terminal na pasta onde os arquivos estão alocados e digitar o comando "streamlit run Planar.py".
- Note que Planar.py pode estar com nomes semelhantes a depender da versão final que foi criada. Até o momento estou utilizando a versão `Planar-v4.py`, então o código usado seria "streamlit run Planar-v4.py".
  
