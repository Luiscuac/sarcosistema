"""Catalogo inicial de radiologia convencional: estudios, protocolos, proyecciones y plantillas.

Fuente unica de verdad para sembrar la base de datos, generar la documentacion
(docs/imagenes/radiologia-convencional.md) y construir los formularios.

Distincion de conceptos:
- Estudio: lo que se solicita y se informa (p. ej. "Radiografia de rodilla"). Un estudio
  por region anatomica; la lateralidad es un dato de la solicitud, no un estudio distinto.
- Protocolo: conjunto habitual de proyecciones para una indicacion (p. ej. "PA y lateral").
- Proyeccion: una exposicion concreta (PA, lateral, oblicua...). Las solicitadas no implican
  que se realizaran: el tecnico registra las realizadas por separado.

Las plantillas son guias de lectura. Ningun apartado es obligatorio salvo la conclusion al
validar, y nada se completa automaticamente: las frases sugeridas solo se insertan si el
medico las elige explicitamente.

Referencias generales (ver docs para detalle):
- ACR Practice Parameter for Communication of Diagnostic Imaging Findings (estructura del informe).
- ACR-SPR-STR Practice Parameter for the Performance of Chest Radiography.
- ACR-ASSR-SPR-SSR Practice Parameter for the Performance of Spine Radiography.
- ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities.
- ACR-AAPM-SIIM-SPR Practice Parameter for Digital Radiography.
- RSNA RadReport (plantillas estructuradas, p. ej. "Chest Xray").
- IEC 62494-1 / DICOM PS3.3 Exposure Index Macro (indice de exposicion EI/DI).
- Textos de posicionamiento radiografico (Bontrager; Merrill) para proyecciones habituales.
Las proyecciones y protocolos son orientativos y deben ser validados por el servicio de
radiologia de cada centro, que puede deshabilitar los que su equipamiento no permita.
"""
from __future__ import annotations

from dataclasses import dataclass, field

VERSION_CATALOGO = 1

LATERALIDADES = ('derecha', 'izquierda', 'bilateral')
TIPOS_CAMPO = ('texto', 'opcion', 'medicion')


@dataclass(frozen=True, slots=True)
class Proyeccion:
    codigo: str
    nombre: str


@dataclass(frozen=True, slots=True)
class Protocolo:
    codigo: str
    nombre: str
    proyecciones: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Campo:
    """Apartado de evaluacion de la plantilla."""

    clave: str
    titulo: str
    tipo: str = 'texto'
    ayuda: str = ''
    frases: tuple[str, ...] = ()
    opciones: tuple[str, ...] = ()
    unidad: str = ''
    minimo: float | None = None
    maximo: float | None = None


@dataclass(frozen=True, slots=True)
class Plantilla:
    codigo: str
    nombre: str
    campos: tuple[Campo, ...]


@dataclass(frozen=True, slots=True)
class EstudioRadiologico:
    codigo: str
    nombre: str
    categoria: str
    region: str
    descripcion: str
    plantilla: str
    proyecciones: tuple[str, ...]
    protocolos: tuple[Protocolo, ...]
    requiere_lateralidad: bool = False
    permite_bilateral: bool = True
    detalle_requerido: str = ''
    fuente: str = ''
    notas: tuple[str, ...] = field(default_factory=tuple)


CATEGORIAS = {
    'torax': 'Tórax',
    'abdomen': 'Abdomen',
    'columna': 'Columna vertebral',
    'pelvis_cadera': 'Pelvis y cadera',
    'extremidad_superior': 'Extremidades superiores',
    'extremidad_inferior': 'Extremidades inferiores',
    'craneo_cara': 'Cráneo y estructuras faciales',
    'cuello': 'Cuello y partes blandas',
}

PROYECCIONES = {p.codigo: p for p in (
    Proyeccion('PA', 'Posteroanterior (PA)'),
    Proyeccion('AP', 'Anteroposterior (AP)'),
    Proyeccion('LAT', 'Lateral'),
    Proyeccion('OBL', 'Oblicua'),
    Proyeccion('OBL_INT', 'Oblicua interna'),
    Proyeccion('OBL_EXT', 'Oblicua externa'),
    Proyeccion('OBL_DER', 'Oblicua derecha'),
    Proyeccion('OBL_IZQ', 'Oblicua izquierda'),
    Proyeccion('AP_SUPINO', 'AP en decúbito supino'),
    Proyeccion('AP_BIPEDESTACION', 'AP en bipedestación'),
    Proyeccion('DECUBITO_LATERAL', 'Decúbito lateral con rayo horizontal'),
    Proyeccion('LORDOTICA', 'AP lordótica (vértices)'),
    Proyeccion('OAD', 'Oblicua anterior derecha (OAD)'),
    Proyeccion('AP_TRANSORAL', 'AP transoral (C1-C2, boca abierta)'),
    Proyeccion('NADADOR', 'Lateral de nadador (cervicotorácica)'),
    Proyeccion('FLEXION', 'Lateral en flexión'),
    Proyeccion('EXTENSION', 'Lateral en extensión'),
    Proyeccion('L5S1', 'Lateral focalizada L5-S1'),
    Proyeccion('AP_AXIAL', 'AP axial (angulada)'),
    Proyeccion('RANA', 'Lateral en rana (Lauenstein)'),
    Proyeccion('AXIAL_CADERA', 'Axial lateral de cadera (rayo horizontal)'),
    Proyeccion('AP_ROT_INT', 'AP en rotación interna'),
    Proyeccion('AP_ROT_EXT', 'AP en rotación externa'),
    Proyeccion('GRASHEY', 'AP verdadera de glenoides (Grashey)'),
    Proyeccion('AXILAR', 'Axilar'),
    Proyeccion('Y_ESCAPULAR', 'Lateral en Y escapular'),
    Proyeccion('PA_ESCAFOIDES', 'PA con desviación cubital (escafoides)'),
    Proyeccion('TUNEL', 'Túnel intercondíleo'),
    Proyeccion('AXIAL_ROTULA', 'Axial de rótula (Merchant / sol naciente)'),
    Proyeccion('MORTAJA', 'AP de mortaja'),
    Proyeccion('AP_DP', 'Dorsoplantar (AP de pie)'),
    Proyeccion('AXIAL_CALCANEO', 'Axial de calcáneo (plantodorsal)'),
    Proyeccion('CARGA', 'Con carga (bipedestación)'),
    Proyeccion('CALDWELL', 'PA de Caldwell'),
    Proyeccion('WATERS', 'Occipitomentoniana (Waters)'),
    Proyeccion('TOWNE', 'AP axial de Towne'),
    Proyeccion('SMV', 'Submentovértice'),
)}

