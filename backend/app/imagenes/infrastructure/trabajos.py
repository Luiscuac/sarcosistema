"""Cola local persistida; un líder PostgreSQL y una inferencia a la vez."""
import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.imagenes.application.analizar_estudio import AnalizarEstudio, validar_snapshot
from app.imagenes.domain.vision import ErrorVision, VisionConfig
from app.imagenes.infrastructure.archivos import leer_archivo_local
from app.imagenes.infrastructure.persistence.repository import EstudiosRepository


async def ejecutar_trabajo(trabajo, sesiones, analizador, repositorio=EstudiosRepository, vigente=None, liderazgo=None):
    if vigente and not await vigente():
        return
    resultado, error = None,None
    try:
        async with sesiones.begin() as db:
            snapshot = await repositorio(db).obtener(trabajo['estudio_id'],trabajo['solicitado_por'])
        validar_snapshot(trabajo,snapshot)
        resultado = await analizador.ejecutar(trabajo,snapshot)
        if vigente and not await vigente():
            return
        async with sesiones.begin() as db:
            actual = await repositorio(db).obtener(trabajo['estudio_id'],trabajo['solicitado_por'])
            validar_snapshot(trabajo,actual)
    except ValueError:
        resultado,error = None,'snapshot_obsoleto'
    except ErrorVision as exc:
        resultado,error = None,type(exc).__name__
    except Exception:
        resultado,error = None,'fallo_local'
    if vigente and not await vigente():
        return
    async with sesiones.begin() as db:
        if liderazgo:
            await repositorio(db).finalizar(trabajo['id'],resultado,error,liderazgo=liderazgo)
        else:
            await repositorio(db).finalizar(trabajo['id'],resultado,error)


class Liderazgo:
    def __init__(self, conexion, datos):
        self.conexion,self.datos = conexion,datos
        self.guard = asyncio.Lock()
        self.perdido = False

    async def _comprobar(self):
        if self.perdido:
            return False
        try:
            existe = await self.conexion.scalar(text('''SELECT EXISTS(SELECT 1 FROM pg_locks
                WHERE locktype='advisory' AND classid=0 AND objid=2111009 AND objsubid=1
                AND granted AND pid=pg_backend_pid())'''))
            await self.conexion.commit()
            self.perdido = not existe
        except Exception:
            # Drivers pueden emitir errores de protocolo sin envolver al perder
            # la sesión. Ante cualquier incertidumbre se pierde liderazgo.
            self.perdido = True
        return not self.perdido

    async def comprobar(self):
        async with self.guard:
            return await self._comprobar()

    async def reclamar(self):
        async with self.guard:
            if not await self._comprobar():
                return None
            # Claim y COMMIT en la MISMA conexión que posee el lock. Si muere,
            # se revierte la transacción antes de que otro líder pueda recuperarla.
            async with self.conexion.begin():
                async with AsyncSession(bind=self.conexion) as db:
                    return await EstudiosRepository(db).reclamar()

    async def recuperar(self):
        async with self.guard:
            if not await self._comprobar():
                return
            async with self.conexion.begin():
                async with AsyncSession(bind=self.conexion) as db:
                    await EstudiosRepository(db).recuperar_interrumpidos()

    async def vigilar(self, terminar):
        while not terminar.is_set() and await self.comprobar():
            try:
                await asyncio.wait_for(terminar.wait(),timeout=1)
            except asyncio.TimeoutError:
                pass


class GestorTrabajos:
    def __init__(self, engine, sesiones, analizador):
        self.engine,self.sesiones,self.analizador = engine,sesiones,analizador
        self.detener = asyncio.Event()

    async def esperar(self):
        try:
            await asyncio.wait_for(self.detener.wait(),timeout=2)
        except asyncio.TimeoutError:
            pass

    async def ejecutar(self):
        while not self.detener.is_set():
            try:
                async with self.engine.connect() as lider:
                    adquirido = await lider.scalar(text('SELECT pg_try_advisory_lock(2111009)'))
                    await lider.commit()
                    if not adquirido:
                        await self.esperar()
                        continue
                    datos = (await lider.execute(text('SELECT pid,backend_start AS inicio FROM pg_stat_activity WHERE pid=pg_backend_pid()'))).mappings().one()
                    await lider.commit()
                    vigencia = Liderazgo(lider,dict(datos))
                    finalizar_monitor = asyncio.Event()
                    monitor = asyncio.create_task(vigencia.vigilar(finalizar_monitor))
                    try:
                        await vigencia.recuperar()
                        while not self.detener.is_set() and not vigencia.perdido:
                            trabajo = await vigencia.reclamar()
                            if trabajo:
                                await ejecutar_trabajo(trabajo,self.sesiones,self.analizador,
                                    vigente=vigencia.comprobar,liderazgo=vigencia.datos)
                            else:
                                await self.esperar()
                    finally:
                        finalizar_monitor.set()
                        await monitor
                        await lider.execute(text('SELECT pg_advisory_unlock(2111009)'))
                        await lider.commit()
            except Exception:
                # Fallo de infraestructura: no registrar SQL/parámetros clínicos.
                await self.esperar()


def construir_gestor():
    from app.config.database import engine, SessionLocal
    from app.config.settings import settings
    from app.imagenes.infrastructure.rag.servicio import ServicioRag
    from app.imagenes.infrastructure.vision.servicio import AnalizadorTorax
    base = Path(__file__).resolve().parents[3]
    raiz = Path(settings.radiology_storage_dir)
    if not raiz.is_absolute():
        raiz = base/raiz
    vision = AnalizadorTorax(VisionConfig(base/'.models/radiologia',
        min_free_bytes=settings.radiology_vision_min_free_mib*1024**2))
    rag = ServicioRag(base/'.models/rag-torax',base/'.datasets/rag-torax',SessionLocal)
    analizador = AnalizarEstudio(vision,rag,lambda archivo:leer_archivo_local(raiz,archivo)[0],settings.radiology_score_threshold)
    return GestorTrabajos(engine,SessionLocal,analizador)
