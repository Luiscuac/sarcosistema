from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.accesos.domain.entities import Usuario
from app.accesos.presentation.dependencies.current_user import usuario_actual
from app.accesos.presentation.dependencies.role_required import requiere_rol
from app.config.database import get_db
from app.enfermeria.application.use_cases.registrar_admision import RegistrarAdmision
from app.enfermeria.infrastructure.persistence.repository import SqlAlchemyRegistroEnfermeriaRepository
from app.enfermeria.presentation.schemas import AdmisionRequest
from app.enfermeria.presentation.recetas import RecetaRequest
from sqlalchemy import text
import json

router = APIRouter(prefix='/enfermeria', tags=['enfermeria'])


def get_repository(db: AsyncSession = Depends(get_db)):
    return SqlAlchemyRegistroEnfermeriaRepository(db)


@router.get('/pacientes', dependencies=[Depends(requiere_rol('enfermeria'))])
async def buscar_pacientes(
    buscar: str = Query(min_length=2, max_length=100),
    pagina: int = Query(default=1, ge=1),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    return await repo.buscar_pacientes(buscar.strip(), pagina, 20)


@router.post('/pacientes/{paciente_id}/registros', status_code=201,
             dependencies=[Depends(requiere_rol('enfermeria'))])
async def crear_borrador(
    paciente_id: int,
    datos: AdmisionRequest,
    usuario: Usuario = Depends(usuario_actual),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    try:
        return await RegistrarAdmision(repo).ejecutar(paciente_id, usuario.id, datos)
    except LookupError:
        raise HTTPException(404, 'Paciente no encontrado.') from None


@router.get('/pacientes/{paciente_id}/registros',
            dependencies=[Depends(requiere_rol('enfermeria'))])
async def listar_registros_enfermeria(
    paciente_id: int,
    usuario: Usuario = Depends(usuario_actual),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    if await repo.obtener_paciente(paciente_id) is None:
        raise HTTPException(404, 'Paciente no encontrado.')
    return await repo.listar_registros(paciente_id, usuario.id)


@router.put('/registros/{registro_id}', dependencies=[Depends(requiere_rol('enfermeria'))])
async def editar_borrador(
    registro_id: int,
    datos: AdmisionRequest,
    usuario: Usuario = Depends(usuario_actual),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    resultado = await repo.editar_borrador(registro_id, usuario.id, datos)
    if resultado is None:
        raise HTTPException(409, 'El borrador no existe, no te pertenece o ya fue publicado.')
    return resultado


@router.post('/registros/{registro_id}/publicar',
             dependencies=[Depends(requiere_rol('enfermeria'))])
async def publicar_registro(
    registro_id: int,
    usuario: Usuario = Depends(usuario_actual),
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    resultado = await repo.publicar(registro_id, usuario.id)
    if resultado is None:
        raise HTTPException(409, 'El borrador no existe, no te pertenece o ya fue publicado.')
    return resultado


@router.get('/pacientes/{paciente_id}/publicados',
            dependencies=[Depends(requiere_rol('medico'))])
async def listar_publicados_para_medico(
    paciente_id: int,
    repo: SqlAlchemyRegistroEnfermeriaRepository = Depends(get_repository),
):
    if await repo.obtener_paciente(paciente_id) is None:
        raise HTTPException(404, 'Paciente no encontrado.')
    return await repo.listar_publicados(paciente_id)


@router.post('/pacientes/{paciente_id}/recetas', status_code=201,
             dependencies=[Depends(requiere_rol('enfermeria'))])
async def crear_receta(paciente_id: int, datos: RecetaRequest,
                       usuario: Usuario = Depends(usuario_actual),
                       db: AsyncSession = Depends(get_db)):
    existe = (await db.execute(text("SELECT 1 FROM public.paciente WHERE id=:id AND estado='activo'"), {'id': paciente_id})).scalar_one_or_none()
    if not existe:
        raise HTTPException(404, 'Paciente no encontrado.')
    campos = ['establecimiento','programas','numero_receta','venta','historia_clinica','tipo_atencion','fecha','diagnostico_principal','diagnostico_secundario','prestaciones','medicamentos','dispensador','prescriptor','costo_total','paciente_firma']
    valores = datos.model_dump(mode='json')
    params = {k: valores[k] for k in campos}
    params.update(paciente=paciente_id, usuario=usuario.id)
    for campo in ('prestaciones','medicamentos'):
        params[campo] = json.dumps(params[campo], ensure_ascii=False, allow_nan=False)
    receta_id = (await db.execute(text('''INSERT INTO public.receta_enfermeria
        (paciente_id, registrado_por, establecimiento, programas, numero_receta, venta,
         historia_clinica, tipo_atencion, fecha, diagnostico_principal, diagnostico_secundario,
         prestaciones, medicamentos, dispensador, prescriptor, costo_total, paciente_firma)
        VALUES (:paciente,:usuario,:establecimiento,:programas,:numero_receta,:venta,
         :historia_clinica,:tipo_atencion,:fecha,:diagnostico_principal,:diagnostico_secundario,
         CAST(:prestaciones AS jsonb),CAST(:medicamentos AS jsonb),:dispensador,:prescriptor,:costo_total,:paciente_firma)
        RETURNING id'''), params)).scalar_one()
    await db.execute(text("INSERT INTO public.auditoria_accion (fecha_hora,usuario_id,accion,entidad_afectada,referencia_registro) VALUES(now(),:u,'crear','receta_enfermeria',:r)"), {'u': usuario.id, 'r': str(receta_id)})
    return {'id': receta_id, 'estado': 'borrador'}


@router.get('/pacientes/{paciente_id}/recetas', dependencies=[Depends(requiere_rol('enfermeria'))])
async def listar_recetas_enfermeria(paciente_id: int, usuario: Usuario = Depends(usuario_actual), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text('''SELECT r.*, u.identificador_acceso AS registrado_por FROM public.receta_enfermeria r JOIN public.usuario u ON u.id=r.registrado_por WHERE r.paciente_id=:p AND r.registrado_por=:u ORDER BY r.creado_en DESC'''), {'p': paciente_id, 'u': usuario.id})).mappings().all()
    return [dict(row) for row in rows]


@router.post('/recetas/{receta_id}/publicar', dependencies=[Depends(requiere_rol('enfermeria'))])
async def publicar_receta(receta_id: int, usuario: Usuario = Depends(usuario_actual), db: AsyncSession = Depends(get_db)):
    result = (await db.execute(text("UPDATE public.receta_enfermeria SET estado='publicado', publicado_por=:u, publicado_en=now() WHERE id=:id AND registrado_por=:u AND estado='borrador' RETURNING id"), {'id': receta_id, 'u': usuario.id})).scalar_one_or_none()
    if result is None:
        raise HTTPException(409, 'El borrador no existe, no te pertenece o ya fue publicado.')
    await db.execute(text("INSERT INTO public.auditoria_accion (fecha_hora,usuario_id,accion,entidad_afectada,referencia_registro) VALUES(now(),:u,'publicar','receta_enfermeria',:r)"), {'u': usuario.id, 'r': str(result)})
    return {'id': result, 'estado': 'publicado'}


@router.get('/pacientes/{paciente_id}/recetas-publicadas', dependencies=[Depends(requiere_rol('medico'))])
async def recetas_publicadas_medico(paciente_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text("SELECT r.*, u.identificador_acceso AS registrado_por, up.identificador_acceso AS publicado_por FROM public.receta_enfermeria r JOIN public.usuario u ON u.id=r.registrado_por LEFT JOIN public.usuario up ON up.id=r.publicado_por WHERE r.paciente_id=:p AND r.estado='publicado' ORDER BY r.publicado_en DESC"), {'p': paciente_id})).mappings().all()
    return [dict(row) for row in rows]
