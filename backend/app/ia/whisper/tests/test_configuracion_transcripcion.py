"""Configuración de velocidad sin descargar modelos ni usar audio real."""
from types import SimpleNamespace

import pytest

from app.ia.whisper.infrastructure.transcription import faster_whisper_service as modulo


@pytest.mark.parametrize('beam_size', [1, 3, 5])
def test_aplica_busqueda_configurada_y_reutiliza_modelo(monkeypatch, beam_size):
    cargas, llamadas = [], []

    class Modelo:
        def __init__(self, *args, **kwargs):
            cargas.append((args, kwargs))

        def transcribe(self, audio, **kwargs):
            llamadas.append(kwargs)
            return iter([SimpleNamespace(text=' Texto ficticio.')]), None

    monkeypatch.setattr(modulo, 'WhisperModel', Modelo)
    servicio = modulo.FasterWhisperService('small', 'cpu', 'int8', '.models/whisper', 4, beam_size)
    assert servicio._transcribir_sync(b'audio-ficticio') == 'Texto ficticio.'
    assert servicio._transcribir_sync(b'otro-audio-ficticio') == 'Texto ficticio.'
    assert len(cargas) == 1
    assert len(llamadas) == 2
    assert all(c['beam_size'] == beam_size and c['language'] == 'es' and c['vad_filter'] for c in llamadas)


def test_perfil_rapido_conserva_reintento_si_vad_descarta_voz(monkeypatch):
    llamadas = []

    class Modelo:
        def transcribe(self, audio, **kwargs):
            llamadas.append(kwargs)
            return iter([] if kwargs['vad_filter'] else [SimpleNamespace(text=' Voz baja ficticia.')]), None

    servicio = modulo.FasterWhisperService('small', 'cpu', 'int8', '.models/whisper', 4, beam_size=1)
    monkeypatch.setitem(servicio.__dict__, 'model', Modelo())
    assert servicio._transcribir_sync(b'audio-ficticio') == 'Voz baja ficticia.'
    assert [c['vad_filter'] for c in llamadas] == [True, False]
    assert all(c['beam_size'] == 1 for c in llamadas)
