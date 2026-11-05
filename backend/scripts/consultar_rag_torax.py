"""CLI local: ingesta explícita o consulta documental, sin endpoints clínicos."""
import argparse
import asyncio
import json
from pathlib import Path

from app.imagenes.application.consultar_rag import responder_con_evidencia
from app.imagenes.infrastructure.rag.embeddings import EmbeddingsLocales
from app.imagenes.infrastructure.rag.ingesta import cargar_corpus
from app.imagenes.infrastructure.rag.repository import RepositorioRag

BASE = Path(__file__).resolve().parents[1]


async def ejecutar(args):
    # Validar fuentes en disco incluso al consultar: no aceptar corpus alterado.
    corpus = cargar_corpus(args.corpus_dir)
    manifest = json.loads((args.model_dir / 'manifest.json').read_text(encoding='utf-8'))
    modelo_id = manifest['model'] + '@' + manifest['revision']
    embeddings = EmbeddingsLocales(args.model_dir, min_free_bytes=args.min_free_mib*1024**2)
    from app.config.database import SessionLocal, engine
    try:
        async with SessionLocal.begin() as session:
            repo = RepositorioRag(session)
            if args.indexar:
                for documento, fragmentos in corpus:
                    vectores = []
                    for inicio in range(0, len(fragmentos), 128):
                        vectores.extend(embeddings.codificar([f['texto'] for f in fragmentos[inicio:inicio+128]]))
                    await repo.ingestar(documento, fragmentos, vectores, modelo_id)
                return {'estado': 'indexado', 'documentos': len(corpus)}
            vector = embeddings.codificar([args.pregunta], consulta=True)[0]
            recuperados = await repo.buscar(vector, modelo_id, limite=10)
            documentos = {d['id']: d for d, _ in corpus}
            verificados = [e for e in recuperados if e['documento_id'] in documentos
                and e['sha256'] == documentos[e['documento_id']]['sha256']
                and e['contenido'] == documentos[e['documento_id']]['contenido']]
            return responder_con_evidencia(args.pregunta, verificados)
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    accion = parser.add_mutually_exclusive_group(required=True)
    accion.add_argument('--indexar', action='store_true')
    accion.add_argument('--pregunta')
    parser.add_argument('--model-dir', type=Path, default=BASE / '.models' / 'rag-torax')
    parser.add_argument('--corpus-dir', type=Path, default=BASE / '.datasets' / 'rag-torax')
    parser.add_argument('--min-free-mib', type=int, default=2048)
    args = parser.parse_args()
    try:
        resultado = asyncio.run(ejecutar(args))
    except (ValueError, OSError) as error:
        print(json.dumps({'estado': 'error', 'tipo': type(error).__name__,
                          'mensaje': 'Revisar preparación local, integridad y recursos; no se descargó nada.'}))
        raise SystemExit(1) from None
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
