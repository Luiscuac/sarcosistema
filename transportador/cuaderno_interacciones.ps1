Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$pacientes = @(
    [pscustomobject]@{ Registro = 'PAC-DEMO-CONSULTA-001'; Nombre = 'Paciente ficticio de consulta'; Documento = 'TEST-001'; Nacimiento = '01/01/1990'; Sexo = 'F' },
    [pscustomobject]@{ Registro = '48449'; Nombre = 'JAILLITA ARIAS CRECENCIA'; Documento = '1234567'; Nacimiento = '19/04/1944'; Sexo = 'Femenino' },
    [pscustomobject]@{ Registro = '51028'; Nombre = 'MURGUIA SANCHEZ BENJAMIN'; Documento = '2345678'; Nacimiento = '11/02/1980'; Sexo = 'Masculino' },
    [pscustomobject]@{ Registro = '53216'; Nombre = 'NOLVANI ESPINOZA SANTIAGO'; Documento = '3456789'; Nacimiento = '08/09/1992'; Sexo = 'Masculino' },
    [pscustomobject]@{ Registro = '54803'; Nombre = 'PARDO AGUILAR DIANA JHAJA'; Documento = '4567890'; Nacimiento = '23/07/1987'; Sexo = 'Femenino' },
    [pscustomobject]@{ Registro = '56011'; Nombre = 'PORCO PACO MATTHEW IAN'; Documento = '5678901'; Nacimiento = '15/01/2001'; Sexo = 'Masculino' },
    [pscustomobject]@{ Registro = '57124'; Nombre = 'ROJAS AGUILAR LUCAS'; Documento = '6789012'; Nacimiento = '04/06/2010'; Sexo = 'Masculino' },
    [pscustomobject]@{ Registro = '58732'; Nombre = 'GARRIDO VARGAS CLARA'; Documento = '7890123'; Nacimiento = '27/03/1958'; Sexo = 'Femenino' },
    [pscustomobject]@{ Registro = '60145'; Nombre = 'SOZA VIDAURRE PAHOLE'; Documento = '8901234'; Nacimiento = '12/12/1995'; Sexo = 'Femenino' }
)
$consultas = [System.Collections.Generic.List[object]]::new()
$campos = @(
    @{ Grupo = 'Signos vitales y antropometría'; Id = 'peso_kg'; Etiqueta = 'Peso (kg)'; Numerico = $true },
    @{ Grupo = 'Signos vitales y antropometría'; Id = 'talla_cm'; Etiqueta = 'Talla (cm)'; Numerico = $true },
    @{ Grupo = 'Signos vitales y antropometría'; Id = 'temperatura_c'; Etiqueta = 'Temperatura (°C)'; Numerico = $true },
    @{ Grupo = 'Signos vitales y antropometría'; Id = 'frecuencia_cardiaca'; Etiqueta = 'Frecuencia cardíaca (lat/min)'; Numerico = $true },
    @{ Grupo = 'Signos vitales y antropometría'; Id = 'frecuencia_respiratoria'; Etiqueta = 'Frecuencia respiratoria (resp/min)'; Numerico = $true },
    @{ Grupo = 'Signos vitales y antropometría'; Id = 'presion_sistolica'; Etiqueta = 'Presión sistólica (mmHg)'; Numerico = $true },
    @{ Grupo = 'Signos vitales y antropometría'; Id = 'presion_diastolica'; Etiqueta = 'Presión diastólica (mmHg)'; Numerico = $true },
    @{ Grupo = 'Signos vitales y antropometría'; Id = 'saturacion_oxigeno'; Etiqueta = 'Saturación de oxígeno (%)'; Numerico = $true },
    @{ Grupo = 'S · Subjetivo'; Id = 'motivo_consulta'; Etiqueta = 'Motivo de consulta *' },
    @{ Grupo = 'S · Subjetivo'; Id = 'sintomas'; Etiqueta = 'Síntomas' },
    @{ Grupo = 'S · Subjetivo'; Id = 'enfermedad_actual'; Etiqueta = 'Enfermedad actual' },
    @{ Grupo = 'S · Subjetivo'; Id = 'antecedentes'; Etiqueta = 'Antecedentes relevantes' },
    @{ Grupo = 'O · Objetivo'; Id = 'examen_fisico'; Etiqueta = 'Examen físico' },
    @{ Grupo = 'O · Objetivo'; Id = 'hallazgos'; Etiqueta = 'Hallazgos clínicos' },
    @{ Grupo = 'O · Objetivo'; Id = 'observaciones'; Etiqueta = 'Observaciones' },
    @{ Grupo = 'A · Análisis'; Id = 'evaluacion_clinica'; Etiqueta = 'Evaluación clínica' },
    @{ Grupo = 'A · Análisis'; Id = 'diagnostico_principal'; Etiqueta = 'Diagnóstico principal *' },
    @{ Grupo = 'A · Análisis'; Id = 'diagnosticos_secundarios'; Etiqueta = 'Diagnósticos secundarios' },
    @{ Grupo = 'P · Plan de acción'; Id = 'tratamiento'; Etiqueta = 'Tratamiento' },
    @{ Grupo = 'P · Plan de acción'; Id = 'medicamentos'; Etiqueta = 'Medicamentos indicados (texto)' },
    @{ Grupo = 'P · Plan de acción'; Id = 'indicaciones'; Etiqueta = 'Indicaciones médicas' },
    @{ Grupo = 'P · Plan de acción'; Id = 'estudios_solicitados'; Etiqueta = 'Estudios complementarios solicitados' },
    @{ Grupo = 'P · Plan de acción'; Id = 'referencias'; Etiqueta = 'Referencias y contrarreferencias' },
    @{ Grupo = 'P · Plan de acción'; Id = 'recomendaciones'; Etiqueta = 'Recomendaciones' },
    @{ Grupo = 'P · Plan de acción'; Id = 'plan_seguimiento'; Etiqueta = 'Seguimiento o próxima revisión' }
)

