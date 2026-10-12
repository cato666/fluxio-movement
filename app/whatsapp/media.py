"""Download references through the provider; store only internal private paths."""
from datetime import timedelta
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
from uuid import UUID, uuid4
from sqlalchemy import select
from ..services.training_errors import TrainingInvalid
from ..services.training_service import TrainingService
from .identity import now
from .models import WhatsAppMedia
from .provider import ProviderError
from ..media_protocol import publish_bytes
from .queue import usage

VIDEO_LIMIT = 16 * 1024 * 1024
MEDIA_LIMIT = 8 * 1024 * 1024


def private_root():
    return Path(os.getenv('STORAGE_PATH', '/data/storage'))


def store_video(raw):
    if len(raw) > VIDEO_LIMIT or raw[4:8] != b'ftyp':
        raise TrainingInvalid('Video inválido o superior a 16 MB. Envía MP4.')
    with tempfile.TemporaryDirectory(prefix='whatsapp-video-') as directory:
        original = Path(directory) / 'video.mp4'
        original.write_bytes(raw)
        try:
            probe = subprocess.run(['ffprobe', '-v', 'error', '-protocol_whitelist', 'file,pipe',
                '-show_entries', 'format=duration,format_name:stream=codec_type,codec_name', '-of', 'json', str(original)],
                capture_output=True, timeout=15, check=True)
            info = json.loads(probe.stdout)
            seconds = float(info['format']['duration'])
            if not math.isfinite(seconds) or not 0 < seconds <= 180 or not any(
                s.get('codec_type') == 'video' and s.get('codec_name') in {'h264', 'hevc'} for s in info.get('streams', [])):
                raise ValueError()
        except Exception:
            raise TrainingInvalid('Video inválido o superior a 3 minutos. Envía MP4 H.264/HEVC.') from None
    target = private_root() / 'original' / 'whatsapp' / (uuid4().hex + '.mp4')
    target.parent.mkdir(parents=True, exist_ok=True)
    publish_bytes(target, raw)
    return target.relative_to(private_root()).as_posix()


def receive(session, inbox, message, athlete_id, provider, *, reusable_audio=None):
    if message.message_type == 'audio' and isinstance(reusable_audio, dict) and reusable_audio.get('reference') == message.media_reference and isinstance(reusable_audio.get('transcript'), str) and reusable_audio['transcript']:
        return None, None, reusable_audio['transcript']
    cached = session.scalar(select(WhatsAppMedia).where(WhatsAppMedia.inbox_id == inbox.id,
                                                     WhatsAppMedia.athlete_id == athlete_id))
    if cached:
        image_id = UUID(Path(cached.path).stem) if cached.media_type == 'image' else None
        return cached, image_id, None
    if not message.media_reference:
        raise TrainingInvalid('El mensaje no contiene una referencia de media válida')
    from ..services.consumption_limits import reserve, check_budget
    reservation = None
    if message.message_type in {'audio', 'image'}:
        operation = 'TRANSCRIBE' if message.message_type == 'audio' else 'INTERPRET'
        TrainingService(session, athlete_id, commit=False).check_provider(operation)
        reservation = reserve(session, athlete_id, operation, request_key=inbox.id, channel='whatsapp')
        session.info.setdefault('media_reservations', {})[(inbox.id, operation)] = reservation
    else:
        check_budget()
    if reservation is not None:
        session.info.setdefault('media_provider_started', set()).add(reservation)
    media = provider.download_media(message.media_reference, VIDEO_LIMIT if message.message_type == 'video' else MEDIA_LIMIT)
    usage(session, f'download:{inbox.id}:{inbox.attempts}', 'media_bytes', athlete_id, units=len(media.data))
    session.flush()  # Keep the account lock until worker completion.
    mime = media.mime.lower()
    allowed = {'image': {'image/jpeg','image/png','image/webp'},
               'audio': {'audio/ogg','application/ogg','audio/webm','audio/mp4','audio/wav','audio/x-wav'},
               'video': {'video/mp4'}}
    if mime not in allowed.get(message.message_type, set()):
        raise TrainingInvalid('Tipo de media no soportado')
    service = TrainingService(session, athlete_id, commit=False, request_key=inbox.id, channel='whatsapp', reservation_id=reservation if message.message_type == 'audio' else None)
    if message.message_type == 'audio':
        return None, None, service.transcribe(media.data)
    if message.message_type == 'image':
        image = service.store_image(media.data)
        path = 'training-images/' + image.path
        image_id = image.id
    else:
        path, image_id = store_video(media.data), None
    row = WhatsAppMedia(athlete_id=athlete_id, inbox_id=inbox.id, path=path,
                       media_type=message.message_type, expires_at=now() + timedelta(hours=24))
    session.add(row)
    try:
        session.flush()
    except Exception:
        # A published generation is retained for reference-aware reconciliation.
        raise
    return row, image_id, None
