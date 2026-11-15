"""Regresión: las solicitudes reales del médico deben llegar a su pantalla de Rayos X con IA."""
import uuid

import pytest
from sqlalchemy import text

from app.imagenes.domain.entities import SolicitudEcografia
from app.imagenes.infrastructure.persistence.repository import EstudiosRepository, RepositorioImagenSql
from app.imagenes.tests.test_estudios_imagenes import estudio_fixture  # noqa: F401


async def _tipo(db, nombre):
    servicio = await db.scalar(text("SELECT id FROM public.servicio WHERE codigo='IMG'"))
    return await db.scalar(text('INSERT INTO public.tipo_estudio(codigo,nombre,servicio_id,requiere_informe,requiere_archivos) '
                                'VALUES (:c,:n,:s,true,true) RETURNING id'), {'c': 'TEST-' + uuid.uuid4().hex, 'n': nombre, 's': servicio})


async def _publicar(db, solicitud_id):
    await db.execute(text("UPDATE public.estudio_solicitado SET estado='publicado' WHERE solicitud_id=:s"), {'s': solicitud_id})
    return await db.scalar(text('SELECT id FROM public.estudio_solicitado WHERE solicitud_id=:s'), {'s': solicitud_id})


@pytest.mark.asyncio
async def test_solicitud_guarda_id_del_medico_y_aparece_en_su_lista(estudio_fixture):  # noqa: F811
    db, usuario, _, _, _ = estudio_fixture
    paciente = await db.scalar(text('SELECT paciente_id FROM public.estudio_solicitado ORDER BY id DESC LIMIT 1'))
    tipo = await _tipo(db, 'Radiografía de tórax ficticia')
    solicitud = await RepositorioImagenSql(db).crear_solicitud(
        SolicitudEcografia(paciente, (tipo,), 'nombre ficticio', 'TEST-' + uuid.uuid4().hex, ''), usuario)
    medico = await db.scalar(text('SELECT medico_solicitante_id FROM public.solicitud WHERE id=:s'), {'s': solicitud})
    assert medico is not None
    estudio = await _publicar(db, solicitud)
    assert estudio in [e['id'] for e in await EstudiosRepository(db).listar(usuario, 1)]


@pytest.mark.asyncio
async def test_solicitud_antigua_sin_id_se_reconoce_por_creador_y_excluye_ecografias(estudio_fixture):  # noqa: F811
    db, usuario, _, _, _ = estudio_fixture
    paciente = await db.scalar(text('SELECT paciente_id FROM public.estudio_solicitado ORDER BY id DESC LIMIT 1'))
    visibles = []
    for nombre in ('Radiografía de tórax antigua', 'Ecografía abdominal ficticia'):
        tipo = await _tipo(db, nombre)
        solicitud = await RepositorioImagenSql(db).crear_solicitud(
            SolicitudEcografia(paciente, (tipo,), 'nombre ficticio', 'TEST-' + uuid.uuid4().hex, ''), usuario)
        await db.execute(text('UPDATE public.solicitud SET medico_solicitante_id=NULL WHERE id=:s'), {'s': solicitud})
        visibles.append(await _publicar(db, solicitud))
    ids = [e['id'] for e in await EstudiosRepository(db).listar(usuario, 1)]
    assert visibles[0] in ids and visibles[1] not in ids
    assert await EstudiosRepository(db).obtener(visibles[0], -1) is None
