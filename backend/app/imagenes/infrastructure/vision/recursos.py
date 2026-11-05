from contextlib import contextmanager
import os
from pathlib import Path

from app.imagenes.domain.vision import RecursosInsuficientes, InferenciaOcupada


def memoria_disponible() -> int:
    try:
        import psutil
    except ImportError:
        raise RecursosInsuficientes('Instala las dependencias opcionales de radiología antes de analizar.') from None
    disponible = psutil.virtual_memory().available
    # psutil puede ver RAM del host dentro de Docker: respetar también cgroup v2.
    try:
        limite = Path('/sys/fs/cgroup/memory.max').read_text().strip()
        if limite != 'max':
            usada = int(Path('/sys/fs/cgroup/memory.current').read_text().strip())
            disponible = min(disponible, max(0, int(limite) - usada))
    except (OSError, ValueError):
        pass
    return disponible


def verificar_memoria(minimo: int, disponible: int | None = None) -> int:
    libre = memoria_disponible() if disponible is None else disponible
    if libre < minimo:
        raise RecursosInsuficientes('RAM libre insuficiente para visión. Libera memoria y vuelve a intentarlo; no se cargó el modelo.')
    return libre


@contextmanager
def bloqueo_inferencia(carpeta: Path):
    # Lock compartido por procesos que usen esta carpeta; archivo sin contenido clínico.
    path = Path(carpeta) / '.inferencia.lock'
    archivo = path.open('a+b')
    bloqueado = False
    try:
        if archivo.tell() == 0:
            archivo.write(b'0')
            archivo.flush()
        archivo.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(archivo.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(archivo.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            bloqueado = True
        except OSError:
            raise InferenciaOcupada('Ya hay una inferencia visual en ejecución. Reintenta al terminar.') from None
        yield
    finally:
        if bloqueado:
            archivo.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(archivo.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(archivo.fileno(), fcntl.LOCK_UN)
        archivo.close()
