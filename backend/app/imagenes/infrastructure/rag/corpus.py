"""Integridad y fragmentación local, sin imports de modelos ni acceso a red."""
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET
import re


def verificar_documento(archivo: Path, sha256: str, max_bytes: int = 8 * 1024**2) -> bytes:
    if archivo.stat().st_size > max_bytes:
        raise ValueError('Documento excede el límite de tamaño.')
    with archivo.open('rb') as stream:
        contenido = stream.read(max_bytes + 1)
    if len(contenido) > max_bytes or hashlib.sha256(contenido).hexdigest() != sha256:
        raise ValueError('Falló la integridad del documento local.')
    return contenido


def fragmentar(texto: str, max_caracteres: int = 400) -> list[dict]:
    if not texto.strip() or not 32 <= max_caracteres <= 2000:
        raise ValueError('Texto vacío o límite de fragmentación inválido.')
    fragmentos = []
    inicio = 0
    while inicio < len(texto):
        fin = min(inicio + max_caracteres, len(texto))
        if fin < len(texto):
            corte = texto.rfind(' ', inicio + max_caracteres // 2, fin)
            if corte != -1:
                fin = corte + 1
        fragmentos.append({'texto': texto[inicio:fin], 'inicio': inicio, 'fin': fin})
        inicio = fin
    return fragmentos


def extraer_articulo(contenido: bytes) -> dict:
    if len(contenido) > 8 * 1024**2 or b'<!DOCTYPE' in contenido.upper() or b'<!ENTITY' in contenido.upper():
        raise ValueError('XML no permitido o demasiado grande.')
    root = ET.fromstring(contenido)
    licencia = ' '.join(' '.join(e.itertext()) for e in root.findall('.//permissions/license'))
    permiso = ' '.join(licencia.lower().split())
    reconocido = ('creative commons attribution-noncommercial-sharealike 4.0' in permiso
                  or 'permits unrestricted noncommercial use' in permiso)
    if not reconocido or re.search(r'\bnot\b|\bno permission\b|\bprohibited\b', permiso):
        raise ValueError('No se encontró una licencia de uso local permitida.')
    titulo = root.find('.//article-title')
    secciones = []
    def recorrer(nodo, ruta):
        encabezado = nodo.find('title')
        if encabezado is not None:
            ruta = ruta + [''.join(encabezado.itertext()).strip()]
        for hijo in nodo:
            if hijo.tag == 'p':
                texto = ''.join(hijo.itertext()).strip()
                if texto:
                    secciones.append({'seccion': ' / '.join(ruta) or 'Cuerpo', 'texto': texto})
            elif hijo.tag == 'sec':
                recorrer(hijo, ruta)
    body = root.find('body')
    if body is None:
        raise ValueError('Artículo sin cuerpo documental.')
    recorrer(body, [])
    if not secciones or titulo is None:
        raise ValueError('Artículo sin texto o título verificable.')
    return {'titulo': ''.join(titulo.itertext()).strip(), 'licencia': licencia, 'secciones': secciones}
