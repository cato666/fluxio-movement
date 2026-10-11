"""Bounded audio validation and transcription; recordings are not persisted."""
import json
import os
import math
from pathlib import Path
import subprocess
import tempfile
from uuid import uuid4
from urllib.request import Request, urlopen

AUDIO_LIMIT = 8 * 1024 * 1024
MAX_SECONDS = 180


class AudioUnavailable(RuntimeError):
    pass


def prepare_audio(raw: bytes):
    if len(raw) > AUDIO_LIMIT:
        raise ValueError('El audio supera 8 MB')
    ogg = raw.startswith(b'OggS')
    if not (raw.startswith(b'\x1a\x45\xdf\xa3') or (raw.startswith(b'RIFF') and raw[8:12] == b'WAVE') or raw[4:8] == b'ftyp' or ogg):
        raise ValueError('Audio inválido. Graba nuevamente en formato WebM, MP4, WAV u OGG/Opus.')
    with tempfile.TemporaryDirectory(prefix='training-voice-') as directory:
        original = Path(directory) / 'recording'
        normalized = Path(directory) / 'audio.wav'
        original.write_bytes(raw)
        try:
            probe = subprocess.run(['ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-show_entries', 'format=duration:stream=codec_type,codec_name', '-of', 'json', str(original)], capture_output=True, timeout=15, check=True)
            info = json.loads(probe.stdout)
            duration = float(info.get('format', {}).get('duration', 0))
            # Some browser WebM recordings lack a duration header. Decode a bounded
            # sample and check its actual length below rather than trusting metadata.
            streams = info.get('streams', [])
            if not math.isfinite(duration) or duration < 0 or duration > MAX_SECONDS or not any(stream.get('codec_type') == 'audio' for stream in streams):
                raise ValueError('Audio inválido o superior a 3 minutos')
            if ogg and (any(stream.get('codec_type') != 'audio' for stream in streams) or not all(stream.get('codec_name') == 'opus' for stream in streams)):
                raise ValueError('La nota OGG debe contener únicamente audio Opus')
            subprocess.run(['ffmpeg', '-v', 'error', '-protocol_whitelist', 'file,pipe', '-i', str(original), '-t', str(MAX_SECONDS + 1), '-vn', '-ac', '1', '-ar', '16000', '-y', str(normalized)], capture_output=True, timeout=20, check=True)
            import wave
            with wave.open(str(normalized), 'rb') as audio:
                seconds = audio.getnframes() / audio.getframerate()
            if seconds <= 0 or seconds > MAX_SECONDS:
                raise ValueError('Audio vacío o superior a 3 minutos')
            audio_bytes = normalized.read_bytes()
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, KeyError, json.JSONDecodeError) as error:
            raise ValueError('No se pudo leer el audio. Graba nuevamente.') from error
        except FileNotFoundError as error:
            raise AudioUnavailable('La transcripción no está disponible en este servidor. Puedes escribir tu entrenamiento.') from error
    return audio_bytes, seconds


def enabled():
    return bool(os.getenv('OPENAI_API_KEY')) and os.getenv('TRAINING_VOICE_ENABLED', 'true').lower() in {'true', '1', 'yes'}


def transcribe(raw: bytes) -> str:
    if not enabled():
        raise AudioUnavailable('La transcripción no está configurada. Puedes escribir tu entrenamiento.')
    return transcribe_prepared(prepare_audio(raw))


def transcribe_prepared(prepared, *, before_call=None) -> str:
    from .training_usage import report_usage
    if not enabled():
        raise AudioUnavailable('La transcripción no está configurada. Puedes escribir tu entrenamiento.')
    audio_bytes, seconds = prepared
    boundary = 'training-' + uuid4().hex
    fields = {'model': os.getenv('TRAINING_TRANSCRIPTION_MODEL', 'gpt-transcribe'), 'language': 'es', 'response_format': 'json'}
    body = b''
    for name, value in fields.items():
        body += f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
    body += f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="recording.wav"\r\nContent-Type: audio/wav\r\n\r\n'.encode()
    body += audio_bytes + f'\r\n--{boundary}--\r\n'.encode()
    request = Request('https://api.openai.com/v1/audio/transcriptions', data=body, headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'multipart/form-data; boundary=' + boundary}, method='POST')
    report_usage(fields['model'], duration_seconds=seconds)
    if before_call is not None:
        before_call()
    with urlopen(request, timeout=45) as response:
        data = json.loads(response.read())
    usage = data.get('usage')
    report_usage(fields['model'], usage, usage.get('seconds', seconds) if isinstance(usage, dict) else seconds)
    text = data.get('text')
    if not isinstance(text, str) or not text.strip() or len(text) > 12000:
        raise ValueError('No se obtuvo una transcripción legible. Intenta hablar más cerca del micrófono.')
    return text.strip()
