"""Preguntas de autoría no experta, ancladas al corpus ANTES de recuperar."""
from pathlib import Path
import re
from app.imagenes.infrastructure.rag.ingesta import cargar_corpus

# Pregunta, hallazgo, sección y ancla verificable del documento; no usar top-k
# para establecer relevancia. Varias preguntas comparten sección: no independientes.
RESPONDIBLES = [
 ('¿Qué volumen de derrame pleural se hace evidente en una radiografía PA?', 'Effusion', 'Imaging studies / Chest X-ray', '200 mL'),
 ('¿Cuánto líquido pleural puede borrar el ángulo costofrénico en la vista lateral?', 'Effusion', 'Imaging studies / Chest X-ray', '50 mL'),
 ('¿Qué forma tiene el borde superior clásico del derrame pleural?', 'Effusion', 'Imaging studies / Chest X-ray', 'Ellis S-shaped curve'),
 ('¿Puede un derrame pleural tener localización subpulmonar?', 'Effusion', 'Imaging studies / Chest X-ray', 'subpulmonic'),
 ('¿Qué apariencia tiene un derrame pleural en una cisura?', 'Effusion', 'Imaging studies / Chest X-ray', 'biconvex opacities'),
 ('¿Qué desplazamiento puede producir un derrame pleural masivo?', 'Effusion', 'Imaging studies / Chest X-ray', 'contralateral mediastinal shift'),
 ('¿Qué vista radiográfica ayuda a evaluar un derrame pleural subpulmonar?', 'Effusion', 'Imaging studies / Chest X-ray', 'Lateral decubitus radiography'),
 ('¿Qué opacidad pleural residual puede aparecer al resolverse un derrame?', 'Effusion', 'Imaging studies / Chest X-ray', 'rounded opacity'),
 ('¿La cardiomegalia ayuda a diferenciar edema hidrostático de ARDS?', 'Cardiomegaly', 'Introduction / Pulmonary edema', 'presence of cardiomegaly'),
 ('¿Qué ancho del pedículo vascular acompaña a cardiomegalia en edema hidrostático?', 'Cardiomegaly', 'Introduction / Pulmonary edema', 'vascular pedicle'),
 ('¿La ausencia de cardiomegalia es típica de ARDS frente al edema cardiogénico?', 'Cardiomegaly', 'Introduction / Acute respiratory distress syndrome (ARDS)', 'cardiomegaly, normal vascular pedicle'),
 ('¿Puede existir insuficiencia cardiaca con tamaño cardiaco normal y confundir la lectura de cardiomegalia?', 'Cardiomegaly', 'Introduction / Acute respiratory distress syndrome (ARDS)', 'heart failure in a normal sized heart'),
 ('¿Pueden coexistir ARDS y edema cardiogénico al interpretar cardiomegalia?', 'Cardiomegaly', 'Introduction / Acute respiratory distress syndrome (ARDS)', 'coexistence of ARDS'),
 ('¿Qué redistribución vascular ayuda a distinguir ARDS de edema con cardiomegalia?', 'Cardiomegaly', 'Introduction / Acute respiratory distress syndrome (ARDS)', 'apical vascular redistribution'),
 ('¿Cómo es la silueta cardiaca en el patrón descrito de aspiración, en contraste con cardiomegalia?', 'Cardiomegaly', 'Aspiration', 'normal cardiac silhouette'),
 ('¿Qué patrones pueden variar con la posición en edema acompañado de cardiomegalia?', 'Cardiomegaly', 'Introduction / Pulmonary edema', 'patient position'),
 ('¿Qué patrón de consolidación se describe en neumonía asociada a ventilación?', 'Consolidation', 'Introduction / Ventilator-associated pneumonia', 'patchy areas of consolidation'),
 ('¿La consolidación de neumonía asociada a ventilación puede ser multifocal?', 'Consolidation', 'Introduction / Ventilator-associated pneumonia', 'often multifocal'),
 ('¿Un derrame asociado favorece el contexto de consolidación en neumonía del ventilado?', 'Consolidation', 'Introduction / Ventilator-associated pneumonia', 'pleural effusion favors'),
 ('¿Qué ausencia de pérdida de volumen orienta al interpretar consolidación frente a atelectasia?', 'Consolidation', 'Introduction / Ventilator-associated pneumonia', 'Absence of volume loss'),
 ('¿El empeoramiento del edema alveolar puede producir consolidación?', 'Consolidation', 'Introduction / Pulmonary edema', 'frank consolidation'),
 ('¿Cómo evolucionan las opacidades hacia consolidación difusa en ARDS?', 'Consolidation', 'Introduction / Acute respiratory distress syndrome (ARDS)', 'diffuse consolidation'),
 ('¿En qué intervalo descrito puede progresar la consolidación del ARDS?', 'Consolidation', 'Introduction / Acute respiratory distress syndrome (ARDS)', '48'),
 ('¿Una radiografía negativa excluye neumonía asociada a ventilación con posible consolidación?', 'Consolidation', 'Introduction / Ventilator-associated pneumonia', 'negative chest x-ray does not exclude'),
]
FUERA = ['¿Qué dosis de insulina corresponde a esta glucemia?', '¿Cómo se clasifica una fractura de cadera?',
 '¿Qué muestra la resonancia cerebral?', '¿Cuál es la técnica de cirugía de catarata?',
 '¿Qué antibiótico y dosis debe recibir esta persona?', '¿Cuál es la estadificación histológica del melanoma?',
 '¿Qué vacuna corresponde según el calendario boliviano?', '¿Qué interacciones tiene la warfarina con este medicamento?']
AMBIGUAS = ['¿Está confirmado el derrame pleural de este paciente?', '¿Esta cardiomegalia pertenece al paciente A o B?',
 '¿La consolidación es derecha o izquierda en mi imagen no adjunta?', '¿El derrame pleural de hoy aumentó frente a ayer sin imágenes?',
 '¿Cuál de dos informes contradictorios confirma cardiomegalia?', '¿Este score de consolidación confirma neumonía?',
 '¿La silueta cardiaca de esta persona demuestra cardiomegalia sin imagen?', '¿El derrame pleural de este paciente es maligno sin estudios?']


def generar_preguntas(corpus_dir: Path) -> list[dict]:
    corpus = cargar_corpus(corpus_dir)
    filas = []
    for n, (texto, hallazgo, seccion, ancla) in enumerate(RESPONDIBLES, 1):
        patron = r'\s+'.join(re.escape(p) for p in ancla.split())
        matches = [(d, f, re.search(patron, f['texto'])) for d, fs in corpus for f in fs
                   if f['seccion'] == seccion and re.search(patron, f['texto'])]
        if not matches:
            raise ValueError('Referencia no encontrada: '+ancla)
        d, f, match = matches[0]
        filas.append({'id': f'RAG-{n:02d}', 'pregunta': texto, 'grupo': 'respondible',
            'respondible': True, 'hallazgo': hallazgo, 'referencias': [{'documento_id': d['id'],
                'seccion': seccion, 'cita': match.group(), 'sha256': d['sha256']}], 'autor': 'sintético, no revisión experta'})
    for grupo, textos in [('fuera_corpus', FUERA), ('ambiguo_paciente', AMBIGUAS)]:
        for texto in textos:
            filas.append({'id': f'RAG-{len(filas)+1:02d}', 'pregunta': texto, 'grupo': grupo,
                'respondible': False, 'referencias': [], 'autor': 'sintético, no revisión experta'})
    return filas
