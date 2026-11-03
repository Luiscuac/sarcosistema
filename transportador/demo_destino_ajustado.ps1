Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# --- Configuración del Formulario Principal ---
$mainForm = New-Object System.Windows.Forms.Form
$mainForm.Text = "CUADERNO DE CONSULTA EXTERNA - Registro de Pacientes"
$mainForm.Size = New-Object System.Drawing.Size(1200, 750)
$mainForm.StartPosition = "CenterScreen"
$mainForm.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 240)

# --- PANEL IZQUIERDO: Lista de Pacientes ---
$panelLeft = New-Object System.Windows.Forms.Panel
$panelLeft.Dock = [System.Windows.Forms.DockStyle]::Left
$panelLeft.Width = 250
$panelLeft.BorderStyle = [System.Windows.Forms.BorderStyle]::FixedSingle
$mainForm.Controls.Add($panelLeft)

$lblPacientes = New-Object System.Windows.Forms.Label
$lblPacientes.Text = "Lista de Pacientes"
$lblPacientes.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$lblPacientes.Dock = [System.Windows.Forms.DockStyle]::Top
$lblPacientes.Height = 25
$lblPacientes.TextAlign = "MiddleCenter"
$lblPacientes.BackColor = [System.Drawing.Color]::LightGray
$panelLeft.Controls.Add($lblPacientes)

$listBoxPacientes = New-Object System.Windows.Forms.ListBox
$listBoxPacientes.Dock = [System.Windows.Forms.DockStyle]::Fill
@("MURGUIA SANCHEZ BENJAMIN", "NOLVANI ESPINOZA SANTIAGO", "PARDO AGUILAR DIANA JHAJA", 
  "PORCO PACO MATTHEW IAN", "ROJAS AGUILAR LUCAS", "JAILLITA ARIAS CRECENCIA", 
  "GARRIDO VARGAS CLARA", "SOZA VIDAURRE PAHOLE") | ForEach-Object {
    [void]$listBoxPacientes.Items.Add($_)
}
$panelLeft.Controls.Add($listBoxPacientes)

$panelSearch = New-Object System.Windows.Forms.Panel
$panelSearch.Dock = [System.Windows.Forms.DockStyle]::Bottom
$panelSearch.Height = 40
$txtBuscar = New-Object System.Windows.Forms.TextBox
$txtBuscar.Location = New-Object System.Drawing.Point(5, 10)
$txtBuscar.Width = 150
$btnBuscar = New-Object System.Windows.Forms.Button
$btnBuscar.Text = "Buscar"
$btnBuscar.Location = New-Object System.Drawing.Point(160, 8)
$btnBuscar.Width = 80
$panelSearch.Controls.AddRange(@($txtBuscar, $btnBuscar))
$panelLeft.Controls.Add($panelSearch)

# --- PANEL PRINCIPAL (DERECHO) ---
$panelMain = New-Object System.Windows.Forms.Panel
$panelMain.Dock = [System.Windows.Forms.DockStyle]::Fill
$mainForm.Controls.Add($panelMain)

# 1. Cabecera con Datos del Paciente
$gbPaciente = New-Object System.Windows.Forms.GroupBox
$gbPaciente.Text = "Paciente"
$gbPaciente.Dock = [System.Windows.Forms.DockStyle]::Top
$gbPaciente.Height = 70
$gbPaciente.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)

$lblInfo1 = New-Object System.Windows.Forms.Label
$lblInfo1.Text = "REGISTRO CLÍNICO: 48449`t`tFECHA DE NACIMIENTO: 19/04/1944"
$lblInfo1.Location = New-Object System.Drawing.Point(15, 20)
$lblInfo1.AutoSize = $true

$lblInfo2 = New-Object System.Windows.Forms.Label
$lblInfo2.Text = "NOMBRE COMPLETO: CRECENCIA JAILLITA ARIAS`t`tSEXO: Femenino"
$lblInfo2.Location = New-Object System.Drawing.Point(15, 42)
$lblInfo2.AutoSize = $true

$gbPaciente.Controls.AddRange(@($lblInfo1, $lblInfo2))
$panelMain.Controls.Add($gbPaciente)

# 2. Barra de Herramientas Superior
$toolStrip = New-Object System.Windows.Forms.ToolStrip
$toolStrip.Dock = [System.Windows.Forms.DockStyle]::Top
$btnCuadernos = $toolStrip.Items.Add("Cuadernos")
$btnNueva = $toolStrip.Items.Add("Nueva Consulta")
$btnModificar = $toolStrip.Items.Add("Modificar Consulta")
$btnEliminar = $toolStrip.Items.Add("Eliminar Consulta")
$btnBuscarReg = $toolStrip.Items.Add("Buscar Reg. Clínico")
$btnImpAtencion = $toolStrip.Items.Add("Imprimir Atención")
$btnImpRecibo = $toolStrip.Items.Add("Imprimir Recibo Rec.")

$panelMain.Controls.Add($toolStrip)

# 3. Grid Superior: Registro Histórico del Paciente
$lblHistorico = New-Object System.Windows.Forms.Label
$lblHistorico.Text = "Registro Histórico del Paciente"
$lblHistorico.Dock = [System.Windows.Forms.DockStyle]::Top
$lblHistorico.Height = 25
$lblHistorico.BackColor = [System.Drawing.Color]::Navy
$lblHistorico.ForeColor = [System.Drawing.Color]::White
$lblHistorico.TextAlign = "MiddleLeft"
$lblHistorico.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$panelMain.Controls.Add($lblHistorico)

