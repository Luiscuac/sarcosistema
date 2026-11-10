"""Prueba real aislada: ejecutar solo sobre copia temporal de datos ficticios."""
import asyncio
import json
import socket
import uuid

import httpx
from fastapi import FastAPI
from sqlalchemy import text

from app.accesos.infrastructure.security.jwt_service import JwtTokenService
from app.config.database import SessionLocal, engine
from app.config.settings import settings
from app.imagenes.router import router
from app.imagenes.infrastructure.trabajos import construir_gestor


async def main():
    try:
        socket.create_connection(('1.1.1.1',443),timeout=2).close()
    except OSError:
        pass
    else:
        raise AssertionError('La prueba requiere bloqueo real de salida a Internet')
    async with SessionLocal() as db:
        usuario = await db.scalar(text("SELECT id FROM public.usuario WHERE identificador_acceso='medico_demo'"))
        estudio = await db.scalar(text("SELECT id FROM public.estudio_solicitado WHERE referencia='RX-DEMO-IA-001'"))
        original = await db.scalar(text("SELECT descripcion_texto FROM public.informe_imagen WHERE estudio_id=:id AND estado='publicado'"),{'id':estudio})
    assert usuario and estudio and 'SIMULACIÓN' in original
    token = JwtTokenService(settings.jwt_secret_key).emitir(str(usuario),'medico')
    app = FastAPI()
    app.include_router(router)
    gestor = construir_gestor()
    tarea = asyncio.create_task(gestor.ejecutar())
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://local',headers={'Authorization':f'Bearer {token}'}) as client:
            detalle = (await client.get(f'/imagenes/analisis/estudios/{estudio}')).json()
            imagen = await client.get(f'/imagenes/analisis/estudios/{estudio}/archivos/{detalle["archivo"]["id"]}')
            assert imagen.status_code==200 and imagen.content.startswith(b'\x89PNG')
            solicitud = {'confirmar_torax_frontal':True,'proyeccion':'PA','clave':'offline-'+uuid.uuid4().hex}
            respuesta = await client.post(f'/imagenes/analisis/estudios/{estudio}/analisis',json=solicitud)
            assert respuesta.status_code==202, respuesta.status_code
            id = respuesta.json()['id']
            repetido = await client.post(f'/imagenes/analisis/estudios/{estudio}/analisis',json=solicitud)
            assert repetido.json()['id']==id
            limite = asyncio.get_running_loop().time()+360
            while True:
                resultado = (await client.get(f'/imagenes/analisis/{id}')).json()
                if resultado['estado'] not in ('en_cola','procesando'):
                    break
                assert asyncio.get_running_loop().time()<limite,'Timeout del flujo completo'
                await asyncio.sleep(1)
            assert resultado['estado']=='completado',resultado.get('error_codigo')
            salida = resultado['resultado']
            assert len(salida['vision']['findings'])==3
            assert salida['fusion']['hallazgos_confirmados']==[]
            fuentes = (await client.get(f'/imagenes/analisis/{id}/fuentes')).json()['fuentes']
            assert fuentes and all(f['cita'] for f in fuentes)
            revision = await client.post(f'/imagenes/analisis/{id}/revision',json={
                'version':0,'decision':'rechazada','motivo':'Prueba offline FICTICIA, no diagnóstico.'})
            assert revision.status_code==200 and revision.json()['version_revision']==1
            conflicto = await client.post(f'/imagenes/analisis/{id}/revision',json={
                'version':0,'decision':'rechazada','motivo':'Conflicto ficticio'})
            assert conflicto.status_code==409
            async with SessionLocal() as db:
                actual = await db.scalar(text("SELECT descripcion_texto FROM public.informe_imagen WHERE estudio_id=:id AND estado='publicado'"),{'id':estudio})
            assert actual==original
            print(json.dumps({'offline_real':True,'api_autenticada':True,'imagen_local':True,
                'modelos_cpu_reales':True,'idempotencia':True,'citas_locales':len(fuentes),
                'revision_persistida':True,'conflicto_revision_409':True,'informe_sin_cambios':True,
                'analisis_id':id,'scores_experimentales':salida['vision']['findings'],
                'metricas_vision':salida['vision']['metrics']},indent=2))
    finally:
        gestor.detener.set()
        await tarea
        await engine.dispose()


if __name__=='__main__':
    asyncio.run(main())
