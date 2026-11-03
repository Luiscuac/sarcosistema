import multiprocessing
from pathlib import Path
import tempfile
import time

from app.imagenes.domain.vision import (
    ErrorVision, ImagenNoValida, ModeloNoPreparado, RecursosInsuficientes, TiempoAgotado,
    VisionConfig, MAX_IMAGE_BYTES,
)
from app.imagenes.infrastructure.vision.artefactos import comprobar_artefactos
from app.imagenes.infrastructure.vision.recursos import verificar_memoria, bloqueo_inferencia


class AnalizadorTorax:
    """Puerto visual reutilizable; una solicitud, hijo efímero y timeout real."""
    def __init__(self, config: VisionConfig):
        self.config = config

    def analizar(self, contenido: bytes, proyeccion: str = 'PA', repeticiones: int = 1) -> dict:
        if proyeccion not in ('PA', 'AP', 'frontal_no_especificada') or not 1 <= repeticiones <= 3:
            raise ValueError('Solo tórax frontal declarado AP/PA y de una a tres repeticiones de evaluación.')
        if not contenido or len(contenido) > MAX_IMAGE_BYTES:
            raise ImagenNoValida('Imagen vacía o superior a 10 MiB.')
        comprobar_artefactos(self.config.model_dir)
        verificar_memoria(self.config.min_free_bytes)
        # El lock está fuera de los artefactos: estos pueden montarse solo lectura.
        with bloqueo_inferencia(Path(tempfile.gettempdir())):
            return self._ejecutar(contenido, proyeccion, repeticiones)

    def _ejecutar(self, contenido, proyeccion, repeticiones):
        from app.imagenes.infrastructure.vision.worker import ejecutar_worker
        import psutil
        contexto = multiprocessing.get_context('spawn')
        receptor, emisor = contexto.Pipe(duplex=False)
        proceso = contexto.Process(target=ejecutar_worker,
            args=(emisor, contenido, self.config, proyeccion, repeticiones), daemon=True)
        inicio = time.perf_counter()
        pico = 0
        mensaje = None
        try:
            proceso.start()
            emisor.close()
            while True:
                if time.perf_counter() - inicio > self.config.timeout_seconds:
                    raise TiempoAgotado('El análisis visual agotó su tiempo y se detuvo su trabajador. Puedes continuar sin IA.')
                try:
                    pico = max(pico, psutil.Process(proceso.pid).memory_info().rss)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                if receptor.poll(0.02):
                    try:
                        mensaje = receptor.recv()
                    except EOFError:
                        pass
                    break
                if not proceso.is_alive():
                    break
            if not mensaje:
                raise ErrorVision('El trabajador terminó sin resultado; revisa RAM y dependencias.')
            if not mensaje['ok']:
                tipos = {'ImagenNoValida': ImagenNoValida, 'ModeloNoPreparado': ModeloNoPreparado,
                         'RecursosInsuficientes': RecursosInsuficientes}
                raise tipos.get(mensaje['kind'], ErrorVision)(mensaje['message'])
            resultado = mensaje['result']
            resultado['metrics']['worker_peak_rss_bytes_observed'] = max(pico, resultado['metrics']['worker_rss_at_end_bytes'])
            resultado['metrics']['end_to_end_seconds'] = time.perf_counter() - inicio
            return resultado
        finally:
            # Incluso ante Ctrl+C/timeout, no queda un modelo pesado indefinidamente.
            if proceso.pid is not None:
                proceso.join(timeout=1)
                if proceso.is_alive():
                    proceso.terminate()
                    proceso.join(timeout=5)
                if proceso.is_alive():
                    # En POSIX SIGTERM puede ignorarse; SIGKILL/TerminateProcess no.
                    proceso.kill()
                    proceso.join()
                proceso.close()
            receptor.close()
            emisor.close()
