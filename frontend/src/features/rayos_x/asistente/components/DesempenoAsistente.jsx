import { useQuery } from '@tanstack/react-query'
import { obtenerConcordancia } from '../api/rayosXAiApi.js'
import { mensajeError, porcentaje } from '../analisis.js'

const Tarjeta = ({ titulo, valor, detalle }) => <div className="rx-tarjeta"><span>{titulo}</span><strong>{valor}</strong>{detalle && <small>{detalle}</small>}</div>

/** Desempeño del asistente en este hospital: solo agregados, sin pacientes. */
export default function DesempenoAsistente({ usuario }) {
  const consulta = useQuery({ queryKey: ['imagenes', usuario.id, 'concordancia'], queryFn: ({ signal }) => obtenerConcordancia(signal) })
  if (consulta.isPending) return <p role="status">Cargando desempeño del asistente…</p>
  if (consulta.error) return <p role="alert">{mensajeError(consulta.error)}</p>
  const d = consulta.data
  const c = d.calibracion
  const t = d.calibracion_tb
  const p = d.patron_tb_actual
  return <section className="rx-desempeno" aria-label="Desempeño del asistente">
    <h2>Desempeño del asistente en este hospital</h2>
    <p className="rx-nota">{d.nota} Solo cifras agregadas: no se muestran pacientes.</p>
    <div className="rx-tarjetas">
      <Tarjeta titulo="Análisis completados" valor={d.analisis_completados} detalle={`${d.analisis_totales} solicitados`} />
      <Tarjeta titulo="Revisados por un médico" valor={d.analisis_revisados} detalle={porcentaje(d.tasa_revision)} />
      <Tarjeta titulo="Propuestas aceptadas" valor={porcentaje(d.tasa_aceptacion)} detalle={`${d.decisiones.corregida} corregidas · ${d.decisiones.rechazada} rechazadas`} />
      <Tarjeta titulo="Avisos generados" valor={d.avisos_generados.discrepancias + d.avisos_generados.omisiones}
        detalle={`${d.avisos_generados.discrepancias} discrepancias · ${d.avisos_generados.omisiones} posibles omisiones`} />
    </div>
    <p>De los estudios revisados con avisos ({d.revisados_con_avisos}), el médico corrigió o rechazó la propuesta en {d.revisados_con_avisos_corregidos_o_rechazados}.</p>
    <h3>Calibración local de la prioridad</h3>
    <p>Umbrales en uso: alta ≥ {Math.round(d.umbrales_actuales.alta * 100)}, media ≥ {Math.round(d.umbrales_actuales.media * 100)} ({d.umbrales_actuales.origen}).</p>
    <p>Lecturas médicas registradas: {d.lecturas_medicas.anormal} anormales y {d.lecturas_medicas.normal} normales.</p>
    {c.estado === 'insuficiente'
      ? <p className="rx-advertencia">{c.mensaje} Faltan {c.faltan_anormales} anormales y {c.faltan_normales} normales. Responde “¿la radiografía es anormal?” al revisar cada análisis.</p>
      : <div className="rx-calibracion">
        <p><strong>AUC local del índice: {c.auroc_local.toFixed(2)}</strong> con {c.casos} casos.</p>
        <table className="lab-table"><thead><tr><th>Nivel</th><th>Umbral sugerido</th><th>Sensibilidad</th><th>Especificidad</th></tr></thead><tbody>
          <tr><td>Media</td><td>{Math.round(c.umbral_sugerido_media * 100)}</td><td>{porcentaje(c.operacion_media.sensibilidad)}</td><td>{porcentaje(c.operacion_media.especificidad)}</td></tr>
          <tr><td>Alta</td><td>{Math.round(c.umbral_sugerido_alta * 100)}</td><td>{porcentaje(c.operacion_alta.sensibilidad)}</td><td>{porcentaje(c.operacion_alta.especificidad)}</td></tr>
        </tbody></table>
        <p className="rx-nota">{c.mensaje} Valores para el archivo .env: RADIOLOGY_TRIAGE_UMBRAL_ALTA={c.umbral_sugerido_alta.toFixed(3)} y RADIOLOGY_TRIAGE_UMBRAL_MEDIA={c.umbral_sugerido_media.toFixed(3)}.</p>
      </div>}
    {t && p && <>
      <h3>Calibración local del aviso de tuberculosis</h3>
      <p>Aviso en uso: {p.version}, corte {Math.round(p.umbral_actual * 100)} de 100 ({p.origen}).</p>
      <p>Casos con resultado bacteriológico: {d.lecturas_tb.confirmada} con TB confirmada y {d.lecturas_tb.descartada} con TB descartada{t.otras_versiones > 0 ? ` (${t.otras_versiones} de otra versión del aviso no se usan)` : ''}.</p>
      {t.estado === 'insuficiente'
        ? <p className="rx-advertencia">{t.mensaje} Faltan {t.faltan_con_tb} con TB y {t.faltan_sin_tb} sin TB. Al revisar, indica “Tuberculosis: confirmada / descartada” solo cuando haya baciloscopía, GeneXpert o cultivo.</p>
        : <div className="rx-calibracion">
          <p><strong>AUC local del aviso de TB: {t.auroc_local.toFixed(2)}</strong> con {t.casos} casos.</p>
          <table className="lab-table"><thead><tr><th>Corte</th><th>Valor</th><th>TB detectadas</th><th>Sin TB sin aviso</th></tr></thead><tbody>
            <tr><td>En uso</td><td>{Math.round(t.operacion_actual.umbral * 100)}</td><td>{porcentaje(t.operacion_actual.sensibilidad)}</td><td>{porcentaje(t.operacion_actual.especificidad)}</td></tr>
            <tr><td>Sugerido</td><td>{Math.round(t.umbral_sugerido * 100)}</td><td>{porcentaje(t.operacion_sugerida.sensibilidad)}</td><td>{porcentaje(t.operacion_sugerida.especificidad)}</td></tr>
          </tbody></table>
          <p className="rx-nota">{t.mensaje} Valor para el archivo .env: RADIOLOGY_TB_UMBRAL_COMPATIBLE={t.umbral_sugerido.toFixed(3)}.</p>
        </div>}
    </>}
  </section>
}
