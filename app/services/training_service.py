"""Shared Bitácora operations. Callers supply an authenticated athlete_id.

No phone numbers, cookies, HTTP requests or provider-specific payloads belong here.
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Analysis, TrainingImage, TrainingSession
from .training_contracts import InterpretPayload, SessionPayload
from .training_errors import (
    TrainingInvalid, TrainingNotFound, TrainingProcessingFailed,
    TrainingTooLarge, TrainingUnavailable,
)
from .training_media import TrainingMediaStore
from .training_transcription import AUDIO_LIMIT, AudioUnavailable, transcribe
from .training_usage import track_usage
from .workout_interpretation import interpret


def fields(row):
    return {key: getattr(row, key) for key in ('id', 'trained_on', 'title', 'source_text', 'workout', 'result_text', 'adaptations', 'rpe', 'video_links', 'blocks', 'source_image_id', 'created_at')}


class TrainingService:
    def __init__(self, session: Session, athlete_id: UUID, *, media=None,
                 interpreter=None, transcriber=None):
        self.session = session
        self.athlete_id = athlete_id
        self.media = media if media is not None else TrainingMediaStore()
        self.interpreter = interpreter if interpreter is not None else interpret
        self.transcriber = transcriber if transcriber is not None else transcribe

    def owned_image(self, identifier):
        row = self.session.scalar(select(TrainingImage).where(
            TrainingImage.id == identifier, TrainingImage.athlete_id == self.athlete_id))
        if row is None:
            raise TrainingNotFound('Imagen no encontrada')
        return row

    def image_path(self, identifier):
        return self.media.image_path(self.owned_image(identifier).path)

    def store_image(self, raw: bytes):
        identifier, path = self.media.save_image(raw)
        row = TrainingImage(id=identifier, athlete_id=self.athlete_id, path=path.name)
        try:
            self.session.add(row)
            self.session.commit()
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return row

    def interpret(self, payload: InterpretPayload):
        payload = InterpretPayload.model_validate(payload)
        if not payload.text.strip() and payload.image_id is None:
            raise TrainingInvalid('Escribe el WOD o agrega una foto de la pizarra')
        image = self.image_path(payload.image_id).read_bytes() if payload.image_id else None
        try:
            with track_usage(self.session, self.athlete_id, 'INTERPRET'):
                return self.interpreter(payload.text, image)
        except RuntimeError as error:
            raise TrainingUnavailable(str(error)) from error
        except Exception as error:
            raise TrainingProcessingFailed('No se pudo interpretar el WOD. Reintenta o completa la ficha manualmente.') from error

    def transcribe(self, raw: bytes):
        if len(raw) > AUDIO_LIMIT:
            raise TrainingTooLarge('El audio supera 8 MB')
        if not raw:
            raise TrainingInvalid('La grabación está vacía')
        try:
            with track_usage(self.session, self.athlete_id, 'TRANSCRIBE'):
                return self.transcriber(raw)
        except AudioUnavailable as error:
            raise TrainingUnavailable(str(error)) from error
        except ValueError as error:
            raise TrainingInvalid(str(error)) from error
        except Exception as error:
            raise TrainingProcessingFailed('No se pudo transcribir. Conserva la grabación y reintenta, o escribe el entrenamiento.') from error

    def owned(self, identifier):
        row = self.session.scalar(select(TrainingSession).where(
            TrainingSession.id == identifier, TrainingSession.athlete_id == self.athlete_id))
        if row is None:
            raise TrainingNotFound('Sesión no encontrada')
        return row

    def _assign(self, row, payload):
        if payload.source_image_id:
            self.owned_image(payload.source_image_id)
        for link in payload.video_links:
            analysis = self.session.get(Analysis, link.analysis_id)
            if analysis is None or analysis.athlete_id != self.athlete_id:
                raise TrainingNotFound('Análisis no disponible para esta sesión')
        for key, value in payload.model_dump(mode='python').items():
            setattr(row, key, value)

    def list_sessions(self):
        rows = self.session.scalars(select(TrainingSession).where(
            TrainingSession.athlete_id == self.athlete_id).order_by(
                TrainingSession.trained_on.desc(), TrainingSession.created_at.desc()).limit(200)).all()
        return [fields(row) for row in rows]

    def create(self, payload: SessionPayload):
        payload = SessionPayload.model_validate(payload)
        row = TrainingSession(athlete_id=self.athlete_id)
        self._assign(row, payload)
        self.session.add(row)
        self.session.commit()
        return fields(row)

    def detail(self, identifier):
        return fields(self.owned(identifier))

    def update(self, identifier, payload: SessionPayload):
        payload = SessionPayload.model_validate(payload)
        row = self.owned(identifier)
        self._assign(row, payload)
        self.session.commit()
        return fields(row)

    def delete(self, identifier):
        row = self.owned(identifier)
        self.session.delete(row)
        self.session.commit()
        return {'deleted': True}