# ---------------------------------------------------------------------------
# Campos generales: forman parte de toda plantilla (estructura recomendada por el ACR).
# ---------------------------------------------------------------------------
CAMPOS_GENERALES = (
    Campo('tecnica', 'Técnica', ayuda='Proyecciones realizadas y condiciones del estudio. Se propone desde la adquisición registrada y es editable.'),
    Campo('indicacion', 'Indicación clínica', ayuda='Motivo del examen según la solicitud. Editable.'),
    Campo('comparacion', 'Comparación', ayuda='Estudios previos comparados con su fecha, o indique que no hay estudios previos disponibles.',
          frases=('No se dispone de estudios previos para comparación.',)),
    Campo('limitaciones', 'Limitaciones técnicas', ayuda='Rotación, inspiración insuficiente, movimiento, superposición, proyecciones no obtenidas.'),
    Campo('conclusion', 'Conclusión / impresión diagnóstica', ayuda='Obligatoria para validar. Redáctela usted; el sistema no propone diagnósticos.'),
    Campo('recomendaciones', 'Recomendaciones', ayuda='Solo cuando correspondan (correlación clínica, estudio complementario, control).'),
)
CLAVES_GENERALES = tuple(c.clave for c in CAMPOS_GENERALES)

_SIN_ALTERACIONES = 'Sin alteraciones radiológicas evidentes en este apartado.'


def _c(clave: str, titulo: str, ayuda: str = '', *frases: str) -> Campo:
    return Campo(clave, titulo, ayuda=ayuda, frases=frases or (_SIN_ALTERACIONES,))


_OTROS = _c('otros', 'Otros hallazgos', 'Hallazgos incidentales o fuera de los apartados anteriores.')
_PARTES_BLANDAS = _c('partes_blandas', 'Partes blandas', 'Aumento de volumen, gas, calcificaciones o cuerpos extraños radiopacos.')
_MATERIAL = _c('material', 'Material de osteosíntesis / dispositivos', 'Posición e integridad del material; aflojamiento o rotura.',
               'No se observa material de osteosíntesis.')

