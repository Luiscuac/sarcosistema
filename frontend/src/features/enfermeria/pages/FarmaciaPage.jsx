import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { obtenerInformeRecetasFarmacia } from '../api/farmaciaApi.js'
import '../pages/enfermeria.css'
import { formatearFecha } from '../../../shared/utils/formatearFecha.js'

export default function FarmaciaPage({ usuario, logout }) {
  const recetas = useQuery({ queryKey: ['farmacia', 'recetas'], queryFn: obtenerInformeRecetasFarmacia })
  return <main className="enf-page"><header className="enf-topbar"><strong>SarcoSistema · Farmacia</strong><div><span>{usuario.identificador_acceso}</span><Link to="/inicio">Inicio</Link><button onClick={logout}>Cerrar sesión</button></div></header>
    <div className="enf-content"><div className="enf-heading"><div><p>INFORME DE RECETAS</p><h1>Recetas recibidas</h1><span>Recetas médicas emitidas para dispensación.</span></div></div>
      {recetas.isPending && <p role="status" className="enf-message">Cargando recetas…</p>}
      {recetas.isError && <p role="alert" className="enf-error">No se pudieron cargar las recetas.</p>}
      {recetas.data?.length === 0 && <section className="enf-panel"><p className="enf-message">No hay recetas recibidas.</p></section>}
      {recetas.data?.map(r => <article className="enf-panel enf-prescription-card" key={r.id}>
        <header className="enf-prescription-heading"><div><span className="enf-prescription-kicker">RECETA EMITIDA</span><h2>{r.numero_receta || `Receta #${r.id}`}</h2></div><span className="enf-prescription-status">Recibida por farmacia</span></header>
        <dl className="enf-prescription-meta"><div><dt>Paciente</dt><dd>{r.paciente}</dd></div><div><dt>Historia clínica</dt><dd>{r.historia_clinica || 'No registrada'}</dd></div><div><dt>Médico prescriptor</dt><dd>{r.prescriptor}</dd></div><div><dt>Fecha de emisión</dt><dd>{r.publicado_en ? new Date(r.publicado_en).toLocaleString('es-BO') : formatearFecha(r.fecha)}</dd></div></dl>
        <div className="enf-prescription-diagnosis"><span>Diagnóstico</span><p>{r.diagnostico_principal || 'No indicado'}</p></div>
        <div className="enf-prescription-meds"><h3>Medicamentos prescritos <span>{r.medicamentos.length}</span></h3>
          {r.medicamentos.map((m, i) => <section className="enf-prescription-med" key={`${r.id}-${i}`}><div><strong>{m.nombre_generico}</strong><span>{m.forma_concentracion}</span></div><p>{m.indicaciones}</p><footer><span>Cantidad prescrita</span><strong>{m.cantidad_recetada || 'No especificada'}</strong></footer></section>)}
        </div>
      </article>)}
    </div></main>
}
