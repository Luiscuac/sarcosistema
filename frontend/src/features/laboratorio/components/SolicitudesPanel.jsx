export default function SolicitudesPanel() {
  return (
    <div className="lab-list-panel">
      <div className="lab-list-toolbar">
        <div>
          <h2>Buscar solicitudes</h2>
          <p>Consulta por paciente o número de solicitud.</p>
        </div>
        <span className="lab-pending-tag">Consulta pendiente de integración</span>
      </div>
      <input
        className="lab-search"
        type="search"
        placeholder="Buscar paciente o solicitud"
        disabled
        aria-label="Buscar paciente o solicitud; función aún no disponible"
      />
      <div className="lab-table-wrap">
        <table className="lab-table">
          <caption className="sr-only">Solicitudes de laboratorio</caption>
          <thead>
            <tr><th>Solicitud / paciente</th><th>Estado</th><th>Exámenes</th><th>Acciones</th></tr>
          </thead>
          <tbody>
            <tr><td className="lab-empty" colSpan="4">
              <strong>Las solicitudes aún no están disponibles en esta vista.</strong>
              <span>El acceso al módulo funciona; la consulta de solicitudes se añadirá en el siguiente incremento.</span>
            </td></tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