# ---------------------------------------------------------------------------
# Plantillas de evaluacion por familia anatomica
# ---------------------------------------------------------------------------
PLANTILLAS = {p.codigo: p for p in (
    Plantilla('torax', 'Tórax', (
        _c('campos_pulmonares', 'Campos pulmonares', 'Opacidades, consolidación, nódulos, patrón intersticial, hiperinsuflación.',
           'Campos pulmonares sin opacidades focales.'),
        _c('silueta_cardiomediastinica', 'Silueta cardiomediastínica', 'Tamaño y contornos cardíacos; valorar con cautela en proyección AP.'),
        Campo('indice_cardiotoracico', 'Índice cardiotorácico', tipo='medicion', unidad='', minimo=0.2, maximo=0.9,
              ayuda='Opcional. Solo interpretable en PA de buena calidad.'),
        _c('mediastino_hilios', 'Mediastino e hilios', 'Ensanchamiento, desviación traqueal, adenopatías hiliares.'),
        _c('pleura', 'Pleuras y senos costofrénicos', 'Derrame, engrosamiento, neumotórax.',
           'Senos costofrénicos libres.'),
        _c('diafragma', 'Diafragma y espacio subdiafragmático', 'Elevación, aire libre subdiafragmático.'),
        _c('osea', 'Estructuras óseas y partes blandas', 'Fracturas costales, lesiones líticas o blásticas, enfisema subcutáneo.'),
        _c('dispositivos', 'Dispositivos y catéteres', 'Tubos, catéteres, marcapasos: tipo y posición.',
           'No se observan dispositivos.'),
        _OTROS,
    )),
    Plantilla('parrilla_costal', 'Parrilla costal y esternón', (
        _c('arcos_costales', 'Arcos costales', 'Trazos de fractura, desplazamiento, callos, lesiones focales.'),
        _c('esternon', 'Esternón', 'Integridad cortical, alineación de segmentos, articulaciones esternoclaviculares.'),
        _c('pleura_pulmon', 'Pleura y pulmón visibles', 'Neumotórax, derrame o contusión asociados.'),
        _PARTES_BLANDAS, _OTROS,
    )),
    Plantilla('abdomen', 'Abdomen', (
        _c('gas_intestinal', 'Distribución del gas intestinal', 'Patrón inespecífico, ausencia de gas distal, gas en recto.'),
        _c('dilatacion_asas', 'Dilatación de asas', 'Intestino delgado o colon; calibre y distribución.'),
        Campo('calibre_maximo', 'Calibre máximo de asa', tipo='medicion', unidad='cm', minimo=0, maximo=20,
              ayuda='Opcional; indique el segmento medido en el texto.'),
        _c('niveles_hidroaereos', 'Niveles hidroaéreos', 'Solo evaluables en bipedestación o decúbito con rayo horizontal. Indique si la técnica no lo permite.'),
        _c('aire_libre', 'Aire libre / neumoperitoneo', 'Requiere técnica con rayo horizontal o tórax de pie.'),
        _c('calcificaciones', 'Calcificaciones', 'Litiasis renal o biliar, calcificaciones vasculares o pancreáticas.'),
        _c('cuerpos_extranos', 'Cuerpos extraños', 'Radiopacos: tipo y localización.', 'No se observan cuerpos extraños radiopacos.'),
        _c('organos_solidos', 'Siluetas de órganos sólidos y psoas', 'Hepatomegalia, esplenomegalia, borramiento del psoas.'),
        _c('osea', 'Estructuras óseas visibles', 'Columna lumbar y pelvis visibles.'),
        _OTROS,
    )),
    Plantilla('columna', 'Columna vertebral', (
        _c('alineacion', 'Alineación vertebral', 'Listesis, escoliosis, alineación de líneas espinales.'),
        _c('curvatura', 'Curvatura', 'Lordosis/cifosis fisiológica, rectificación o acentuación.'),
        Campo('angulo_cobb', 'Ángulo de Cobb', tipo='medicion', unidad='°', minimo=0, maximo=120,
              ayuda='Opcional; indique los niveles medidos en el texto.'),
        _c('cuerpos_vertebrales', 'Altura y morfología de cuerpos vertebrales', 'Acuñamientos, aplastamientos, lesiones focales.'),
        _c('espacios_discales', 'Espacios intervertebrales', 'Disminución de altura, vacío discal.'),
        _c('degenerativos', 'Cambios degenerativos', 'Osteofitos, esclerosis de platillos, artrosis facetaria.'),
        _c('elementos_posteriores', 'Pedículos y elementos posteriores', 'Integridad de pedículos, espondilólisis (en oblicuas).'),
        _c('lesiones_oseas', 'Lesiones óseas', 'Líticas, blásticas o fracturas.'),
        _PARTES_BLANDAS, _MATERIAL, _OTROS,
    )),
    Plantilla('pelvis_cadera', 'Pelvis y cadera', (
        _c('alineacion', 'Alineación y relaciones articulares', 'Congruencia coxofemoral, sínfisis y sacroilíacas.'),
        _c('integridad_osea', 'Integridad ósea', 'Fracturas de cuello femoral, trocantéricas, ramas pubianas, acetábulo.'),
        _c('espacio_articular', 'Espacio articular coxofemoral', 'Pinzamiento, simetría.'),
        _c('degenerativos', 'Cambios degenerativos', 'Osteofitos, esclerosis subcondral, quistes.'),
        _c('cabeza_femoral', 'Cabeza femoral', 'Esfericidad, densidad (necrosis avascular), epífisis en pediatría.'),
        _c('lesiones_oseas', 'Lesiones óseas focales', ''),
        _PARTES_BLANDAS, _MATERIAL, _OTROS,
    )),
    Plantilla('articulacion', 'Articulación periférica', (
        _c('alineacion', 'Alineación ósea y relaciones articulares', 'Luxación, subluxación, congruencia.'),
        _c('integridad_osea', 'Integridad de estructuras óseas', 'Trazos de fractura, desplazamiento, angulación, conminución.'),
        _c('espacios_articulares', 'Espacios articulares', 'Pinzamiento, simetría compartimental.'),
        _c('degenerativos', 'Cambios degenerativos', 'Osteofitos, esclerosis subcondral, geodas.'),
        _c('derrame', 'Derrame articular', 'Signos indirectos de derrame (p. ej. almohadillas grasas).'),
        _c('lesiones_oseas', 'Lesiones óseas focales', ''),
        _PARTES_BLANDAS, _MATERIAL, _OTROS,
    )),
    Plantilla('hueso_largo', 'Hueso largo', (
        _c('alineacion', 'Alineación', 'Angulación, rotación, acortamiento.'),
        _c('cortical_medular', 'Cortical y medular', 'Trazos de fractura, reacción perióstica, lesiones focales.'),
        _c('articulaciones_adyacentes', 'Articulaciones proximal y distal', 'Incluidas en el estudio: relaciones articulares.'),
        _PARTES_BLANDAS, _MATERIAL, _OTROS,
    )),
    Plantilla('mano_pie', 'Mano / pie', (
        _c('alineacion', 'Alineación y relaciones articulares', 'Luxaciones, deformidades (hallux valgus, desviación cubital).'),
        _c('integridad_osea', 'Integridad ósea', 'Fracturas de falanges, metacarpianos/metatarsianos, huesos del carpo/tarso.'),
        _c('espacios_articulares', 'Espacios articulares', 'Pinzamiento, erosiones.'),
        _c('degenerativos_inflamatorios', 'Cambios degenerativos o inflamatorios', 'Osteofitos, erosiones, osteopenia periarticular.'),
        _c('densidad_osea', 'Densidad ósea', ''),
        _PARTES_BLANDAS, _MATERIAL, _OTROS,
    )),
    Plantilla('craneo', 'Cráneo', (
        _c('boveda', 'Bóveda craneal', 'Trazos de fractura, lesiones líticas o blásticas, suturas.'),
        _c('base_silla', 'Base de cráneo y silla turca', ''),
        _c('calcificaciones', 'Calcificaciones intracraneales visibles', ''),
        _PARTES_BLANDAS, _OTROS,
    )),
    Plantilla('senos_paranasales', 'Senos paranasales', (
        _c('maxilares', 'Senos maxilares', 'Neumatización, engrosamiento mucoso, niveles hidroaéreos (solo en bipedestación), opacificación.'),
        _c('frontales', 'Senos frontales', ''),
        _c('etmoidales', 'Celdillas etmoidales', ''),
        _c('esfenoidal', 'Seno esfenoidal', 'Mejor valorado en lateral.'),
        _c('tabique_cornetes', 'Tabique nasal y cornetes', 'Desviación, hipertrofia.'),
        _c('paredes_oseas', 'Paredes óseas', 'Integridad, erosión.'),
        _OTROS,
    )),
    Plantilla('huesos_nasales', 'Huesos nasales', (
        _c('integridad', 'Integridad de huesos nasales', 'Trazos de fractura, desplazamiento, hundimiento.'),
        _c('espina_nasal', 'Espina nasal anterior y tabique', ''),
        _PARTES_BLANDAS, _OTROS,
    )),
    Plantilla('huesos_faciales', 'Huesos faciales', (
        _c('orbitas', 'Órbitas', 'Rebordes orbitarios, suelo de órbita.'),
        _c('cigomaticos', 'Arcos y huesos cigomáticos', ''),
        _c('maxilar_mandibula', 'Maxilar y mandíbula', 'Trazos de fractura, cóndilos.'),
        _c('senos', 'Senos maxilares', 'Hemoseno, nivel hidroaéreo en contexto traumático.'),
        _PARTES_BLANDAS, _OTROS,
    )),
    Plantilla('edad_osea', 'Edad ósea', (
        Campo('edad_cronologica', 'Edad cronológica', tipo='medicion', unidad='años', minimo=0, maximo=20),
        Campo('edad_osea', 'Edad ósea estimada', tipo='medicion', unidad='años', minimo=0, maximo=20),
        Campo('metodo', 'Método', tipo='opcion', opciones=('Greulich y Pyle', 'Tanner-Whitehouse (TW3)', 'Otro')),
        _c('nucleos_osificacion', 'Núcleos de osificación y fisis', 'Descripción de núcleos y estado de cartílagos de crecimiento.'),
        _OTROS,
    )),
    Plantilla('cuello_partes_blandas', 'Partes blandas de cuello / cavum', (
        _c('via_aerea', 'Vía aérea', 'Calibre traqueal y de la columna aérea faríngea.'),
        _c('adenoides', 'Tejido adenoideo', 'Relación adenoides-nasofaringe (opcional: cociente A/N).'),
        Campo('cociente_an', 'Cociente adenoides/nasofaringe', tipo='medicion', minimo=0, maximo=1.5,
              ayuda='Opcional (método de Fujioka).'),
        _c('prevertebral', 'Partes blandas prevertebrales', 'Grosor prevertebral.'),
        _c('cuerpos_extranos', 'Cuerpos extraños', '', 'No se observan cuerpos extraños radiopacos.'),
        _OTROS,
    )),
)}