$gridHistorico = New-Object System.Windows.Forms.DataGridView
$gridHistorico.Dock = [System.Windows.Forms.DockStyle]::Top
$gridHistorico.Height = 180
$gridHistorico.ColumnCount = 5
$gridHistorico.Columns[0].Name = "Fecha"
$gridHistorico.Columns[1].Name = "Registro"
$gridHistorico.Columns[2].Name = "Personal de Salud"
$gridHistorico.Columns[3].Name = "Usuario"
$gridHistorico.Columns[4].Name = "Tipo Paciente"
$gridHistorico.AutoSizeColumnsMode = [System.Windows.Forms.DataGridViewAutoSizeColumnsMode]::Fill

[void]$gridHistorico.Rows.Add("31/12/2025", "CONSULTA EXTERNA", "PATIÑO VALLEJOS", "JPATIÑO", "LEY N° 1152 (SUS)")
[void]$gridHistorico.Rows.Add("19/11/2025", "CONSULTA EXTERNA", "JHONNY WILDER", "JPATIÑO", "LEY N° 1152 (SUS)")
[void]$gridHistorico.Rows.Add("21/05/2024", "CONSULTA EXTERNA", "PATIÑO VALLEJOS", "JPATIÑO", "LEY N° 1152 (SUS)")
[void]$gridHistorico.Rows.Add("01/06/2023", "CONSULTA EXTERNA", "SANCHEZ SORIANO", "JSANCHEZ", "LEY N° 1152 (SUS)")
$panelMain.Controls.Add($gridHistorico)

# 4. Pestañas Inferiores (Atención, Medicamentos, Servicios)
$tabControl = New-Object System.Windows.Forms.TabControl
$tabControl.Dock = [System.Windows.Forms.DockStyle]::Fill

$tabAtencion = New-Object System.Windows.Forms.TabPage
$tabAtencion.Text = "Atención"

$tabMedicamentos = New-Object System.Windows.Forms.TabPage
$tabMedicamentos.Text = "Medicamentos"

$tabServicios = New-Object System.Windows.Forms.TabPage
$tabServicios.Text = "Servicios Complementarios"

$tabControl.Controls.AddRange(@($tabAtencion, $tabMedicamentos, $tabServicios))
$panelMain.Controls.Add($tabControl)

# Grid de Variables en la pestaña Atención
$lblEdad = New-Object System.Windows.Forms.Label
$lblEdad.Text = "Edad del paciente al 19/11/2025: 81 años - 7 meses - 0 días"
$lblEdad.Dock = [System.Windows.Forms.DockStyle]::Top
$lblEdad.Height = 25
$lblEdad.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
$tabAtencion.Controls.Add($lblEdad)

$gridVariables = New-Object System.Windows.Forms.DataGridView
$gridVariables.Dock = [System.Windows.Forms.DockStyle]::Fill
$gridVariables.ColumnCount = 3
$gridVariables.Columns[0].Name = "Variables"
$gridVariables.Columns[1].Name = "Valor"
$gridVariables.Columns[2].Name = "Descripción"
$gridVariables.AutoSizeColumnsMode = [System.Windows.Forms.DataGridViewAutoSizeColumnsMode]::Fill

[void]$gridVariables.Rows.Add("ATENCION", "199566", "199566")
[void]$gridVariables.Rows.Add("PRIMERA CONSULTA", "", "0")
[void]$gridVariables.Rows.Add("PCD ATENDIDOS", "", "")
[void]$gridVariables.Rows.Add("PESO (KG)", "86.3", "86.3 Kg")
[void]$gridVariables.Rows.Add("TALLA (CM)", "145", "145 Cm")

$tabAtencion.Controls.Add($gridVariables)

# --- VENTANA MODAL: Selección de Cuadernos ---
$fnMostrarCuadernos = {
    $subForm = New-Object System.Windows.Forms.Form
    $subForm.Text = "Cuadernos"
    $subForm.Size = New-Object System.Drawing.Size(420, 360)
    $subForm.StartPosition = "CenterParent"
    $subForm.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
    $subForm.MaximizeBox = $false
    $subForm.MinimizeBox = $false

    $opciones = @(
        "Consulta Externa", 
        "Anticoncepción", 
        "Internaciones", 
        "Odontología", 
        "Vacunas", 
        "Certificado Defunción General", 
        "TeleSalud"
    )

    $top = 15
    foreach ($opcion in $opciones) {
        $btn = New-Object System.Windows.Forms.Button
        $btn.Text = $opcion
        $btn.Size = New-Object System.Drawing.Size(260, 30)
        $btn.Location = New-Object System.Drawing.Point(30, $top)
        $btn.TextAlign = "MiddleLeft"
        $btn.Font = New-Object System.Drawing.Font("Segoe UI", 9, [System.Drawing.FontStyle]::Bold)
        $btn.ForeColor = [System.Drawing.Color]::Navy

        # Evento de clic en cada opción
        $btn.Add_Click({
            [System.Windows.Forms.MessageBox]::Show("Seleccionaste: " + $this.Text, "Información")
            $subForm.Close()
        })

        $subForm.Controls.Add($btn)
        $top += 35
    }

    $btnCancelar = New-Object System.Windows.Forms.Button
    $btnCancelar.Text = "Cancelar"
    $btnCancelar.Size = New-Object System.Drawing.Size(100, 30)
    $btnCancelar.Location = New-Object System.Drawing.Point(140, $top + 10)
    $btnCancelar.BackColor = [System.Drawing.Color]::DeepSkyBlue
    $btnCancelar.ForeColor = [System.Drawing.Color]::White
    $btnCancelar.Add_Click({ $subForm.Close() })

    $subForm.Controls.Add($btnCancelar)
    $subForm.ShowDialog()
}

# Evento para abrir el cuadro de "Cuadernos"
$btnCuadernos.Add_Click($fnMostrarCuadernos)

# Lanzar la aplicación
[void]$mainForm.ShowDialog()