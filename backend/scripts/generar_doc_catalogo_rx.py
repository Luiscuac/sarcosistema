"""Genera docs/imagenes/radiologia-convencional-catalogo.md desde el catalogo de dominio.

Uso (desde backend/):  .venv\\Scripts\\python.exe scripts\\generar_doc_catalogo_rx.py
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.imagenes.domain.catalogo_radiologia import (  # noqa: E402
    CAMPOS_GENERALES, CATEGORIAS, ESTUDIOS, PLANTILLAS, PROYECCIONES, VERSION_CATALOGO, validar_catalogo,
)

DESTINO = Path(__file__).resolve().parents[2] / 'docs' / 'imagenes' / 'radiologia-convencional-catalogo.md'


def _lateralidad(estudio) -> str:
    if not estudio.requiere_lateralidad:
        return 'No aplica'
    return 'Derecha / izquierda / bilateral' if estudio.permite_bilateral else 'Derecha / izquierda'


def generar() -> str:
    errores = validar_catalogo()
    if errores:
        raise SystemExit('Catálogo inválido:\n' + '\n'.join(errores))
    lineas = [
        '# Catálogo de radiología convencional',
        '',
        f'> Generado desde `backend/app/imagenes/domain/catalogo_radiologia.py` (versión {VERSION_CATALOGO}). '
        'No editar a mano: modificar el catálogo y volver a ejecutar `scripts/generar_doc_catalogo_rx.py`.',
        '',
        'Orientativo: cada centro debe validar con su servicio de radiología qué estudios y protocolos habilita según su equipamiento.',
        '',
        '## Campos generales de todo informe',
        '',
        '| Campo | Uso |', '|---|---|',
    ]
    lineas += [f'| {c.titulo} | {c.ayuda} |' for c in CAMPOS_GENERALES]
    lineas += ['', 'Solo la **conclusión** es obligatoria para validar. Los apartados de cada plantilla son guías de lectura opcionales.', '']
    lineas += ['## Matriz de estudios', '',
               '| Código | Estudio | Categoría | Lateralidad | Proyecciones aplicables | Protocolos | Plantilla | Fuente |',
               '|---|---|---|---|---|---|---|---|']
    for e in ESTUDIOS:
        proyecciones = ', '.join(PROYECCIONES[p].nombre for p in e.proyecciones)
        protocolos = '; '.join(p.nombre for p in e.protocolos)
        lineas.append(f'| `{e.codigo}` | {e.nombre} | {CATEGORIAS[e.categoria]} | {_lateralidad(e)} | {proyecciones} | '
                      f'{protocolos} | {PLANTILLAS[e.plantilla].nombre} | {e.fuente} |')
    lineas += ['', '## Notas y datos adicionales por estudio', '']
    for e in ESTUDIOS:
        extra = [*(['Dato requerido en la solicitud: ' + e.detalle_requerido] if e.detalle_requerido else []), *e.notas]
        if e.descripcion or extra:
            lineas.append(f'- **{e.nombre}** (`{e.codigo}`): {e.descripcion} {" ".join(extra)}'.rstrip())
    lineas += ['', '## Plantillas de evaluación', '']
    for p in PLANTILLAS.values():
        usados = ', '.join(e.nombre for e in ESTUDIOS if e.plantilla == p.codigo)
        lineas += [f'### {p.nombre} (`{p.codigo}`)', '', f'Estudios: {usados}.', '', '| Apartado | Tipo | Guía |', '|---|---|---|']
        for c in p.campos:
            tipo = {'texto': 'Descriptivo', 'opcion': 'Selector: ' + ' / '.join(c.opciones),
                    'medicion': f'Medición{f" ({c.unidad})" if c.unidad else ""}, opcional'}[c.tipo]
            lineas.append(f'| {c.titulo} | {tipo} | {c.ayuda} |')
        lineas.append('')
    return '\n'.join(lineas) + '\n'


if __name__ == '__main__':
    DESTINO.write_text(generar(), encoding='utf-8')
    print(f'Escrito {DESTINO}')
