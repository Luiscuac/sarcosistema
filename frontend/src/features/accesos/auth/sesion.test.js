import test from 'node:test'
import assert from 'node:assert/strict'
import { QueryClient } from '@tanstack/react-query'
import { actualizarSesion } from './sesion.js'

function almacenamiento() {
  const items = new Map([['token', 'sesion-ficticia-anterior']])
  return { getItem: k => items.get(k), setItem: (k, v) => items.set(k, v), removeItem: k => items.delete(k) }
}

for (const token of [null, 'otra-sesion-ficticia']) {
  test(`cambio de sesión borra caché clínica (${token === null ? 'salir' : 'entrar'})`, () => {
    const queryClient = new QueryClient()
    const storage = almacenamiento()
    queryClient.setQueryData(['consultas', 'detalle', 1], { motivo_consulta: 'Dato ficticio previo' })
    actualizarSesion(queryClient, storage, token)
    assert.equal(queryClient.getQueryData(['consultas', 'detalle', 1]), undefined)
    assert.equal(queryClient.getQueryCache().getAll().length, 0)
    assert.equal(storage.getItem('token'), token ?? undefined)
  })
}

test('una petición anterior que termina tarde no repuebla caché tras salir', async () => {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  let terminar
  const pendiente = queryClient.fetchQuery({ queryKey: ['consultas', 'previa'],
    queryFn: () => new Promise(resolve => { terminar = resolve }) }).catch(() => {})
  actualizarSesion(queryClient, almacenamiento(), null)
  terminar({ sintomas: 'Dato ficticio de otra sesión' })
  await pendiente
  assert.equal(queryClient.getQueryData(['consultas', 'previa']), undefined)
})
