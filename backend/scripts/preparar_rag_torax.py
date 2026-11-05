"""Preparación explícita online; nunca importar desde el runtime RAG."""
import argparse
import hashlib
import json
from pathlib import Path

from app.imagenes.infrastructure.rag.corpus import extraer_articulo
from app.imagenes.infrastructure.rag.embeddings import MODEL_ID
from app.imagenes.infrastructure.rag.ingesta import cargar_corpus

BASE = Path(__file__).resolve().parents[1]
SOURCES = ('PMC6958895', 'PMC4753987')


def validar_snapshot(carpeta: Path) -> dict[str, str]:
    archivos = [p for p in carpeta.rglob('*') if p.is_file() and '.cache' not in p.parts]
    nombres = {p.relative_to(carpeta).as_posix() for p in archivos}
    if not {'model.safetensors', 'config.json', 'tokenizer.json'} <= nombres:
        raise ValueError('Snapshot incompleto; requiere safetensors y tokenizer local.')
    if any(p.suffix in ('.py', '.bin', '.pt', '.pkl') for p in archivos):
        raise ValueError('No se permite código remoto ni pesos pickle.')
    return {p.relative_to(carpeta).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in archivos if p.name != 'manifest.json'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--descargar', action='store_true')
    parser.add_argument('--solo-documentos', action='store_true')
    args = parser.parse_args()
    if not args.descargar:
        raise SystemExit('Usar --descargar únicamente durante preparación online.')
    import httpx
    destino = BASE / '.datasets' / 'rag-torax'
    destino.mkdir(parents=True, exist_ok=True)
    manifest = destino / 'manifest.json'
    if manifest.exists():
        cargar_corpus(destino)
    else:
        fuentes = []
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            for id in SOURCES:
                url = f'https://www.ebi.ac.uk/europepmc/webservices/rest/{id}/fullTextXML'
                response = client.get(url)
                response.raise_for_status()
                articulo = extraer_articulo(response.content)
                archivo = destino / f'{id}.xml'
                if archivo.exists():
                    if archivo.read_bytes() != response.content:
                        raise ValueError('Fuente existente difiere; revisar antes de sobrescribir.')
                else:
                    archivo.write_bytes(response.content)
                fuentes.append({'id': id, 'archivo': archivo.name, 'sha256': hashlib.sha256(response.content).hexdigest(),
                                'url': f'https://pmc.ncbi.nlm.nih.gov/articles/{id}/', 'download_url': url,
                                'titulo': articulo['titulo'], 'licencia': articulo['licencia'],
                                'categoria': 'radiografia_torax', 'extractor_version': 'jats-paragraphs-v1'})
        manifest.write_text(json.dumps({'fuentes': fuentes}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Corpus médico preparado con licencia y SHA-256; no se añadieron datos clínicos.')
    if args.solo_documentos:
        return
    from huggingface_hub import HfApi, snapshot_download
    modelo = BASE / '.models' / 'rag-torax'
    if (modelo / 'manifest.json').exists():
        existente = json.loads((modelo/'manifest.json').read_text(encoding='utf-8'))
        if existente.get('model') != MODEL_ID or existente.get('files') != validar_snapshot(modelo):
            raise ValueError('Modelo existente incompatible o alterado; no se sobrescribió.')
        print('Modelo local existente verificado; no se descargó de nuevo.')
        return
    revision = HfApi().model_info(MODEL_ID).sha
    snapshot_download(MODEL_ID, revision=revision, local_dir=modelo,
                      allow_patterns=['*.json', '*.txt', '*.model', 'model.safetensors', '1_Pooling/*'],
                      max_workers=1)
    archivos = validar_snapshot(modelo)
    (modelo / 'manifest.json').write_text(json.dumps({'model': MODEL_ID, 'revision': revision,
        'dimension': 384, 'max_seq_length': 128, 'pooling': 'mean', 'license': 'Apache-2.0',
        'files': archivos}, indent=2), encoding='utf-8')
    print('Snapshot local preparado; ninguna consulta requiere descargarlo.')


if __name__ == '__main__':
    main()