$form = New-Object System.Windows.Forms.Form
$form.Text = 'Cuaderno de consulta externa - Demo'
$form.StartPosition = 'CenterScreen'
$form.Size = [System.Drawing.Size]::new(1180, 820)
$form.MinimumSize = [System.Drawing.Size]::new(1000, 680)
$form.BackColor = [System.Drawing.Color]::FromArgb(242, 245, 248)

$header = New-Object System.Windows.Forms.Label
$header.Text = 'CUADERNO DE CONSULTA EXTERNA   |   DEMO LOCAL CON DATOS FICTICIOS'
$header.Dock = 'Top'; $header.Height = 42
$header.BackColor = [System.Drawing.Color]::FromArgb(0, 116, 108)
$header.ForeColor = [System.Drawing.Color]::White
$header.Font = [System.Drawing.Font]::new('Segoe UI', 11, [System.Drawing.FontStyle]::Bold)
$header.TextAlign = 'MiddleLeft'; $header.Padding = [System.Windows.Forms.Padding]::new(14, 0, 0, 0)
$form.Controls.Add($header)

$tabs = New-Object System.Windows.Forms.TabControl
$tabs.Dock = 'Fill'; $tabs.Name = 'pestanasPrincipal'; $tabs.AccessibleName = 'Pestañas del cuaderno'
$tabBusqueda = New-Object System.Windows.Forms.TabPage; $tabBusqueda.Text = 'Pacientes'
$tabFicha = New-Object System.Windows.Forms.TabPage; $tabFicha.Text = 'Ficha e historial'
$tabConsulta = New-Object System.Windows.Forms.TabPage; $tabConsulta.Text = 'Nueva consulta'
$tabDetalle = New-Object System.Windows.Forms.TabPage; $tabDetalle.Text = 'Detalle de consulta'
$tabs.TabPages.AddRange(@($tabBusqueda, $tabFicha, $tabConsulta, $tabDetalle))
$form.Controls.Add($tabs)

