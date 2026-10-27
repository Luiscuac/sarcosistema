const BASE_URL = 'http://127.0.0.1:8765'

async function solicitar(ruta, opciones = {}) {
  let respuesta
  try {
    respuesta = await fetch(`${BASE_URL}${ruta}`, {
      ...opciones,
      headers: { 'Content-Type': 'application/json', ...opciones.headers },
    })
  } catch {
    throw new Error('No se pudo conectar con el agente local. Comprueba que esté iniciado en este equipo.')
  }

  const datos = await respuesta.json().catch(() => ({}))
  if (!respuesta.ok) throw new Error(datos.detail || 'El agente local rechazó la operación.')
  return datos
}

export function obtenerEstadoAgente() {
  return solicitar('/health')
}

export function listarVentanasDestino() {
  return solicitar('/v1/ventanas')
}

export function listarCamposDestino(handle) {
  return solicitar(`/v1/ventanas/${handle}/campos`)
}

export function rellenarCamposDestino(handle, campos) {
  return solicitar(`/v1/ventanas/${handle}/rellenar`, {
    method: 'POST',
    body: JSON.stringify({ campos }),
  })
}
