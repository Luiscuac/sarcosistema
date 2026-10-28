from io import BytesIO
import wave

from faster_whisper.audio import decode_audio


def test_whisper_decodifica_wav_con_pyav_instalado():
    """Detecta incompatibilidades de API PyAV antes de cargar Whisper o su modelo."""
    audio = BytesIO()
    with wave.open(audio, 'wb') as salida:
        salida.setnchannels(1)
        salida.setsampwidth(2)
        salida.setframerate(16000)
        salida.writeframes(b'\x00\x00' * 1600)
    audio.seek(0)
    muestras = decode_audio(audio)
    assert len(muestras) == 1600
