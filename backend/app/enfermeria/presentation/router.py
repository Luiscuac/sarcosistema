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


@router.get('/pacientes/{paciente_id}/recetas-publicadas', dependencies=[Depends(requiere_rol('medico'))])
async def recetas_publicadas_medico(paciente_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text("SELECT r.*, u.identificador_acceso AS registrado_por, up.identificador_acceso AS publicado_por FROM public.receta_enfermeria r JOIN public.usuario u ON u.id=r.registrado_por LEFT JOIN public.usuario up ON up.id=r.publicado_por WHERE r.paciente_id=:p AND r.estado='publicado' ORDER BY r.publicado_en DESC"), {'p': paciente_id})).mappings().all()
    return [dict(row) for row in rows]


@router.get('/pacientes/{paciente_id}/recetas-recibidas', dependencies=[Depends(requiere_rol('enfermeria'))])
async def recetas_recibidas_enfermeria(paciente_id: int, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text("""SELECT r.*, u.identificador_acceso AS registrado_por
        FROM public.receta_enfermeria r JOIN public.usuario u ON u.id=r.registrado_por
        WHERE r.paciente_id=:p AND r.estado='publicado' ORDER BY r.publicado_en DESC"""), {'p': paciente_id})).mappings().all()
    return [dict(row) for row in rows]


@router.post('/pacientes/{paciente_id}/recetas-medicas', status_code=201,
             dependencies=[Depends(requiere_rol('medico'))])
async def crear_receta_medica(paciente_id: int, datos: RecetaRequest,
                              usuario: Usuario = Depends(usuario_actual),
                              db: AsyncSession = Depends(get_db)):
    existe = (await db.execute(text("SELECT 1 FROM public.paciente WHERE id=:id AND estado='activo'"), {'id': paciente_id})).scalar_one_or_none()
    if not existe:
        raise HTTPException(404, 'Paciente no encontrado.')
    # Mantener `fecha` como datetime.date: asyncpg no acepta texto para una columna date.
    valores = datos.model_dump()
    for campo in ('prestaciones', 'medicamentos'):
        valores[campo] = json.dumps(valores[campo], ensure_ascii=False, allow_nan=False)
    valores.update(paciente=paciente_id, usuario=usuario.id,
                   prescriptor=datos.prescriptor or usuario.identificador_acceso)
    receta_id = (await db.execute(text('''INSERT INTO public.receta_enfermeria
        (paciente_id, registrado_por, publicado_por, estado, establecimiento, programas,
         numero_receta, venta, historia_clinica, tipo_atencion, fecha, diagnostico_principal,
         diagnostico_secundario, prestaciones, medicamentos, prescriptor, costo_total, publicado_en)
        VALUES (:paciente,:usuario,:usuario,'publicado',:establecimiento,:programas,
         :numero_receta,:venta,:historia_clinica,:tipo_atencion,:fecha,:diagnostico_principal,
         :diagnostico_secundario,CAST(:prestaciones AS jsonb),CAST(:medicamentos AS jsonb),
         :prescriptor,:costo_total,now()) RETURNING id'''), valores)).scalar_one()
    await db.execute(text("INSERT INTO public.auditoria_accion (fecha_hora,usuario_id,accion,entidad_afectada,referencia_registro) VALUES(now(),:u,'crear','receta_enfermeria',:r)"), {'u': usuario.id, 'r': str(receta_id)})
    return {'id': receta_id, 'estado': 'enviada_a_farmacia'}


@router.get('/farmacia/recetas', dependencies=[Depends(requiere_rol('farmacia'))])
async def listar_recetas_para_farmacia(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(text('''SELECT r.*, p.nombre_completo AS paciente,
        u.identificador_acceso AS prescriptor FROM public.receta_enfermeria r
        JOIN public.paciente p ON p.id=r.paciente_id
        JOIN public.usuario u ON u.id=r.registrado_por
        WHERE r.estado='publicado' ORDER BY r.publicado_en DESC'''))).mappings().all()
    return [dict(row) for row in rows]
