import CampoPlantilla from './CampoPlantilla.jsx'
import { fraseTecnicaDesdeAdquisicion } from '../utils/informe.js'

const CLAVES_DATOS = ['tecnica', 'indicacion', 'comparacion']
const CLAVES_CIERRE = ['limitaciones', 'conclusion', 'recomendaciones']

export default function FormularioInforme({ detalle, contenido, onChange, disabled = false }) {
  const generales = detalle.config?.plantilla?.generales || []
  const apartados = detalle.config?.plantilla?.apartados || []
  const cambiar = (grupo, clave, valor) => onChange({ ...contenido, [grupo]: { ...contenido[grupo], [clave]: valor } })
  const campo = item => <CampoPlantilla key={item.clave} campo={item} valor={contenido.generales?.[item.clave]}
    destacado={item.clave === 'conclusion'} disabled={disabled} onChange={valor => cambiar('generales', item.clave, valor)} />
  return <div className="rxe-form-informe">
    <section><h2>Datos del informe</h2>
      {!disabled && <div className="rxe-ayudas-explicitas">
        <button type="button" className="lab-secondary-button" onClick={() => cambiar('generales', 'tecnica', fraseTecnicaDesdeAdquisicion(detalle))}>Proponer técnica desde la adquisición</button>
        <button type="button" className="lab-secondary-button" onClick={() => cambiar('generales', 'indicacion', detalle.estudio.detalle?.indicacion_clinica || '')}>Usar indicación de la solicitud</button>
      </div>}
      {generales.filter(item => CLAVES_DATOS.includes(item.clave)).map(campo)}
    </section>
    <section><h2>Hallazgos</h2>
      {apartados.map(item => <CampoPlantilla key={item.clave} campo={item} valor={contenido.apartados?.[item.clave]}
        disabled={disabled} onChange={valor => cambiar('apartados', item.clave, valor)} />)}
    </section>
    <section><h2>Cierre</h2>{generales.filter(item => CLAVES_CIERRE.includes(item.clave)).map(campo)}</section>
  </div>
}
