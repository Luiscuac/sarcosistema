"""Los modelos ORM de imagen deben coincidir con las tablas reales.

Evita la deriva entre el modelo y la base: un INSERT falla en tiempo de
ejecucion si el modelo declara columnas que la tabla no tiene.
"""
import pytest
from sqlalchemy import text

from app.config.database import Base
from app.laboratorio.infrastructure.persistence.models import ArchivoImagen, InformeImagen


@pytest.mark.asyncio
async def test_las_columnas_de_los_modelos_existen_en_las_tablas():
    """Un solo test: el pool de conexiones no sobrevive entre loops de eventos."""
    from app.config.database import engine

    await engine.dispose()  # descarta conexiones de loops de eventos anteriores
    faltantes = {}
    try:
        async with engine.connect() as conexion:
            transaccion = await conexion.begin()
            try:
                for modelo in (InformeImagen, ArchivoImagen):
                    filas = (await conexion.execute(text("""
                        SELECT column_name FROM information_schema.columns
                         WHERE table_schema = 'public' AND table_name = :tabla
                    """), {'tabla': modelo.__tablename__})).scalars().all()
                    ausentes = {c.name for c in modelo.__table__.columns} - set(filas)
                    if ausentes:
                        faltantes[modelo.__tablename__] = sorted(ausentes)
            finally:
                await transaccion.rollback()
    finally:
        await engine.dispose()
    assert not faltantes, (
        f'columnas en el modelo que no estan en la tabla: {faltantes}'
    )


def test_los_modelos_de_imagen_estan_registrados_en_el_metadata():
    tablas = Base.metadata.tables
    assert 'informe_imagen' in tablas
    assert 'archivo_imagen' in tablas


def test_el_informe_referencia_al_estudio_y_a_su_version_previa():
    claves = {fk.target_fullname for fk in InformeImagen.__table__.foreign_keys}
    assert 'estudio_solicitado.id' in claves
    assert 'informe_imagen.id' in claves


def test_el_archivo_cuelga_del_informe():
    claves = {fk.target_fullname for fk in ArchivoImagen.__table__.foreign_keys}
    assert 'informe_imagen.id' in claves
