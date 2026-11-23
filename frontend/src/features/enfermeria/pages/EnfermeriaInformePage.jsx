import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  obtenerRecetasRecibidasEnfermeria, obtenerRegistrosEnfermeria, publicarRegistroEnfermeria,
} from '../api/enfermeriaApi.js'
import BarraSuperior from '../../../shared/ui/BarraSuperior.jsx'
import ConfirmarAccion from '../../../shared/ui/ConfirmarAccion.jsx'
import { MEDICIONES, TEXTOS, formularioDesdeRegistro, resumenDelFormulario } from '../utils/signosVitales.js'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'
import { useNotificacion } from '../../../shared/notifications/NotificationContext.jsx'
import './enfermeria.css'
import Boton from '../../../shared/ui/Boton.jsx'
import { mensajeError } from '../../../shared/utils/mensajeError.js'

const fechaHora = (value) => value ? new Date(value).toLocaleString('es-BO') : 'Sin fecha'
const fechaReceta = (receta) => receta.publicado_en
  ? new Date(receta.publicado_en).toLocaleString('es-BO')
  : formatearFecha(receta.fecha)

function ResumenValores({ lineas }) {
  return <dl className="enf-summary">{lineas.map(({ campo, etiqueta, valor }) =>
    <div key={campo}><dt>{etiqueta}</dt><dd>{valor}</dd></div>)}</dl>
}

function CamposInforme({ lineas, titulo }) {
  if (!lineas.length) return null
  return <section className="enf-report-section">
    <h3>{titulo}</h3>
    <dl className="enf-report-fields">{lineas.map(({ campo, etiqueta, valor }) =>
      <div key={campo}><dt>{etiqueta}</dt><dd>{valor}</dd></div>)}</dl>
  </section>
}

function InformeAdmision({ registro, paciente, onVolver, onEditar, onPublicar, ocupado }) {
  const lineas = resumenDelFormulario(formularioDesdeRegistro(registro))
  const camposMedicion = new Set([...Object.keys(MEDICIONES), 'imc', 'presion', 'dolor_escala'])
  const observaciones = lineas.filter(({ campo }) => TEXTOS.some(([nombre]) => nombre === campo))
  const mediciones = lineas.filter(({ campo }) => camposMedicion.has(campo))
  const fecha = fechaHora(registro.publicado_en || registro.creado_en)
  const publicado = registro.estado === 'publicado'
  return <section className="enf-panel enf-admission-report">
    <header className="enf-history-report-header">
      <div>
        <p className="enf-report-eyebrow">INFORME DE ENFERMERÍA</p>
        <h2>Admisión y valoración</h2>
        <p>{publicado ? 'Publicado' : 'Borrador guardado'} el {fecha}</p>
      </div>
      <button type="button" className="enf-history-back" onClick={() => onVolver()}>Volver a registros</button>
    </header>
    <div className="enf-history-report">
      <dl className="enf-report-meta">
        <div><dt>Paciente</dt><dd>{paciente?.nombre_completo || 'Paciente no disponible'}</dd></div>
        <div><dt>{publicado ? 'Publicado por' : 'Registrado por'}</dt><dd>{registro.publicado_por || registro.registrado_por || 'No indicado'}</dd></div>
        <div><dt>Estado</dt><dd>{publicado ? 'Publicado · visible para el médico' : 'Borrador · solo visible para su autora'}</dd></div>
      </dl>
      <CamposInforme lineas={observaciones} titulo="Motivo y valoración" />
      <CamposInforme lineas={mediciones} titulo="Signos vitales" />
      {!lineas.length && <p className="enf-message">Este registro no contiene datos para mostrar.</p>}
      {registro.estado === 'borrador' && <div className="enf-report-actions">
        <button type="button" onClick={() => onEditar(registro)} disabled={ocupado}>Editar borrador</button>
        <Boton onClick={() => onPublicar(registro)} disabled={ocupado}>Publicar para el médico…</Boton>
      </div>}
    </div>
  </section>
}

