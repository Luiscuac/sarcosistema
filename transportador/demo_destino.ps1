Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Programa destino de prueba'
$form.Name = 'sarcoDemoDestino'
$form.StartPosition = 'CenterScreen'
$form.Size = [System.Drawing.Size]::new(650, 610)
$form.MinimumSize = [System.Drawing.Size]::new(650, 610)

$titulo = New-Object System.Windows.Forms.Label
$titulo.Text = 'Formulario de destino para probar el agente local'
$titulo.AutoSize = $true
$titulo.Location = [System.Drawing.Point]::new(20, 18)
$titulo.Font = [System.Drawing.Font]::new('Segoe UI', 12, [System.Drawing.FontStyle]::Bold)
$form.Controls.Add($titulo)

$definiciones = @(
    @{ Id = 'codigo'; Etiqueta = 'Codigo' },
    @{ Id = 'nombre'; Etiqueta = 'Nombre' },
    @{ Id = 'fecha'; Etiqueta = 'Fecha' },
    @{ Id = 'examen'; Etiqueta = 'Examen' },
    @{ Id = 'resultado'; Etiqueta = 'Resultado' },
    @{ Id = 'unidad'; Etiqueta = 'Unidad' }
)

$campos = @{}
$y = 70
foreach ($definicion in $definiciones) {
    $etiqueta = New-Object System.Windows.Forms.Label
    $etiqueta.Text = $definicion.Etiqueta
    $etiqueta.AutoSize = $true
    $etiqueta.Location = [System.Drawing.Point]::new(24, ($y + 5))
    $form.Controls.Add($etiqueta)

    $entrada = New-Object System.Windows.Forms.TextBox
    $entrada.Name = $definicion.Id
    $entrada.AccessibleName = $definicion.Etiqueta
    $entrada.Location = [System.Drawing.Point]::new(145, $y)
    $entrada.Size = [System.Drawing.Size]::new(450, 28)
    $entrada.Anchor = 'Top, Left, Right'
    $form.Controls.Add($entrada)
    $campos[$definicion.Id] = $entrada
    $y += 42
}

$guardar = New-Object System.Windows.Forms.Button
$guardar.Text = 'Guardar fila de prueba'
$guardar.Name = 'guardarFila'
$guardar.Location = [System.Drawing.Point]::new(145, 330)
$guardar.Size = [System.Drawing.Size]::new(190, 34)
$form.Controls.Add($guardar)

$lista = New-Object System.Windows.Forms.ListBox
$lista.Name = 'filasGuardadas'
$lista.Location = [System.Drawing.Point]::new(24, 390)
$lista.Size = [System.Drawing.Size]::new(570, 145)
$lista.Anchor = 'Top, Bottom, Left, Right'
$form.Controls.Add($lista)

$guardar.Add_Click({
    $valores = foreach ($definicion in $definiciones) {
        $campos[$definicion.Id].Text
    }
    $lista.Items.Add(($valores -join ' | ')) | Out-Null
})

[void]$form.ShowDialog()
