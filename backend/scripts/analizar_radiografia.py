"""Inferencia CLI local. No carga modelos al arrancar FastAPI ni descarga archivos."""
import argparse
import json
from pathlib import Path

from app.imagenes.application.use_cases.analizar_torax import AnalizarTorax
from app.imagenes.domain.vision import VisionConfig, ErrorVision, MAX_IMAGE_BYTES
from app.imagenes.infrastructure.vision.servicio import AnalizadorTorax


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('imagen', type=Path)
    parser.add_argument('--model-dir', type=Path, default=Path(__file__).resolve().parents[1] / '.models' / 'radiologia')
    parser.add_argument('--confirmar-torax-frontal', action='store_true', required=True,
                        help='Confirmación del operador, no una detección de modalidad por IA')
    parser.add_argument('--proyeccion', choices=['PA', 'AP', 'frontal_no_especificada'], required=True)
    parser.add_argument('--repeticiones', type=int, default=1)
    parser.add_argument('--min-free-mib', type=int, default=4096)
    parser.add_argument('--timeout', type=float, default=120)
    args = parser.parse_args()
    try:
        if not args.imagen.is_file() or args.imagen.stat().st_size > MAX_IMAGE_BYTES:
            raise ErrorVision('Archivo local ausente o superior a 10 MiB.')
        config = VisionConfig(args.model_dir, min_free_bytes=args.min_free_mib * 1024**2, timeout_seconds=args.timeout)
        datos = AnalizarTorax(AnalizadorTorax(config)).ejecutar(args.imagen.read_bytes(), args.proyeccion, args.repeticiones)
    except (ErrorVision, ValueError, OSError) as error:
        print(json.dumps({'ok': False, 'error': type(error).__name__, 'detail': str(error)}, ensure_ascii=True))
        raise SystemExit(2) from None
    print(json.dumps(datos, indent=2, ensure_ascii=True, allow_nan=False))


if __name__ == '__main__':
    main()
