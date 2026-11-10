// Pantalla principal de cada rol. Lo usan el login (a dónde ir al entrar) e Inicio
// (los roles con un solo módulo no necesitan la pantalla de bienvenida).

export const DESTINO_POR_ROL = {
  medico: '/consultas',
  laboratorio: '/laboratorio',
  enfermeria: '/enfermeria',
  imagenes: '/imagenes',
  farmacia: '/farmacia',
}

/** Roles que eligen entre varios módulos desde Inicio. */
const ROLES_CON_INICIO = new Set(['medico'])

export const destinoDeRol = (rol) => DESTINO_POR_ROL[rol] ?? '/inicio'

/** Ruta a la que Inicio debe redirigir, o null si el rol usa la pantalla de Inicio. */
export const redireccionDesdeInicio = (rol) =>
  (ROLES_CON_INICIO.has(rol) ? null : DESTINO_POR_ROL[rol] ?? null)
