"""Reglas del modulo de imagen, sin HTTP ni base de datos."""
import asyncio
from datetime import date

import pytest

from app.imagenes.application.use_cases.solicitar_ecografia import SolicitarEcografia
from app.imagenes.application.use_cases.trabajar_estudio import GuardarInforme, PublicarInforme
from app.imagenes.domain.entities import InformeImagen, SolicitudEcografia
from app.imagenes.domain.errors import (
    ArchivoVacio,
    EstudioNoEncontrado,
    FormatoNoAdmitido,
    InformeSinContenido,
    InformeYaPublicado,
    SolicitudInvalida,
)
from app.imagenes.infrastructure.storage.almacen_local import AlmacenLocal

TIPOS = ('image/jpeg', 'image/png', 'application/pdf', 'application/dicom')


def _solicitud(**kwargs):
    base = dict(
        paciente_id=1, tipo_estudio_ids=(11,), medico_solicitante_nombre='Dra. Ficticia',
        referencia='', clave_idempotencia='', prioridad='sin_prioridad',
    )
    return SolicitudEcografia(**{**base, **kwargs})


class RepositorioEspia:
    def __init__(self):
        self.solicitud = None
        self.informe = None
        self.publicado = False

    async def crear_solicitud(self, solicitud, usuario_id):
        self.solicitud = (solicitud, usuario_id)
        return 77

    async def obtener_estudio(self, estudio_id):
        from app.imagenes.domain.entities import EstudioImagenDetalle
        from datetime import datetime, timezone

        if estudio_id == 999:
            return None
        return EstudioImagenDetalle(
            estudio_id, 'EST-3', 'SOL-3', 'Paciente ficticio', 'Ecografia abdominal',
            'publicado' if self.publicado else 'pendiente_muestra',
            datetime(2026, 1, 1, tzinfo=timezone.utc), self.informe,
        )

    async def guardar_informe(self, estudio_id, descripcion, archivos, usuario_id):
        self.informe = InformeImagen(1, estudio_id, 1, descripcion, 'borrador', None, None, ())
        return self.informe, True

    async def publicar_informe(self, estudio_id, usuario_id):
        self.publicado = True
        self.informe = InformeImagen(1, estudio_id, 1, 'texto', 'publicado', None, None, ())
        return self.informe


class AlmacenEspia:
    def __init__(self):
        self.guardados = []

    async def guardar(self, contenido, estudio_id, hash_sha256, extension):
        self.guardados.append((estudio_id, hash_sha256, extension, len(contenido)))
        return f'{estudio_id}/{hash_sha256}.{extension}'

    def ruta_absoluta(self, url_archivo):
        return f'/tmp/{url_archivo}'


# ---------- solicitud ----------

async def test_solicitud_valida_llega_al_repositorio():
    repo = RepositorioEspia()
    assert await SolicitarEcografia(repo).ejecutar(_solicitud(), 7) == 77
    assert repo.solicitud[1] == 7


@pytest.mark.parametrize('cambios', [
    {'tipo_estudio_ids': ()},
    {'tipo_estudio_ids': (11, 11)},
    {'medico_solicitante_nombre': '   '},
], ids=['sin_estudios', 'repetido', 'sin_medico'])
async def test_solicitud_invalida_se_rechaza_sin_consultar(cambios):
    repo = RepositorioEspia()
    with pytest.raises(SolicitudInvalida):
        await SolicitarEcografia(repo).ejecutar(_solicitud(**cambios), 7)
    assert repo.solicitud is None


# ---------- subida ----------

async def test_archivos_validos_se_hashean_y_guardan():
    repo, almacen = RepositorioEspia(), AlmacenEspia()
    caso = GuardarInforme(repo, almacen, TIPOS, 15 * 1024 * 1024, 10)
    informe, nuevo = await caso.ejecutar(3, 'Texto', [
        {'nombre': 'a.png', 'mime': 'image/png', 'contenido': b'png-ficticio'},
        {'nombre': 'b.pdf', 'mime': 'application/pdf', 'contenido': b'pdf-ficticio'},
    ], 7)
    assert nuevo is True
    assert informe.descripcion_texto == 'Texto'
    assert len(almacen.guardados) == 2
    assert almacen.guardados[0][2] == 'png'
    assert almacen.guardados[1][2] == 'pdf'
    assert all(len(hash) == 64 for _, hash, _, _ in almacen.guardados)


