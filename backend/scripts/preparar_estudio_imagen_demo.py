"""Estudio ficticio opcional, sin cambiar cuentas ni informes existentes."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import uuid

from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.config.database import SessionLocal
from app.config.settings import settings

BASE = Path(__file__).resolve().parents[1]
REFERENCIA = 'RX-DEMO-IA-001'
PACIENTE_CODIGO = 'PAC-DEMO-RX-IA-001'
INFORME = ('SIMULACIÓN DE INTEGRACIÓN: este texto ficticio no es el informe auténtico de la radiografía NIH adjunta. '
           'No se observa derrame pleural. Posible cardiomegalia. Revisar las propuestas experimentales, no usarlas como diagnóstico.')


async def preparar_estudio_demo(db, usuario_id, archivo):
    existente = await db.scalar(text('SELECT 1 FROM public.estudio_solicitado WHERE referencia=:r'), {'r':REFERENCIA})
    if existente:
        raise ValueError('El estudio demo ya existe; no se reemplazó ningún dato.')
    medico = await db.scalar(text('''SELECT m.id FROM public.medico m
        JOIN public.usuario u ON u.trabajador_id=m.trabajador_id JOIN public.rol r ON r.id=u.rol_id
        WHERE u.id=:u AND u.estado='activo' AND m.activo AND r.codigo='medico' '''), {'u':usuario_id})
    if medico is None:
        raise ValueError('Se necesita un usuario médico activo ya preparado.')
    codigo = PACIENTE_CODIGO
    if await db.scalar(text('SELECT 1 FROM public.paciente WHERE codigo_paciente=:c'), {'c':codigo}):
        raise ValueError('El paciente demo ya existe; no se modificó.')
    paciente = await db.scalar(text("INSERT INTO public.paciente(codigo_paciente,nombre_completo,fecha_nacimiento,sexo,sin_documento,estado) VALUES (:c,'Paciente FICTICIO de radiología',DATE '1980-01-01','F',true,'activo') RETURNING id"), {'c':codigo})
    servicio = await db.scalar(text("SELECT id FROM public.servicio WHERE codigo='IMG'"))
    tipo = await db.scalar(text("SELECT id FROM public.tipo_estudio WHERE codigo='RX-TORAX-DEMO-IA'"))
    if tipo is None:
        tipo = await db.scalar(text("INSERT INTO public.tipo_estudio(codigo,nombre,servicio_id,requiere_informe,requiere_archivos) VALUES ('RX-TORAX-DEMO-IA','Tórax frontal — simulación IA',:s,true,true) RETURNING id"), {'s':servicio})
    solicitud = await db.scalar(text("INSERT INTO public.solicitud(referencia,paciente_id,fecha_solicitud,medico_solicitante_id,prioridad) VALUES (:r,:p,now(),:m,'sin_prioridad') RETURNING id"), {'r':REFERENCIA,'p':paciente,'m':medico})
    estudio = await db.scalar(text("INSERT INTO public.estudio_solicitado(referencia,solicitud_id,paciente_id,servicio_id,tipo_estudio_id,estado) VALUES (:r,:s,:p,:v,:t,'publicado') RETURNING id"), {'r':REFERENCIA,'s':solicitud,'p':paciente,'v':servicio,'t':tipo})
    informe = await db.scalar(text("INSERT INTO public.informe_imagen(estudio_id,numero_version,descripcion_texto,estado,usuario_publicacion_id,fecha_hora_publicacion) VALUES (:e,1,:texto,'publicado',:u,now()) RETURNING id"), {'e':estudio,'texto':INFORME,'u':usuario_id})
    await db.execute(text("INSERT INTO public.archivo_imagen(informe_id,nombre_original,url_archivo,mime_type,tamano_bytes,hash_sha256,fecha_carga,created_by) VALUES (:i,'NIH-RX-001.png',:url,'image/png',:tam,:sha,now(),:u)"), {'i':informe,'url':archivo['url_archivo'],'tam':archivo['tamano_bytes'],'sha':archivo['hash_sha256'],'u':usuario_id})
    return estudio


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparar-demo',action='store_true')
    parser.add_argument('--usuario',default='medico_demo')
    args = parser.parse_args()
    if not args.preparar_demo or make_url(settings.database_url).host not in ('localhost','127.0.0.1'):
        raise SystemExit('Solo PostgreSQL local y preparación explícita con --preparar-demo.')
    muestras = BASE/'.datasets/radiologia'
    manifest = json.loads((muestras/'muestras.json').read_text(encoding='utf-8'))
    fuente = next(f for f in manifest['samples'] if f['filename']=='NIH-RX-001.png')
    contenido = (muestras/'NIH-RX-001.png').read_bytes()
    sha = hashlib.sha256(contenido).hexdigest()
    if sha != fuente['sha256']:
        raise SystemExit('La muestra autorizada no coincide con su manifest.')
    raiz = Path(settings.radiology_storage_dir)
    if not raiz.is_absolute():
        raiz = BASE/raiz
    raiz.mkdir(parents=True,exist_ok=True)
    nombre = f'demo-nih-{uuid.uuid4().hex}.png'
    destino = raiz/nombre
    creado = False
    try:
        async with SessionLocal.begin() as db:
            usuario = await db.scalar(text('SELECT id FROM public.usuario WHERE identificador_acceso=:n'), {'n':args.usuario})
            estudio = await preparar_estudio_demo(db,usuario,{'url_archivo':nombre,'tamano_bytes':len(contenido),'hash_sha256':sha})
            with destino.open('xb') as stream:
                stream.write(contenido)
            creado = True
    except BaseException:
        if creado:
            destino.unlink(missing_ok=True)
        raise
    print(f'Estudio ficticio {REFERENCIA} preparado, id {estudio}. Es simulación, no un par clínico auténtico.')


if __name__ == '__main__':
    asyncio.run(main())
