/** Ejemplos locales para revisar la ficha del paciente de demostración. */
export default function DatosDemoClinicos({ seccion }) {
  if (seccion === 'receta') return <section className="med-panel med-demo-clinical">
    <div className="med-panel-header"><h2>Ejemplo de receta médica</h2><span>Vista previa · sin validez clínica</span></div>
    <article className="med-nursing-record">
      <header><strong>RECETA DE DEMOSTRACIÓN · SOLO FICTICIA</strong><span>Ejemplo de presentación</span></header>
      <dl><div><dt>Paciente</dt><dd>Paciente ficticio de consulta</dd></div><div><dt>Profesional</dt><dd>Profesional ficticio de demostración</dd></div><div><dt>Diagnóstico</dt><dd>Texto de ejemplo</dd></div></dl>
      <h3>Medicamentos e indicaciones</h3><ul><li><strong>Medicamento de ejemplo</strong> · presentación de muestra<br />Indicación de demostración · cantidad: —</li></ul>
      <p className="med-hint">Este contenido sirve únicamente para previsualizar la ficha. No corresponde a una prescripción ni debe utilizarse como indicación de tratamiento.</p>
    </article>
  </section>
  return <section className="med-panel med-demo-clinical">
    <div className="med-panel-header"><h2>Ejemplo de ecografía</h2><span>Vista previa · informe ficticio</span></div>
    <article className="med-eco-estudio"><header><strong>Ecografía de demostración</strong><span>ESTUDIO-DEMO-001</span></header>
      <p className="med-demo-tag">EJEMPLO FICTICIO · SIN VALIDEZ CLÍNICA</p>
      <p className="med-eco-informe">Aquí aparecería el texto del informe publicado por el servicio de imagen.</p>
      <p className="med-message">Este estudio de muestra no contiene imágenes adjuntas.</p>
    </article>
  </section>
}