# Búsqueda y selección de pacientes
$lblBuscar = New-Object System.Windows.Forms.Label
$lblBuscar.Text = 'Buscar por nombre, registro clínico o documento'; $lblBuscar.Location = [System.Drawing.Point]::new(20, 22); $lblBuscar.AutoSize = $true
$txtBuscar = New-Object System.Windows.Forms.TextBox; $txtBuscar.Location = [System.Drawing.Point]::new(20, 48); $txtBuscar.Width = 430; $txtBuscar.Name = 'buscarPaciente'; $txtBuscar.AccessibleName = 'Buscar paciente por nombre, registro clínico o documento'
$listaPacientes = New-Object System.Windows.Forms.ListBox; $listaPacientes.Location = [System.Drawing.Point]::new(20, 88); $listaPacientes.Size = [System.Drawing.Size]::new(650, 540); $listaPacientes.Font = [System.Drawing.Font]::new('Segoe UI', 10); $listaPacientes.Name = 'listaPacientes'; $listaPacientes.AccessibleName = 'Lista de pacientes'
$panelPaciente = New-Object System.Windows.Forms.GroupBox; $panelPaciente.Text = 'Paciente seleccionado'; $panelPaciente.Location = [System.Drawing.Point]::new(700, 88); $panelPaciente.Size = [System.Drawing.Size]::new(420, 240)
$lblPaciente = New-Object System.Windows.Forms.Label; $lblPaciente.Location = [System.Drawing.Point]::new(18, 34); $lblPaciente.Size = [System.Drawing.Size]::new(380, 150); $lblPaciente.Font = [System.Drawing.Font]::new('Segoe UI', 11)
$panelPaciente.Controls.Add($lblPaciente)
$btnFicha = New-Object System.Windows.Forms.Button; $btnFicha.Text = 'Abrir ficha e historial'; $btnFicha.Location = [System.Drawing.Point]::new(700, 350); $btnFicha.Size = [System.Drawing.Size]::new(200, 38)
$btnNueva = New-Object System.Windows.Forms.Button; $btnNueva.Text = 'Iniciar nueva consulta'; $btnNueva.Location = [System.Drawing.Point]::new(910, 350); $btnNueva.Size = [System.Drawing.Size]::new(210, 38)
$lblAviso = New-Object System.Windows.Forms.Label; $lblAviso.Text = 'Entorno de demostración: las consultas se guardan en memoria y se pierden al cerrar.'; $lblAviso.Location = [System.Drawing.Point]::new(700, 415); $lblAviso.Size = [System.Drawing.Size]::new(410, 70); $lblAviso.ForeColor = [System.Drawing.Color]::DimGray
$tabBusqueda.Controls.AddRange(@($lblBuscar, $txtBuscar, $listaPacientes, $panelPaciente, $btnFicha, $btnNueva, $lblAviso))

function Actualizar-ListaPacientes {
    $termino = $txtBuscar.Text.Trim()
    $listaPacientes.Items.Clear()
    foreach ($p in $pacientes) {
        if (-not $termino -or ($p.Nombre -like "*$termino*" -or $p.Registro -like "*$termino*" -or $p.Documento -like "*$termino*")) {
            [void]$listaPacientes.Items.Add("$($p.Nombre)  |  HC $($p.Registro)  |  CI $($p.Documento)")
        }
    }
}
function Obtener-PacienteSeleccionado {
    if ($listaPacientes.SelectedIndex -lt 0) { return $null }
    $termino = $txtBuscar.Text.Trim()
    $resultados = @($pacientes | Where-Object { -not $termino -or $_.Nombre -like "*$termino*" -or $_.Registro -like "*$termino*" -or $_.Documento -like "*$termino*" })
    if ($listaPacientes.SelectedIndex -lt $resultados.Count) { return $resultados[$listaPacientes.SelectedIndex] }
    return $null
}
function Actualizar-Identidad {
    $p = Obtener-PacienteSeleccionado
    if ($null -eq $p) { $lblPaciente.Text = 'Selecciona un paciente de la lista.'; $lblConsultaPaciente.Text = 'Selecciona un paciente antes de registrar la consulta.'; return }
    $lblPaciente.Text = "Nombre: $($p.Nombre)`r`nRegistro clínico: $($p.Registro)`r`nDocumento: $($p.Documento)`r`nNacimiento: $($p.Nacimiento)`r`nSexo: $($p.Sexo)"
    $lblFichaPaciente.Text = "$($p.Nombre)  |  HC $($p.Registro)  |  $($p.Sexo)  |  Nacimiento: $($p.Nacimiento)"
    $lblConsultaPaciente.Text = "Paciente: $($p.Nombre)  |  Registro clínico: $($p.Registro)"
    Actualizar-Historial
}
function Actualizar-Historial {
    $p = Obtener-PacienteSeleccionado
    $gridHistorial.Rows.Clear()
    if ($null -eq $p) { return }
    foreach ($consulta in $consultas | Where-Object { $_.Registro -eq $p.Registro }) {
        $indice = $gridHistorial.Rows.Add($consulta.Fecha, $consulta.Motivo, $consulta.Diagnostico, $consulta.Profesional, 'Consulta externa')
        $gridHistorial.Rows[$indice].Tag = $consulta
    }
}
$txtBuscar.Add_TextChanged({ Actualizar-ListaPacientes })
$listaPacientes.Add_SelectedIndexChanged({ Actualizar-Identidad })
$btnFicha.Add_Click({ if ($null -eq (Obtener-PacienteSeleccionado)) { [void][System.Windows.Forms.MessageBox]::Show('Selecciona primero un paciente.'); return }; $tabs.SelectedTab = $tabFicha })
$btnNueva.Add_Click({ if ($null -eq (Obtener-PacienteSeleccionado)) { [void][System.Windows.Forms.MessageBox]::Show('Selecciona primero un paciente.'); return }; $tabs.SelectedTab = $tabConsulta })

