// Pantalla principal de cada rol. Lo usan el login (a dónde ir al entrar) e Inicio
// (los roles con módulo disponible entran directamente a su área de trabajo).

export const DESTINO_POR_ROL = {
  medico: '/consultas',
  laboratorio: '/laboratorio',
  enfermeria: '/enfermeria',
  imagenes: '/ecografia',
  rayos_x: '/rayos-x/gestion',
  farmacia: '/farmacia',
}

export const destinoDeRol = (rol) => DESTINO_POR_ROL[rol] ?? '/inicio'

/** Los módulos médicos se conectan desde su navegación lateral. */
export const redireccionDesdeInicio = (rol) => DESTINO_POR_ROL[rol] ?? null