def _p(codigo: str, nombre: str, *proyecciones: str) -> Protocolo:
    return Protocolo(codigo, nombre, proyecciones)


_ACR_TORAX = 'ACR-SPR-STR Practice Parameter for the Performance of Chest Radiography; RSNA RadReport "Chest Xray".'
_ACR_COLUMNA = 'ACR-ASSR-SPR-SSR Practice Parameter for the Performance of Spine Radiography.'
_ACR_EXTREMIDADES = 'ACR-SPR-SSR Practice Parameter for the Performance of Radiography of the Extremities; posicionamiento estándar (Bontrager, Merrill).'
_POSICIONAMIENTO = 'Posicionamiento radiográfico estándar (Bontrager; Merrill).'

ESTUDIOS: tuple[EstudioRadiologico, ...] = (
    # --- Torax -------------------------------------------------------------
    EstudioRadiologico('RX_TORAX', 'Radiografía de tórax', 'torax', 'Tórax',
        'Evaluación de pulmones, corazón, mediastino, pleura y estructuras óseas del tórax.', 'torax',
        ('PA', 'LAT', 'AP', 'AP_SUPINO', 'LORDOTICA', 'DECUBITO_LATERAL'),
        (_p('PA', 'PA', 'PA'), _p('AP', 'AP (paciente que no puede ponerse de pie / portátil)', 'AP'),
         _p('PA_LAT', 'PA y lateral', 'PA', 'LAT')),
        fuente=_ACR_TORAX,
        notas=('La proyección AP magnifica la silueta cardíaca; indíquelo al valorar su tamaño.',)),
    EstudioRadiologico('RX_COSTILLAS', 'Radiografía de parrilla costal', 'torax', 'Costillas',
        'Evaluación de arcos costales, habitualmente por traumatismo.', 'parrilla_costal',
        ('AP', 'PA', 'OBL'), (_p('UNILATERAL', 'AP/PA y oblicua del lado afectado', 'AP', 'OBL'),),
        requiere_lateralidad=True, detalle_requerido='Arcos superiores o inferiores al diafragma, si se conoce.',
        fuente=_POSICIONAMIENTO, notas=('Suele acompañarse de una PA de tórax para descartar neumotórax.',)),
    EstudioRadiologico('RX_ESTERNON', 'Radiografía de esternón', 'torax', 'Esternón',
        'Evaluación del esternón, habitualmente por traumatismo.', 'parrilla_costal',
        ('OAD', 'LAT'), (_p('OAD_LAT', 'Oblicua anterior derecha y lateral', 'OAD', 'LAT'),), fuente=_POSICIONAMIENTO),
    # --- Abdomen -----------------------------------------------------------
    EstudioRadiologico('RX_ABDOMEN', 'Radiografía de abdomen simple', 'abdomen', 'Abdomen',
        'Evaluación del patrón de gas intestinal, calcificaciones y cuerpos extraños.', 'abdomen',
        ('AP_SUPINO', 'AP_BIPEDESTACION', 'DECUBITO_LATERAL', 'PA'),
        (_p('SUPINO', 'Decúbito supino', 'AP_SUPINO'), _p('BIPEDESTACION', 'De pie', 'AP_BIPEDESTACION'),
         _p('DECUBITO', 'Decúbito lateral con rayo horizontal', 'DECUBITO_LATERAL'),
         _p('ABDOMEN_AGUDO', 'Serie de abdomen agudo (supino, de pie y PA de tórax)', 'AP_SUPINO', 'AP_BIPEDESTACION', 'PA')),
        detalle_requerido='Protocolo indicado por el médico solicitante.',
        fuente='ACR Appropriateness Criteria (dolor abdominal, obstrucción); ' + _POSICIONAMIENTO,
        notas=('Los niveles hidroaéreos y el aire libre solo se valoran con rayo horizontal.',)),
    # --- Columna -----------------------------------------------------------
    EstudioRadiologico('RX_COL_CERVICAL', 'Radiografía de columna cervical', 'columna', 'Columna cervical',
        'Evaluación de vértebras C1-C7 y su alineación.', 'columna',
        ('AP', 'LAT', 'AP_TRANSORAL', 'OBL_DER', 'OBL_IZQ', 'FLEXION', 'EXTENSION', 'NADADOR'),
        (_p('AP_LAT', 'AP y lateral', 'AP', 'LAT'), _p('TRAUMA', 'AP, lateral y transoral', 'AP', 'LAT', 'AP_TRANSORAL'),
         _p('DINAMICA', 'Laterales dinámicas (flexión y extensión)', 'FLEXION', 'EXTENSION')),
        fuente=_ACR_COLUMNA, notas=('La lateral debe incluir C7-T1; si no, considerar proyección de nadador.',)),
    EstudioRadiologico('RX_COL_DORSAL', 'Radiografía de columna dorsal', 'columna', 'Columna dorsal (torácica)',
        'Evaluación de vértebras T1-T12.', 'columna', ('AP', 'LAT', 'NADADOR'),
        (_p('AP_LAT', 'AP y lateral', 'AP', 'LAT'),), fuente=_ACR_COLUMNA),
    EstudioRadiologico('RX_COL_LUMBAR', 'Radiografía de columna lumbar', 'columna', 'Columna lumbar',
        'Evaluación de vértebras L1-L5.', 'columna',
        ('AP', 'LAT', 'L5S1', 'OBL_DER', 'OBL_IZQ', 'FLEXION', 'EXTENSION'),
        (_p('AP_LAT', 'AP y lateral', 'AP', 'LAT'), _p('AP_LAT_L5S1', 'AP, lateral y L5-S1', 'AP', 'LAT', 'L5S1'),
         _p('OBLICUAS', 'Oblicuas (pars interarticularis)', 'OBL_DER', 'OBL_IZQ'),
         _p('DINAMICA', 'Laterales dinámicas', 'FLEXION', 'EXTENSION')),
        fuente=_ACR_COLUMNA),
    EstudioRadiologico('RX_COL_LUMBOSACRA', 'Radiografía de columna lumbosacra', 'columna', 'Columna lumbosacra',
        'Evaluación de columna lumbar y unión lumbosacra.', 'columna', ('AP', 'LAT', 'L5S1', 'OBL_DER', 'OBL_IZQ'),
        (_p('AP_LAT_L5S1', 'AP, lateral y L5-S1', 'AP', 'LAT', 'L5S1'),), fuente=_ACR_COLUMNA),
    EstudioRadiologico('RX_SACRO_COCCIX', 'Radiografía de sacro y cóccix', 'columna', 'Sacro y cóccix',
        'Evaluación del sacro y cóccix, habitualmente por traumatismo.', 'columna', ('AP_AXIAL', 'LAT'),
        (_p('AP_AXIAL_LAT', 'AP axial y lateral', 'AP_AXIAL', 'LAT'),), fuente=_ACR_COLUMNA),
    EstudioRadiologico('RX_COL_TOTAL', 'Radiografía de columna completa (escoliosis)', 'columna', 'Columna completa',
        'Evaluación de escoliosis en bipedestación; permite medir ángulo de Cobb.', 'columna', ('PA', 'AP', 'LAT'),
        (_p('PA_LAT', 'PA (o AP) y lateral en bipedestación', 'PA', 'LAT'),),
        fuente='ACR-SPR-SSR Practice Parameter for the Performance of Radiography for Scoliosis in Children.',
        notas=('Estudio ampliado: requiere chasis o detector largo; deshabilitar si el equipo no lo permite.',)),
    # --- Pelvis y cadera ---------------------------------------------------
    EstudioRadiologico('RX_PELVIS', 'Radiografía de pelvis', 'pelvis_cadera', 'Pelvis',
        'Evaluación de pelvis ósea, sacroilíacas y ambas caderas.', 'pelvis_cadera', ('AP',),
        (_p('AP', 'AP de pelvis', 'AP'),), fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_CADERA', 'Radiografía de cadera', 'pelvis_cadera', 'Cadera',
        'Evaluación de la articulación coxofemoral.', 'pelvis_cadera', ('AP', 'RANA', 'AXIAL_CADERA'),
        (_p('AP_RANA', 'AP y lateral en rana', 'AP', 'RANA'),
         _p('TRAUMA', 'AP y axial lateral (sospecha de fractura: no usar rana)', 'AP', 'AXIAL_CADERA')),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES,
        notas=('Ante sospecha de fractura de cadera no realizar la proyección en rana.',)),
    # --- Extremidad superior ----------------------------------------------
    EstudioRadiologico('RX_CLAVICULA', 'Radiografía de clavícula', 'extremidad_superior', 'Clavícula', '',
        'articulacion', ('AP', 'AP_AXIAL'), (_p('AP_AXIAL', 'AP y AP axial', 'AP', 'AP_AXIAL'),),
        requiere_lateralidad=True, permite_bilateral=False, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_ESCAPULA', 'Radiografía de escápula', 'extremidad_superior', 'Escápula', '',
        'articulacion', ('AP', 'Y_ESCAPULAR'), (_p('AP_Y', 'AP y lateral en Y', 'AP', 'Y_ESCAPULAR'),),
        requiere_lateralidad=True, permite_bilateral=False, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_HOMBRO', 'Radiografía de hombro', 'extremidad_superior', 'Hombro', '',
        'articulacion', ('AP_ROT_INT', 'AP_ROT_EXT', 'GRASHEY', 'AXILAR', 'Y_ESCAPULAR'),
        (_p('RUTINA', 'AP en rotación interna y externa', 'AP_ROT_INT', 'AP_ROT_EXT'),
         _p('TRAUMA', 'Grashey y lateral en Y (o axilar)', 'GRASHEY', 'Y_ESCAPULAR')),
        requiere_lateralidad=True, permite_bilateral=False, fuente=_ACR_EXTREMIDADES,
        notas=('En traumatismo no rotar el brazo.',)),
    EstudioRadiologico('RX_HUMERO', 'Radiografía de húmero', 'extremidad_superior', 'Húmero', '',
        'hueso_largo', ('AP', 'LAT'), (_p('AP_LAT', 'AP y lateral', 'AP', 'LAT'),),
        requiere_lateralidad=True, permite_bilateral=False, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_CODO', 'Radiografía de codo', 'extremidad_superior', 'Codo', '',
        'articulacion', ('AP', 'LAT', 'OBL_INT', 'OBL_EXT'),
        (_p('AP_LAT', 'AP y lateral', 'AP', 'LAT'), _p('COMPLETO', 'AP, lateral y oblicuas', 'AP', 'LAT', 'OBL_INT', 'OBL_EXT')),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_ANTEBRAZO', 'Radiografía de antebrazo', 'extremidad_superior', 'Antebrazo', '',
        'hueso_largo', ('AP', 'LAT'), (_p('AP_LAT', 'AP y lateral', 'AP', 'LAT'),),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_MUNECA', 'Radiografía de muñeca', 'extremidad_superior', 'Muñeca', '',
        'articulacion', ('PA', 'LAT', 'OBL', 'PA_ESCAFOIDES'),
        (_p('RUTINA', 'PA, oblicua y lateral', 'PA', 'OBL', 'LAT'),
         _p('ESCAFOIDES', 'Serie de escafoides', 'PA', 'LAT', 'OBL', 'PA_ESCAFOIDES')),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_MANO', 'Radiografía de mano', 'extremidad_superior', 'Mano', '',
        'mano_pie', ('PA', 'OBL', 'LAT'), (_p('RUTINA', 'PA y oblicua', 'PA', 'OBL'), _p('COMPLETO', 'PA, oblicua y lateral', 'PA', 'OBL', 'LAT')),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_DEDOS_MANO', 'Radiografía de dedos de la mano', 'extremidad_superior', 'Dedos de la mano', '',
        'mano_pie', ('PA', 'OBL', 'LAT'), (_p('RUTINA', 'PA, oblicua y lateral', 'PA', 'OBL', 'LAT'),),
        requiere_lateralidad=True, permite_bilateral=False, detalle_requerido='Dedo(s): pulgar, índice, medio, anular o meñique.',
        fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_EDAD_OSEA', 'Radiografía para edad ósea', 'extremidad_superior', 'Mano y muñeca (no dominante)',
        'Estimación de la maduración esquelética en pediatría.', 'edad_osea', ('PA',),
        (_p('PA', 'PA de mano y muñeca izquierda', 'PA'),), fuente='Greulich y Pyle; Tanner-Whitehouse.',
        notas=('Por convención se usa la mano izquierda.',)),
    # --- Extremidad inferior -----------------------------------------------
    EstudioRadiologico('RX_FEMUR', 'Radiografía de fémur', 'extremidad_inferior', 'Fémur', '',
        'hueso_largo', ('AP', 'LAT'), (_p('AP_LAT', 'AP y lateral', 'AP', 'LAT'),),
        requiere_lateralidad=True, permite_bilateral=False, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_RODILLA', 'Radiografía de rodilla', 'extremidad_inferior', 'Rodilla', '',
        'articulacion', ('AP', 'LAT', 'OBL_INT', 'OBL_EXT', 'TUNEL', 'AXIAL_ROTULA', 'AP_BIPEDESTACION'),
        (_p('AP_LAT', 'AP y lateral', 'AP', 'LAT'),
         _p('CARGA', 'AP en bipedestación y lateral (artrosis)', 'AP_BIPEDESTACION', 'LAT'),
         _p('COMPLETO', 'AP, lateral, túnel y axial de rótula', 'AP', 'LAT', 'TUNEL', 'AXIAL_ROTULA')),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_ROTULA', 'Radiografía de rótula', 'extremidad_inferior', 'Rótula', '',
        'articulacion', ('PA', 'LAT', 'AXIAL_ROTULA'), (_p('LAT_AXIAL', 'Lateral y axial', 'LAT', 'AXIAL_ROTULA'),),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_TIBIA_PERONE', 'Radiografía de tibia y peroné', 'extremidad_inferior', 'Pierna', '',
        'hueso_largo', ('AP', 'LAT'), (_p('AP_LAT', 'AP y lateral', 'AP', 'LAT'),),
        requiere_lateralidad=True, permite_bilateral=False, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_TOBILLO', 'Radiografía de tobillo', 'extremidad_inferior', 'Tobillo', '',
        'articulacion', ('AP', 'MORTAJA', 'LAT', 'CARGA'),
        (_p('RUTINA', 'AP, mortaja y lateral', 'AP', 'MORTAJA', 'LAT'),),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_PIE', 'Radiografía de pie', 'extremidad_inferior', 'Pie', '',
        'mano_pie', ('AP_DP', 'OBL', 'LAT', 'CARGA'),
        (_p('RUTINA', 'Dorsoplantar, oblicua y lateral', 'AP_DP', 'OBL', 'LAT'),
         _p('CARGA', 'Dorsoplantar y lateral con carga', 'AP_DP', 'LAT', 'CARGA')),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_DEDOS_PIE', 'Radiografía de dedos del pie', 'extremidad_inferior', 'Dedos del pie', '',
        'mano_pie', ('AP_DP', 'OBL', 'LAT'), (_p('RUTINA', 'Dorsoplantar, oblicua y lateral', 'AP_DP', 'OBL', 'LAT'),),
        requiere_lateralidad=True, permite_bilateral=False, detalle_requerido='Dedo(s) del pie.', fuente=_ACR_EXTREMIDADES),
    EstudioRadiologico('RX_CALCANEO', 'Radiografía de calcáneo', 'extremidad_inferior', 'Calcáneo', '',
        'articulacion', ('AXIAL_CALCANEO', 'LAT'), (_p('AXIAL_LAT', 'Axial y lateral', 'AXIAL_CALCANEO', 'LAT'),),
        requiere_lateralidad=True, fuente=_ACR_EXTREMIDADES),
    # --- Craneo y cara -----------------------------------------------------
    EstudioRadiologico('RX_CRANEO', 'Radiografía de cráneo', 'craneo_cara', 'Cráneo',
        'Uso limitado; en traumatismo craneal la TC es el estudio de elección.', 'craneo',
        ('CALDWELL', 'TOWNE', 'LAT'), (_p('RUTINA', 'PA (Caldwell), Towne y lateral', 'CALDWELL', 'TOWNE', 'LAT'),),
        fuente='ACR Appropriateness Criteria (traumatismo craneal: TC de elección); ' + _POSICIONAMIENTO),
    EstudioRadiologico('RX_HUESOS_NASALES', 'Radiografía de huesos nasales', 'craneo_cara', 'Huesos nasales', '',
        'huesos_nasales', ('LAT', 'WATERS'), (_p('RUTINA', 'Laterales y Waters', 'LAT', 'WATERS'),), fuente=_POSICIONAMIENTO),
    EstudioRadiologico('RX_SENOS_PARANASALES', 'Radiografía de senos paranasales', 'craneo_cara', 'Senos paranasales',
        'Uso limitado; la TC es de elección en sinusitis complicada.', 'senos_paranasales',
        ('CALDWELL', 'WATERS', 'LAT', 'SMV'), (_p('RUTINA', 'Caldwell, Waters y lateral (en bipedestación)', 'CALDWELL', 'WATERS', 'LAT'),),
        fuente='ACR Appropriateness Criteria (sinusitis); ' + _POSICIONAMIENTO),
    EstudioRadiologico('RX_HUESOS_FACIALES', 'Radiografía de huesos faciales', 'craneo_cara', 'Macizo facial', '',
        'huesos_faciales', ('WATERS', 'CALDWELL', 'LAT', 'SMV'),
        (_p('RUTINA', 'Waters, Caldwell y lateral', 'WATERS', 'CALDWELL', 'LAT'),), fuente=_POSICIONAMIENTO),
    EstudioRadiologico('RX_CAVUM', 'Radiografía de cavum (partes blandas de cuello)', 'cuello', 'Rinofaringe / cuello',
        'Evaluación de tejido adenoideo en pediatría y de vía aérea.', 'cuello_partes_blandas', ('LAT', 'AP'),
        (_p('LAT', 'Lateral de cuello / cavum', 'LAT'),), fuente=_POSICIONAMIENTO),
)