async def test_el_mismo_archivo_no_se_guarda_dos_veces(tmp_path):
    almacen = AlmacenLocal(str(tmp_path))
    contenido = b'contenido-identico'
    primera = await almacen.guardar(contenido, 3, 'a' * 64, 'png')
    segunda = await almacen.guardar(contenido, 3, 'a' * 64, 'png')
    assert primera == segunda
    assert len(list((tmp_path / '3').iterdir())) == 1


async def test_ruta_fuera_del_almacenamiento_se_rechaza(tmp_path):
    almacen = AlmacenLocal(str(tmp_path))
    with pytest.raises(ValueError):
        almacen.ruta_absoluta('../../etc/passwd')


async def test_archivo_inexistente_no_se_devuelve(tmp_path):
    almacen = AlmacenLocal(str(tmp_path))
    with pytest.raises(FileNotFoundError):
        almacen.ruta_absoluta('3/no-existe.png')


async def test_formato_no_admitido_se_rechaza_antes_de_guardar():
    repo, almacen = RepositorioEspia(), AlmacenEspia()
    caso = GuardarInforme(repo, almacen, TIPOS, 15 * 1024 * 1024, 10)
    with pytest.raises(FormatoNoAdmitido):
        await caso.ejecutar(3, 'Texto', [
            {'nombre': 'x.exe', 'mime': 'application/x-msdownload', 'contenido': b'MZ'},
        ], 7)
    assert almacen.guardados == []


async def test_archivo_vacio_se_rechaza():
    repo, almacen = RepositorioEspia(), AlmacenEspia()
    caso = GuardarInforme(repo, almacen, TIPOS, 15 * 1024 * 1024, 10)
    with pytest.raises(ArchivoVacio):
        await caso.ejecutar(3, 'Texto', [{'nombre': 'v.png', 'mime': 'image/png', 'contenido': b''}], 7)


async def test_demasiados_archivos_se_rechazan():
    repo, almacen = RepositorioEspia(), AlmacenEspia()
    caso = GuardarInforme(repo, almacen, TIPOS, 15 * 1024 * 1024, 2)
    with pytest.raises(ArchivoVacio):
        await caso.ejecutar(3, 'Texto', [
            {'nombre': f'{i}.png', 'mime': 'image/png', 'contenido': b'x'} for i in range(3)
        ], 7)


async def test_informe_sin_texto_ni_imagenes_se_rechaza():
    repo, almacen = RepositorioEspia(), AlmacenEspia()
    caso = GuardarInforme(repo, almacen, TIPOS, 15 * 1024 * 1024, 10)
    with pytest.raises(InformeSinContenido):
        await caso.ejecutar(3, '   ', [], 7)


async def test_estudio_inexistente_no_acepta_informe():
    repo, almacen = RepositorioEspia(), AlmacenEspia()
    caso = GuardarInforme(repo, almacen, TIPOS, 15 * 1024 * 1024, 10)
    with pytest.raises(EstudioNoEncontrado):
        await caso.ejecutar(999, 'Texto', [
            {'nombre': 'a.png', 'mime': 'image/png', 'contenido': b'x'},
        ], 7)


async def test_no_se_sobreescribe_un_informe_ya_publicado():
    repo, almacen = RepositorioEspia(), AlmacenEspia()
    _con_informe(repo, estado='publicado')
    caso = GuardarInforme(repo, almacen, TIPOS, 15 * 1024 * 1024, 10)
    with pytest.raises(InformeYaPublicado):
        await caso.ejecutar(3, 'Otro texto', [
            {'nombre': 'a.png', 'mime': 'image/png', 'contenido': b'x'},
        ], 7)
    assert almacen.guardados == []


# ---------- publicacion ----------

def _con_informe(repo, estado='borrador'):
    repo.informe = InformeImagen(1, 3, 1, 'texto', estado, None, None, ())
    repo.publicado = estado == 'publicado'
    return repo


async def test_publicar_devuelve_el_informe_publicado():
    repo = _con_informe(RepositorioEspia())
    informe = await PublicarInforme(repo).ejecutar(3, 7)
    assert informe.estado == 'publicado'


async def test_publicar_sin_informe_previo_se_rechaza():
    repo = RepositorioEspia()  # sin informe cargado
    with pytest.raises(InformeSinContenido):
        await PublicarInforme(repo).ejecutar(3, 7)


async def test_publicar_dos_veces_se_rechaza():
    repo = _con_informe(RepositorioEspia())
    await PublicarInforme(repo).ejecutar(3, 7)
    with pytest.raises(InformeYaPublicado):
        await PublicarInforme(repo).ejecutar(3, 7)
