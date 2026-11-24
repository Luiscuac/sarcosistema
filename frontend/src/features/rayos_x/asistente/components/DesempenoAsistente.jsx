import { useQuery } from '@tanstack/react-query'
import Dialogo from '../../../../shared/ui/Dialogo.jsx'
import { obtenerConcordancia } from '../api/rayosXAiApi.js'
import { de10, mensajeErrorAsistente, porcentaje, progresoCalibracion } from '../analisis.js'

function Cifra({ titulo, valor, detalle }) {
  return <div className="rx-des-cifra"><span>{titulo}</span><strong>{valor}</strong>{detalle && <small>{detalle}</small>}</div>
}

function Avance({ filas }) {
  return <ul className="rx-des-avance">{filas.map(f => <li key={f.etiqueta}>
    <div><span>{f.etiqueta}</span><strong>{f.actual} de {f.meta}</strong></div>
    <progress max={f.meta} value={Math.min(f.actual, f.meta)} aria-label={`${f.etiqueta}: ${f.actual} de ${f.meta}`} />
  </li>)}</ul>
}

/** Una tarjeta por cosa que se ajusta con casos del hospital: mismo orden de lectura en las dos. */
function TarjetaAjuste({ titulo, enUso, calibracion, filas, comoSumar, resultado, tecnico }) {
  const listo = calibracion.estado === 'calibrado'
  return <article className="rx-des-ajuste">
    <header>
      <h4>{titulo}</h4>
      <span className={`rx-des-estado ${listo ? 'es-listo' : 'es-juntando'}`}>{listo ? 'Ajuste sugerido listo' : 'Juntando casos'}</span>
    </header>
    <p className="rx-des-enuso">En uso: {enUso}</p>
    <Avance filas={filas} />
    {listo ? resultado : <p className="rx-des-como"><strong>Cómo sumar casos:</strong> {comoSumar}</p>}
    {listo && <details className="rx-ia-plegable"><summary>Para el administrador del sistema</summary><div className="rx-des-tecnico">{tecnico}</div></details>}
  </article>
}