ESTUDIOS_POR_CODIGO = {e.codigo: e for e in ESTUDIOS}


def validar_catalogo() -> list[str]:
    """Comprueba consistencia interna; devuelve la lista de errores (vacia si es valido)."""
    errores: list[str] = []
    codigos: set[str] = set()
    for estudio in ESTUDIOS:
        if estudio.codigo in codigos:
            errores.append(f'Código duplicado: {estudio.codigo}')
        codigos.add(estudio.codigo)
        if estudio.categoria not in CATEGORIAS:
            errores.append(f'{estudio.codigo}: categoría desconocida {estudio.categoria}')
        if estudio.plantilla not in PLANTILLAS:
            errores.append(f'{estudio.codigo}: plantilla desconocida {estudio.plantilla}')
        for proyeccion in estudio.proyecciones:
            if proyeccion not in PROYECCIONES:
                errores.append(f'{estudio.codigo}: proyección desconocida {proyeccion}')
        if not estudio.protocolos:
            errores.append(f'{estudio.codigo}: sin protocolos')
        for protocolo in estudio.protocolos:
            fuera = set(protocolo.proyecciones) - set(estudio.proyecciones)
            if fuera:
                errores.append(f'{estudio.codigo}/{protocolo.codigo}: proyecciones no permitidas {sorted(fuera)}')
    for plantilla in PLANTILLAS.values():
        claves = [c.clave for c in plantilla.campos]
        if len(claves) != len(set(claves)):
            errores.append(f'Plantilla {plantilla.codigo}: claves repetidas')
        if set(claves) & set(CLAVES_GENERALES):
            errores.append(f'Plantilla {plantilla.codigo}: usa claves reservadas de campos generales')
        for campo in plantilla.campos:
            if campo.tipo not in TIPOS_CAMPO:
                errores.append(f'Plantilla {plantilla.codigo}/{campo.clave}: tipo {campo.tipo} no válido')
            if campo.tipo == 'opcion' and not campo.opciones:
                errores.append(f'Plantilla {plantilla.codigo}/{campo.clave}: opción sin valores')
    return errores


