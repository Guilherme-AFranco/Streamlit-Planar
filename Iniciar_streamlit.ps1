$nome1 = "Laptop Guilherme (e5e)"
$nome2 = "Desktop LEMI (4fg)"
$dockerDir = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
$dockerID1 = "e5e103b53684"
$dockerID2 = "4fg849564j8s"
$streamlitFolder = "E:\TCC\1sem-2024\Streamlit-Oficial"

# Carrega a biblioteca do Windows Forms
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Cria um novo formulário
$form = New-Object System.Windows.Forms.Form
$form.Text = "Escolher Container"
$form.Width = 400
$form.Height = 300
$form.StartPosition = "CenterScreen"
$form.BackColor = [System.Drawing.Color]::White

# Adiciona um título
$labelTitle = New-Object System.Windows.Forms.Label
$labelTitle.Text = "Selecione o container Docker"
$labelTitle.Font = New-Object System.Drawing.Font("Arial", 14, [System.Drawing.FontStyle]::Bold)
$labelTitle.AutoSize = $true
$labelX = ($form.Width - $labelTitle.PreferredWidth) / 2
$labelY = 20
$labelTitle.Location = New-Object System.Drawing.Point($labelX, $labelY)
$form.Controls.Add($labelTitle)

# Cria uma caixa de seleção para o container 1
$checkbox1 = New-Object System.Windows.Forms.CheckBox
$checkbox1.Text = "$nome1"
$checkbox1.Font = New-Object System.Drawing.Font("Arial", 10)
$checkbox1.AutoSize = $true
$checkbox1.Location = New-Object System.Drawing.Point(30, 70)
$form.Controls.Add($checkbox1)

# Cria uma caixa de seleção para o container 2
$checkbox2 = New-Object System.Windows.Forms.CheckBox
$checkbox2.Text = "$nome2"
$checkbox2.Font = New-Object System.Drawing.Font("Arial", 10)
$checkbox2.AutoSize = $true
$checkbox2.Location = New-Object System.Drawing.Point(30, 100)
$form.Controls.Add($checkbox2)

# Cria um botão para confirmar a seleção
$buttonStart = New-Object System.Windows.Forms.Button
$buttonStart.Text = "Iniciar"
$buttonStart.Font = New-Object System.Drawing.Font("Arial", 10, [System.Drawing.FontStyle]::Bold)
$buttonStart.Width = 100
$buttonStart.Height = 30
$buttonStart.Location = New-Object System.Drawing.Point(50, 150)
$buttonStart.BackColor = [System.Drawing.Color]::LightBlue
$form.Controls.Add($buttonStart)

# Cria um botão para sair
$buttonExit = New-Object System.Windows.Forms.Button
$buttonExit.Text = "Sair"
$buttonExit.Font = New-Object System.Drawing.Font("Arial", 10, [System.Drawing.FontStyle]::Bold)
$buttonExit.Width = 100
$buttonExit.Height = 30
$buttonExit.Location = New-Object System.Drawing.Point(200, 150)
$buttonExit.BackColor = [System.Drawing.Color]::LightCoral
$form.Controls.Add($buttonExit)

# Função para verificar o status do container
function Get-ContainerStatus {
    param($containerId)
    $status = (docker inspect --format "{{.State.Status}}" $containerId)
    return $status
}

# Define o que acontece ao clicar no botão "Iniciar"
$buttonStart.Add_Click({
    Start-Process "$dockerDir"
    
    Start-Sleep -Seconds 15

    # Inicializa o container escolhido em segundo plano
    if ($checkbox1.Checked) {
        $status = Get-ContainerStatus "$dockerID1"
        if ($status -eq "paused") {
            Start-Process "docker" -ArgumentList "unpause $dockerID1"
        } elseif ($status -eq "exited" -or $status -eq "created") {
            Start-Process "docker" -ArgumentList "start $dockerID1"
        }
    }
    elseif ($checkbox2.Checked) {
        $status = Get-ContainerStatus "$dockerID2"
        if ($status -eq "paused") {
            Start-Process "docker" -ArgumentList "unpause $dockerID2"
        } elseif ($status -eq "exited" -or $status -eq "created") {
            Start-Process "docker" -ArgumentList "start $dockerID"
        }
    } else {
        [System.Windows.Forms.MessageBox]::Show("Por favor, selecione um container.")
        return
    }

    # Ativa o ambiente virtual
        Set-Location -Path "$streamlitFolder"
        .\venv\Scripts\activate

        # Roda o Streamlit em segundo plano
        streamlit run Planar-v4.py


        # Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd 'E:\TCC\1sem-2024\Estudo_Streamlit'; .\venv_Steamlit\Scripts\Activate; streamlit run Planar-v4.py"
        [System.Windows.Forms.MessageBox]::Show("Programa liberado.")

    # Mostra uma mensagem informando que o processo foi iniciado
    # [System.Windows.Forms.MessageBox]::Show("O container foi iniciado e o Streamlit está rodando.")
})

# Define o que acontece ao clicar no botão "Sair"
$buttonExit.Add_Click({
    # Pausa o container escolhido
    if ($checkbox1.Checked) {
        Start-Process "docker" -ArgumentList "pause $dockerID1"
    }
    elseif ($checkbox2.Checked) {
        Start-Process "docker" -ArgumentList "pause $dockerID2"
    }

    # Fecha o formulário
    $form.Close()
})

# Mostra o formulário
$form.ShowDialog()
