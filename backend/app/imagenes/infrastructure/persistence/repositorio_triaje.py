"""Persistencia SQL de la cola y los resumenes del triaje radiologico."""
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.imagenes.application.triaje import resumir_triaje
from app.imagenes.infrastructure.archivos import MIMES_RADIOGRAFIA


class RepositorioTriajeSql:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def encolar_triaje(self, estudio_id: int, archivos) -> int:
        """Encola cada radiografia nueva, deduplicada por estudio y hash."""
        encolados = 0
        for archivo in archivos:
            if archivo.mime_type not in MIMES_RADIOGRAFIA.values():
                continue
            fila = await self.db.execute(text('''INSERT INTO public.imagen_triaje_ia
                (id,estudio_id,archivo_id,archivo_sha256) VALUES (CAST(:id AS uuid),:e,:a,:h)
                ON CONFLICT (estudio_id,archivo_sha256) DO NOTHING RETURNING id'''),
                {'id': str(uuid4()), 'e': estudio_id, 'a': archivo.id, 'h': archivo.hash_sha256})
            encolados += fila.first() is not None
        return encolados

    async def triaje_por_estudio(self, estudio_ids: list[int]) -> dict[int, dict]:
        """Resume por estudio el indice maximo y el estado de la cola."""
        if not estudio_ids:
            return {}
        filas = (await self.db.execute(text('''SELECT estudio_id, estado,
            (resultado->'indice_pulmonar'->>'valor')::float AS indice,
            resultado->'calidad'->>'estado' AS calidad,
            resultado->'indice_pulmonar'->'contribuciones' AS contribuciones,
            resultado->'patron_tb'->>'nivel' AS patron_tb
            FROM public.imagen_triaje_ia WHERE estudio_id = ANY(:ids)'''),
            {'ids': list(estudio_ids)})).mappings().all()
        return resumir_triaje([dict(f) for f in filas])