def _campo_dict(campo: Campo) -> dict:
    datos = {'clave': campo.clave, 'titulo': campo.titulo, 'tipo': campo.tipo, 'ayuda': campo.ayuda}
    if campo.frases:
        datos['frases'] = list(campo.frases)
    if campo.opciones:
        datos['opciones'] = list(campo.opciones)
    if campo.tipo == 'medicion':
        datos.update({'unidad': campo.unidad, 'minimo': campo.minimo, 'maximo': campo.maximo})
    return datos


def plantilla_como_dict(codigo: str) -> dict:
    plantilla = PLANTILLAS[codigo]
    return {
        'codigo': plantilla.codigo,
        'nombre': plantilla.nombre,
        'version': VERSION_CATALOGO,
        'generales': [_campo_dict(c) for c in CAMPOS_GENERALES],
        'apartados': [_campo_dict(c) for c in plantilla.campos],
    }


def configuracion_estudio(estudio: EstudioRadiologico) -> dict:
    """Configuracion serializable (JSON) del estudio, para guardar en BD y enviar al frontend."""
    return {
        'version': VERSION_CATALOGO,
        'categoria': estudio.categoria,
        'region': estudio.region,
        'descripcion': estudio.descripcion,
        'requiere_lateralidad': estudio.requiere_lateralidad,
        'permite_bilateral': estudio.permite_bilateral,
        'detalle_requerido': estudio.detalle_requerido,
        'proyecciones': [{'codigo': c, 'nombre': PROYECCIONES[c].nombre} for c in estudio.proyecciones],
        'protocolos': [{'codigo': p.codigo, 'nombre': p.nombre, 'proyecciones': list(p.proyecciones)} for p in estudio.protocolos],
        'plantilla': plantilla_como_dict(estudio.plantilla),
        'fuente': estudio.fuente,
        'notas': list(estudio.notas),
    }
