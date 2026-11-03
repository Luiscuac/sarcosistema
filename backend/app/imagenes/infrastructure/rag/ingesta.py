import json
from pathlib import Path

from app.imagenes.infrastructure.rag.corpus import extraer_articulo, fragmentar, verificar_documento


def cargar_corpus(carpeta: Path) -> list[tuple[dict, list[dict]]]:
    if not (carpeta / 'manifest.json').is_file():
        raise ValueError('Corpus médico no preparado; no se intentará descargarlo.')
    manifest = json.loads((carpeta / 'manifest.json').read_text(encoding='utf-8'))
    corpus = []
    for fuente in manifest['fuentes']:
        archivo = (carpeta / fuente['archivo']).resolve()
        if not archivo.is_relative_to(carpeta.resolve()):
            raise ValueError('Ruta documental no permitida.')
        articulo = extraer_articulo(verificar_documento(archivo, fuente['sha256']))
        contenido = ''
        fragmentos = []
        id = fuente['id'] + ':' + fuente['sha256'][:16]
        for seccion in articulo['secciones']:
            base = len(contenido)
            contenido += seccion['texto'] + '\n\n'
            for f in fragmentar(seccion['texto']):
                fragmentos.append({**f, 'id': f'{id}:{base+f["inicio"]}',
                    'seccion': seccion['seccion'], 'inicio': base+f['inicio'], 'fin': base+f['fin']})
        documento = {'id': id, 'titulo': articulo['titulo'], 'fuente': fuente['url'],
            'licencia': articulo['licencia'], 'categoria': fuente['categoria'],
            'version': fuente['extractor_version'], 'sha256': fuente['sha256'], 'contenido': contenido}
        corpus.append((documento, fragmentos))
    if not corpus:
        raise ValueError('Corpus local vacío.')
    return corpus