# Ficha e historial del paciente
$lblFichaPaciente = New-Object System.Windows.Forms.Label; $lblFichaPaciente.Location = [System.Drawing.Point]::new(18, 20); $lblFichaPaciente.Size = [System.Drawing.Size]::new(1080, 34); $lblFichaPaciente.Font = [System.Drawing.Font]::new('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
$lblHistorial = New-Object System.Windows.Forms.Label; $lblHistorial.Text = 'Registro histórico de consultas'; $lblHistorial.Location = [System.Drawing.Point]::new(18, 68); $lblHistorial.AutoSize = $true; $lblHistorial.Font = [System.Drawing.Font]::new('Segoe UI', 10, [System.Drawing.FontStyle]::Bold)
$gridHistorial = New-Object System.Windows.Forms.DataGridView; $gridHistorial.Location = [System.Drawing.Point]::new(18, 98); $gridHistorial.Size = [System.Drawing.Size]::new(1080, 500); $gridHistorial.ReadOnly = $true; $gridHistorial.AllowUserToAddRows = $false; $gridHistorial.AutoSizeColumnsMode = 'Fill'; $gridHistorial.SelectionMode = 'FullRowSelect'; $gridHistorial.MultiSelect = $false; $gridHistorial.ColumnCount = 5
@('Fecha', 'Motivo de consulta', 'Diagnóstico principal', 'Profesional', 'Tipo') | ForEach-Object -Begin { $i = 0 } -Process { $gridHistorial.Columns[$i].Name = $_; $i++ }
$btnFichaVolver = New-Object System.Windows.Forms.Button; $btnFichaVolver.Text = 'Volver a pacientes'; $btnFichaVolver.Location = [System.Drawing.Point]::new(18, 620); $btnFichaVolver.Size = [System.Drawing.Size]::new(170, 36); $btnFichaVolver.Add_Click({ $tabs.SelectedTab = $tabBusqueda })
$btnDesdeFicha = New-Object System.Windows.Forms.Button; $btnDesdeFicha.Text = 'Nueva consulta para este paciente'; $btnDesdeFicha.Location = [System.Drawing.Point]::new(200, 620); $btnDesdeFicha.Size = [System.Drawing.Size]::new(240, 36); $btnDesdeFicha.Add_Click({ $tabs.SelectedTab = $tabConsulta })
$btnVerConsulta = New-Object System.Windows.Forms.Button; $btnVerConsulta.Text = 'Ver consulta seleccionada'; $btnVerConsulta.Location = [System.Drawing.Point]::new(455, 620); $btnVerConsulta.Size = [System.Drawing.Size]::new(220, 36)
$tabFicha.Controls.AddRange(@($lblFichaPaciente, $lblHistorial, $gridHistorial, $btnFichaVolver, $btnDesdeFicha, $btnVerConsulta))

# Página de lectura de la consulta elegida en el historial
$lblDetalleTitulo = New-Object System.Windows.Forms.Label; $lblDetalleTitulo.Text = 'Consulta guardada'; $lblDetalleTitulo.Location = [System.Drawing.Point]::new(20, 18); $lblDetalleTitulo.Size = [System.Drawing.Size]::new(1080, 32); $lblDetalleTitulo.Font = [System.Drawing.Font]::new('Segoe UI', 12, [System.Drawing.FontStyle]::Bold)
$txtDetalleConsulta = New-Object System.Windows.Forms.TextBox; $txtDetalleConsulta.Location = [System.Drawing.Point]::new(20, 60); $txtDetalleConsulta.Size = [System.Drawing.Size]::new(1080, 540); $txtDetalleConsulta.Multiline = $true; $txtDetalleConsulta.ReadOnly = $true; $txtDetalleConsulta.ScrollBars = 'Vertical'; $txtDetalleConsulta.Font = [System.Drawing.Font]::new('Consolas', 10)
$btnDetalleVolver = New-Object System.Windows.Forms.Button; $btnDetalleVolver.Text = 'Volver al historial'; $btnDetalleVolver.Location = [System.Drawing.Point]::new(20, 620); $btnDetalleVolver.Size = [System.Drawing.Size]::new(180, 36)
$tabDetalle.Controls.AddRange(@($lblDetalleTitulo, $txtDetalleConsulta, $btnDetalleVolver))

function Mostrar-ConsultaSeleccionada {
    if ($gridHistorial.SelectedRows.Count -eq 0 -or $null -eq $gridHistorial.SelectedRows[0].Tag) {
        [void][System.Windows.Forms.MessageBox]::Show('Selecciona una consulta del historial.'); return
    }
    $consulta = $gridHistorial.SelectedRows[0].Tag
    $lblDetalleTitulo.Text = "Consulta de $($consulta.Paciente) · $($consulta.Fecha)"
    $lineas = @("Paciente: $($consulta.Paciente)", "Registro clínico: $($consulta.Registro)", "Fecha: $($consulta.Fecha)", "Profesional: $($consulta.Profesional)", '')
    foreach ($campo in $campos) {
        $valor = $consulta.PSObject.Properties[$campo.Id].Value
        if ($valor) { $lineas += "$($campo.Etiqueta): $valor" }
    }
    $txtDetalleConsulta.Text = $lineas -join [Environment]::NewLine
    $tabs.SelectedTab = $tabDetalle
}
$btnVerConsulta.Add_Click({ Mostrar-ConsultaSeleccionada })
$gridHistorial.Add_CellDoubleClick({ if ($_.RowIndex -ge 0) { Mostrar-ConsultaSeleccionada } })
$btnDetalleVolver.Add_Click({ $tabs.SelectedTab = $tabFicha })

# Formulario de consulta con los mismos campos que la pantalla web
$panelFormulario = New-Object System.Windows.Forms.Panel; $panelFormulario.Dock = 'Fill'; $panelFormulario.AutoScroll = $true
$flow = New-Object System.Windows.Forms.FlowLayoutPanel; $flow.FlowDirection = 'TopDown'; $flow.WrapContents = $false; $flow.AutoSize = $true; $flow.AutoSizeMode = 'GrowAndShrink'; $flow.Dock = 'Top'; $flow.Padding = [System.Windows.Forms.Padding]::new(14)
$panelFormulario.Controls.Add($flow); $tabConsulta.Controls.Add($panelFormulario)
$lblConsultaPaciente = New-Object System.Windows.Forms.Label; $lblConsultaPaciente.Text = 'Selecciona un paciente antes de registrar la consulta.'; $lblConsultaPaciente.Width = 1080; $lblConsultaPaciente.Height = 32; $lblConsultaPaciente.Font = [System.Drawing.Font]::new('Segoe UI', 10, [System.Drawing.FontStyle]::Bold); [void]$flow.Controls.Add($lblConsultaPaciente)
$lblProfesional = New-Object System.Windows.Forms.Label; $lblProfesional.Text = 'Profesional de salud'; $lblProfesional.Width = 1080; $lblProfesional.Height = 24; [void]$flow.Controls.Add($lblProfesional)
$txtProfesional = New-Object System.Windows.Forms.TextBox; $txtProfesional.Width = 500; $txtProfesional.Text = 'DEMO MEDICO'; $txtProfesional.Name = 'profesional'; $txtProfesional.AccessibleName = 'Profesional de salud'; [void]$flow.Controls.Add($txtProfesional)
$entradas = @{}
$grupoActual = ''
foreach ($campo in $campos) {
    if ($campo.Grupo -ne $grupoActual) {
        $grupoActual = $campo.Grupo
        $grupoBox = New-Object System.Windows.Forms.GroupBox; $grupoBox.Text = $grupoActual; $grupoBox.Width = 1080; $grupoBox.Height = 115; $grupoBox.Padding = [System.Windows.Forms.Padding]::new(12)
        $grupoBox.Tag = $grupoActual
        [void]$flow.Controls.Add($grupoBox)
        $contenedor = New-Object System.Windows.Forms.FlowLayoutPanel; $contenedor.Dock = 'Fill'; $contenedor.AutoScroll = $true; $contenedor.WrapContents = $true
        $grupoBox.Controls.Add($contenedor)
    }
    $fila = New-Object System.Windows.Forms.Panel; $fila.Width = 500; $fila.Height = 76
    $etiqueta = New-Object System.Windows.Forms.Label; $etiqueta.Text = $campo.Etiqueta; $etiqueta.Location = [System.Drawing.Point]::new(4, 3); $etiqueta.Size = [System.Drawing.Size]::new(480, 20)
    $entrada = New-Object System.Windows.Forms.TextBox
    $entrada.Name = $campo.Id; $entrada.AccessibleName = $campo.Etiqueta; $entrada.Tag = $campo.Id
    $entrada.Width = 470; $entrada.Location = [System.Drawing.Point]::new(4, 26)
    if ($campo.Numerico) { $entrada.Height = 24 } else { $entrada.Multiline = $true; $entrada.ScrollBars = 'Vertical'; $entrada.Height = 48 }
    $fila.Controls.AddRange(@($etiqueta, $entrada)); [void]$contenedor.Controls.Add($fila); $entradas[$campo.Id] = $entrada
}
$panelAcciones = New-Object System.Windows.Forms.FlowLayoutPanel; $panelAcciones.Width = 1080; $panelAcciones.Height = 52
$btnGuardar = New-Object System.Windows.Forms.Button; $btnGuardar.Text = 'Finalizar y guardar consulta'; $btnGuardar.Name = 'guardarConsulta'; $btnGuardar.AccessibleName = 'Finalizar y guardar consulta'; $btnGuardar.Width = 230; $btnGuardar.Height = 36
$btnCancelar = New-Object System.Windows.Forms.Button; $btnCancelar.Text = 'Limpiar formulario'; $btnCancelar.Width = 170; $btnCancelar.Height = 36
$btnRegresar = New-Object System.Windows.Forms.Button; $btnRegresar.Text = 'Volver a ficha'; $btnRegresar.Width = 140; $btnRegresar.Height = 36
$panelAcciones.Controls.AddRange(@($btnGuardar, $btnCancelar, $btnRegresar)); [void]$flow.Controls.Add($panelAcciones)
$lblEstado = New-Object System.Windows.Forms.Label; $lblEstado.Width = 1080; $lblEstado.Height = 30; $lblEstado.ForeColor = [System.Drawing.Color]::FromArgb(0, 116, 108); [void]$flow.Controls.Add($lblEstado)

$btnGuardar.Add_Click({
    $p = Obtener-PacienteSeleccionado
    if ($null -eq $p) { [void][System.Windows.Forms.MessageBox]::Show('Selecciona un paciente antes de guardar.'); return }
    if (-not $entradas['motivo_consulta'].Text.Trim() -or -not $entradas['diagnostico_principal'].Text.Trim()) { [void][System.Windows.Forms.MessageBox]::Show('Completa el motivo de consulta y el diagnóstico principal.'); return }
    $registro = [ordered]@{ Registro = $p.Registro; Paciente = $p.Nombre; Fecha = (Get-Date).ToString('dd/MM/yyyy HH:mm'); Profesional = $txtProfesional.Text.Trim(); Motivo = $entradas['motivo_consulta'].Text.Trim(); Diagnostico = $entradas['diagnostico_principal'].Text.Trim() }
    foreach ($campo in $campos) { $registro[$campo.Id] = $entradas[$campo.Id].Text.Trim() }
    $consultas.Add([pscustomobject]$registro)
    Actualizar-Historial
    $lblEstado.Text = "Consulta guardada en el demo para $($p.Nombre), con fecha $($registro.Fecha)."
    $tabs.SelectedTab = $tabFicha
})
$btnCancelar.Add_Click({ foreach ($campo in $campos) { $entradas[$campo.Id].Clear() }; $lblEstado.Text = '' })
$btnRegresar.Add_Click({ $tabs.SelectedTab = $tabFicha })

Actualizar-ListaPacientes
$listaPacientes.SelectedIndex = 0
[void]$form.ShowDialog()