function InformeReceta({ receta, paciente, onVolver }) {
  return <section className="enf-panel enf-prescription-report">
    <header className="enf-history-report-header">
      <div>
        <p className="enf-report-eyebrow">INFORME DE RECETA</p>
        <h2>{receta.numero_receta || `Receta #${receta.id}`}</h2>
        <p>Emitida el {fechaReceta(receta)}</p>
      </div>
      <button type="button" className="enf-history-back" onClick={() => onVolver()}>Volver a recetas</button>
    </header>
    <div className="enf-history-report">
      <dl className="enf-report-meta">
        <div><dt>Paciente</dt><dd>{paciente?.nombre_completo || 'Paciente no disponible'}</dd></div>
        <div><dt>Historia clínica</dt><dd>{receta.historia_clinica || paciente?.historia_clinica || 'No registrada'}</dd></div>
        <div><dt>Médico prescriptor</dt><dd>{receta.prescriptor || receta.registrado_por || 'No indicado'}</dd></div>
      </dl>
      <section className="enf-report-section">
        <h3>Diagnóstico</h3>
        <p>{receta.diagnostico_principal || 'No indicado'}</p>
      </section>
      <section className="enf-report-section">
        <h3>Medicamentos prescritos <span>{receta.medicamentos?.length || 0}</span></h3>
        {receta.medicamentos?.length
          ? <ol className="enf-report-medications">
            {receta.medicamentos.map((medicamento, indice) => <li key={`${receta.id}-${indice}`}>
              <header><strong>{medicamento.nombre_generico}</strong><span>{medicamento.forma_concentracion}</span></header>
              <p>{medicamento.indicaciones}</p>
              <footer>Cantidad recetada: <strong>{medicamento.cantidad_recetada || 'No especificada'}</strong></footer>
            </li>)}
          </ol>
          : <p className="enf-message">La receta no tiene medicamentos registrados.</p>}
      </section>
    </div>
  </section>
}

export default function EnfermeriaInformePage({ usuario, logout }) {
  const { pacienteId, registroId, recetaId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const cache = useQueryClient()
  const { notificar } = useNotificacion()
  const [confirmacion, setConfirmacion] = useState(false)
  const [ocupado, setOcupado] = useState(false)
  const esReceta = Boolean(recetaId)
  const registros = useQuery({
    queryKey: ['enfermeria', 'registros', pacienteId],
    queryFn: () => obtenerRegistrosEnfermeria(pacienteId),
    enabled: Boolean(registroId),
  })
  const recetas = useQuery({
    queryKey: ['enfermeria', 'recetas-recibidas', pacienteId],
    queryFn: () => obtenerRecetasRecibidasEnfermeria(pacienteId),
    enabled: esReceta,
  })
  const paciente = location.state?.paciente
  const registro = registros.data
    ? registros.data.find((item) => String(item.id) === registroId) || null
    : String(location.state?.registro?.id) === registroId ? location.state.registro : null
  const receta = recetas.data
    ? recetas.data.find((item) => String(item.id) === recetaId) || null
    : String(location.state?.receta?.id) === recetaId ? location.state.receta : null

  function volver(pantalla = esReceta ? 'recetas' : 'registros', edicion = null) {
    const state = { pantalla }
    if (paciente) state.paciente = paciente
    if (edicion) state.edicion = edicion
    navigate('/enfermeria', { state })
  }

  async function publicarBorrador(registroSeleccionado) {
    setOcupado(true)
    try {
      await publicarRegistroEnfermeria(registroSeleccionado.id)
      notificar('Registro publicado. Ya está disponible en la ficha médica del paciente.', 'exito')
    } catch (error) {
      notificar(mensajeError(error, 'No se pudo publicar el registro.'), 'error')
    } finally {
      await cache.invalidateQueries({ queryKey: ['enfermeria', 'registros', pacienteId] })
      setOcupado(false)
      setConfirmacion(false)
    }
  }

  const cargando = esReceta ? recetas.isPending && !receta : registros.isPending && !registro
  const error = esReceta ? recetas.isError && !receta : registros.isError && !registro
  const encontrado = esReceta ? receta : registro
  return <main className="lab-page enf-page">
    <BarraSuperior usuario={usuario} titulo="Enfermería" inicio="/enfermeria" onLogout={logout} />
    <div className="enf-content">
      {cargando
        ? <p role="status" className="enf-message">Cargando informe…</p>
        : error
          ? <p role="alert" className="enf-error">No se pudo cargar el informe.</p>
          : !encontrado
            ? <p role="alert" className="enf-error">No se encontró el informe solicitado.</p>
            : esReceta
              ? <InformeReceta receta={receta} paciente={paciente} onVolver={volver} />
            : <InformeAdmision registro={registro} paciente={paciente} onVolver={volver}
              onEditar={(item) => volver('admision', item)} onPublicar={() => setConfirmacion(true)} ocupado={ocupado} />}
      {(error || !cargando && !encontrado) && <button type="button" className="enf-history-back" onClick={() => volver()}>Volver a Enfermería</button>}
    </div>
    {confirmacion && registro && <ConfirmarAccion titulo="Publicar registro de enfermería" textoConfirmar="Publicar para el médico"
      pendiente={ocupado} onCancelar={() => setConfirmacion(false)} onConfirmar={() => publicarBorrador(registro)}>
      <p>Paciente: <strong>{paciente?.nombre_completo || `#${pacienteId}`}</strong>. Una vez publicado, el equipo médico lo verá y <strong>ya no se podrá editar</strong>.</p>
      <ResumenValores lineas={resumenDelFormulario(formularioDesdeRegistro(registro))} />
    </ConfirmarAccion>}
  </main>
}
