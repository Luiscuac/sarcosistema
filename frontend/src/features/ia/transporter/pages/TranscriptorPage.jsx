import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listarRegistrosPrueba } from '../api/transcriptorApi.js'
import './transcriptor.css'

export default function TranscriptorPage({ usuario, logout }) {
  const [registros, setRegistros] = useState([])
  const [seleccionado, setSeleccionado] = useState(null)
  const [error, setError] = useState('')
  const [copiado, setCopiado] = useState(false)

  useEffect(() => {
    listarRegistrosPrueba()
      .then((datos) => {
        setRegistros(datos)
        setSeleccionado(datos[0] ?? null)
      })
      .catch(() => setError('No se pudieron cargar los datos de prueba. Comprueba tu sesión y el backend.'))
  }, [])

  async function copiarRegistro() {
    if (!seleccionado) return
    const texto = [seleccionado.codigo, seleccionado.nombre, seleccionado.fecha, seleccionado.tipo_examen, seleccionado.resultado, seleccionado.unidad].join('\t')
    try {
      await navigator.clipboard.writeText(texto)
      setCopiado(true)
      window.setTimeout(() => setCopiado(false), 2000)
    } catch {
      setError('El navegador no permitió copiar. Power Automate aún puede leer los campos visibles.')
    }
  }

  return (
    <main className="transcriptor-page">
      <header className="transcriptor-header">
        <div><Link to="/inicio" className="transcriptor-brand">SarcoSistema</Link><span>PRUEBA DE AUTOMATIZACIÓN DE ESCRITORIO</span></div>
        <div className="transcriptor-session"><span>{usuario?.identificador_acceso}</span><button type="button" onClick={logout}>Cerrar sesión</button></div>
      </header>
      <section className="transcriptor-content">
        <p className="transcriptor-eyebrow">POWER AUTOMATE DESKTOP · DEMOSTRACIÓN</p>
        <h1>Registros para transcribir</h1>
        <p className="transcriptor-intro">Selecciona un registro ficticio y usa sus campos visibles en un flujo de Power Automate Desktop para completar un formulario de prueba.</p>
        <div className="transcriptor-warning" role="note"><strong>Entorno de prueba.</strong> Estos datos son ficticios y no se consultan ni modifican registros clínicos.</div>
        {error && <p className="transcriptor-error" role="alert">{error}</p>}
        <div className="transcriptor-layout">
          <section className="transcriptor-card" aria-label="Registros disponibles">
            <h2>Registros disponibles</h2>
            {registros.length === 0 && !error && <p>Cargando registros…</p>}
            <div className="transcriptor-list">
              {registros.map((registro) => (
                <button key={registro.id} type="button" className={`transcriptor-row${seleccionado?.id === registro.id ? ' is-selected' : ''}`} onClick={() => setSeleccionado(registro)} data-testid={`registro-${registro.id}`}>
                  <span><strong>{registro.codigo}</strong><small>{registro.nombre}</small></span><span>{registro.tipo_examen}</span>
                </button>
              ))}
            </div>
          </section>
          <section className="transcriptor-card transcriptor-detail" aria-label="Vista previa para automatización">
            <div className="transcriptor-detail-heading"><h2>Vista previa</h2><span>Datos visibles para PAD</span></div>
            {seleccionado ? <dl>
              <div data-testid="campo-codigo"><dt>Código</dt><dd>{seleccionado.codigo}</dd></div>
              <div data-testid="campo-nombre"><dt>Nombre</dt><dd>{seleccionado.nombre}</dd></div>
              <div data-testid="campo-fecha"><dt>Fecha</dt><dd>{seleccionado.fecha}</dd></div>
              <div data-testid="campo-examen"><dt>Examen</dt><dd>{seleccionado.tipo_examen}</dd></div>
              <div data-testid="campo-resultado"><dt>Resultado</dt><dd>{seleccionado.resultado}</dd></div>
              <div data-testid="campo-unidad"><dt>Unidad</dt><dd>{seleccionado.unidad}</dd></div>
            </dl> : <p>Elige un registro para ver sus campos.</p>}
            <button className="transcriptor-copy" type="button" onClick={copiarRegistro} disabled={!seleccionado}>{copiado ? 'Copiado' : 'Copiar campos'}</button>
          </section>
        </div>
        <p className="transcriptor-footnote">Esta pantalla solo prepara y muestra los datos. PAD realiza la interacción con el software externo; revisa el formulario de destino antes de guardarlo.</p>
      </section>
    </main>
  )
}
