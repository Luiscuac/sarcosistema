import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { obtenerInformeRecetasFarmacia } from '../api/farmaciaApi.js'
import RecetaFicha from '../components/RecetaFicha.jsx'
import '../pages/enfermeria.css'

export default function FarmaciaPage({ usuario, logout }) {
  const [buscar, setBuscar] = useState('')
  const recetas = useQuery({ queryKey: ['farmacia', 'recetas'], queryFn: obtenerInformeRecetasFarmacia })
  const filtradas = useMemo(() => {
    const termino = buscar.trim().toLocaleLowerCase('es')
    if (!termino) return recetas.data || []
    return (recetas.data || []).filter(receta => [
      receta.numero_receta, receta.paciente, receta.historia_clinica,
      receta.prescriptor, receta.diagnostico_principal,
      ...(receta.medicamentos || []).flatMap(m => [m.nombre_generico, m.forma_concentracion, m.indicaciones]),
    ].some(valor => String(valor || '').toLocaleLowerCase('es').includes(termino)))
  }, [buscar, recetas.data])

  return <main className="enf-page">
    <header className="enf-topbar"><strong>SarcoSistema · Farmacia</strong><div><span>{usuario.identificador_acceso}</span><Link to="/inicio">Inicio</Link><button onClick={logout}>Cerrar sesión</button></div></header>
    <div className="enf-content">
      <div className="enf-heading"><div><p>INFORME DE RECETAS</p><h1>Recetas recibidas</h1><span>Consulta las indicaciones emitidas por el médico.</span></div></div>
      {recetas.isPending && <p role="status" className="enf-message">Cargando recetas…</p>}
      {recetas.isError && <p role="alert" className="enf-error">No se pudieron cargar las recetas.</p>}
      {recetas.data?.length === 0 && <section className="enf-panel enf-prescription-empty"><div aria-hidden="true">Rx</div><h2>La bandeja está vacía</h2><p>Las recetas emitidas por el médico aparecerán aquí para su revisión.</p></section>}
      {recetas.data?.length > 0 && <>
        <section className="enf-panel enf-prescription-tools">
          <label className="enf-search">Buscar por paciente, historia clínica, receta o medicamento
            <input type="search" value={buscar} onChange={evento => setBuscar(evento.target.value)} placeholder="Escribe para filtrar las recetas" />
          </label>
          <div className="enf-prescription-tool-actions"><span className="enf-prescription-result-count">{filtradas.length} de {recetas.data.length} recetas</span>
            <button type="button" className="enf-print-button" onClick={() => window.print()} disabled={!filtradas.length}>Imprimir lista</button></div>
        </section>
        {filtradas.length === 0 && <section className="enf-panel"><p className="enf-message">No hay recetas que coincidan con esa búsqueda.</p></section>}
        {filtradas.map(receta => <RecetaFicha key={receta.id} receta={receta} paciente={receta.paciente} estado="Recibida por farmacia" />)}
      </>}
    </div>
  </main>
}
