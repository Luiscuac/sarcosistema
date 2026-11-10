/** Ejemplo local de ecografía para revisar la ficha del paciente de demostración (va dentro de los resultados). */
export default function DatosDemoClinicos() {
  return <article className="med-eco-estudio med-demo-clinical">
    <header><strong>Ecografía de demostración</strong><span>ESTUDIO-DEMO-001</span></header>
    <p className="med-demo-tag">EJEMPLO FICTICIO · SIN VALIDEZ CLÍNICA</p>
    <p className="med-eco-informe">Aquí aparecería el texto del informe publicado por el servicio de imagen.</p>
    <p className="med-message">Este estudio de muestra no contiene imágenes adjuntas.</p>
  </article>
}