/** Desempeño del asistente en este hospital: solo agregados, sin pacientes. Se abre como diálogo. */
export default function DesempenoAsistente({ usuario, onCerrar }) {
  const consulta = useQuery({ queryKey: ['imagenes', usuario.id, 'concordancia'], queryFn: ({ signal }) => obtenerConcordancia(signal) })
  const d = consulta.data
  return <Dialogo eyebrow="ASISTENTE DE RAYOS X" titulo="Desempeño en este hospital" onCerrar={onCerrar}
    descripcion="Cómo se está usando la IA y cuánto falta para ajustarla a los pacientes de aquí. Solo cifras agregadas: no se muestran pacientes.">
    <div className="rx-des">
      {consulta.isPending && <p role="status">Cargando desempeño del asistente…</p>}
      {consulta.error && <p role="alert">{mensajeErrorAsistente(consulta.error)}</p>}
      {d && <>
        <section aria-labelledby="rx-des-uso">
          <h3 id="rx-des-uso">Uso</h3>
          <div className="rx-des-cifras">
            <Cifra titulo="Radiografías analizadas" valor={d.analisis_completados} detalle={`de ${d.analisis_totales} pedidas`} />
            <Cifra titulo="Revisadas por un médico" valor={d.analisis_revisados} detalle={d.tasa_revision == null ? 'sin datos' : `${porcentaje(d.tasa_revision)} de las analizadas`} />
            <Cifra titulo="El médico estuvo de acuerdo" valor={d.tasa_aceptacion == null ? '—' : porcentaje(d.tasa_aceptacion)}
              detalle={`${d.decisiones.corregida} corregidas · ${d.decisiones.rechazada} rechazadas`} />
          </div>
          <p className="rx-nota">Avisos de diferencia con el informe: {d.avisos_generados.discrepancias} discrepancias y {d.avisos_generados.omisiones} posibles omisiones.
            {d.revisados_con_avisos > 0 && ` En ${d.revisados_con_avisos_corregidos_o_rechazados} de ${d.revisados_con_avisos} revisados con aviso, el médico corrigió o rechazó la propuesta.`}</p>
        </section>

        <section aria-labelledby="rx-des-ajuste">
          <h3 id="rx-des-ajuste">Ajuste a este hospital</h3>
          <p className="rx-nota">Con {d.calibracion.minimo_por_clase} casos de cada tipo, el sistema sugiere cortes calculados con tus pacientes. Nunca se aplican solos.</p>
          <div className="rx-des-ajustes">
            <TarjetaAjuste titulo="Prioridad de la bandeja" calibracion={d.calibracion}
              enUso={`alta desde ${Math.round(d.umbrales_actuales.alta * 100)}, media desde ${Math.round(d.umbrales_actuales.media * 100)} · ${d.umbrales_actuales.origen}`}
              filas={progresoCalibracion(d.calibracion, 'prioridad')}
              comoSumar={'al revisar un análisis, en "Tu revisión" responde si la radiografía es anormal o normal.'}
              resultado={d.calibracion.estado === 'calibrado' && <p className="rx-des-resultado">Con los cortes sugeridos, prioridad media o alta en {de10(d.calibracion.operacion_media.sensibilidad)} de cada 10 placas anormales; prioridad alta en {de10(1 - d.calibracion.operacion_alta.especificidad)} de cada 10 normales.</p>}
              tecnico={d.calibracion.estado === 'calibrado' && <>
                <p>AUC local {d.calibracion.auroc_local.toFixed(2)} con {d.calibracion.casos} casos.</p>
                <code>RADIOLOGY_TRIAGE_UMBRAL_ALTA={d.calibracion.umbral_sugerido_alta.toFixed(3)}</code>
                <code>RADIOLOGY_TRIAGE_UMBRAL_MEDIA={d.calibracion.umbral_sugerido_media.toFixed(3)}</code>
              </>} />
            {d.calibracion_tb && d.patron_tb_actual && <TarjetaAjuste titulo="Aviso de tuberculosis" calibracion={d.calibracion_tb}
              enUso={`corte ${Math.round(d.patron_tb_actual.umbral_actual * 100)} de 100 · ${d.patron_tb_actual.origen}`}
              filas={progresoCalibracion(d.calibracion_tb, 'tb')}
              comoSumar={'en "Tu revisión" marca tuberculosis confirmada o descartada, solo con baciloscopía, GeneXpert o cultivo.'}
              resultado={d.calibracion_tb.estado === 'calibrado' && <p className="rx-des-resultado">Con el corte sugerido, avisa en {de10(d.calibracion_tb.operacion_sugerida.sensibilidad)} de cada 10 casos con TB y por error en {de10(1 - d.calibracion_tb.operacion_sugerida.especificidad)} de cada 10 sin TB (hoy: {de10(d.calibracion_tb.operacion_actual.sensibilidad)} y {de10(1 - d.calibracion_tb.operacion_actual.especificidad)}).</p>}
              tecnico={d.calibracion_tb.estado === 'calibrado' && <>
                <p>AUC local {d.calibracion_tb.auroc_local.toFixed(2)} con {d.calibracion_tb.casos} casos ({d.calibracion_tb.version}).</p>
                <code>RADIOLOGY_TB_UMBRAL_COMPATIBLE={d.calibracion_tb.umbral_sugerido.toFixed(3)}</code>
              </>} />}
          </div>
          {d.calibracion_tb?.otras_versiones > 0 && <p className="rx-nota">{d.calibracion_tb.otras_versiones} casos de TB son de otra versión del aviso y no cuentan.</p>}
        </section>
        <p className="rx-nota">{d.nota}</p>
      </>}
    </div>
  </Dialogo>
}
