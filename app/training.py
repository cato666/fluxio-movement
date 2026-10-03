"""Owned training sessions. Videos remain optional and use existing analyses."""
from datetime import date
from uuid import UUID, uuid4
from pathlib import Path
import os
import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session
from .database import get_session
from .models import Analysis, TrainingImage, TrainingSession, User
from .services.workout_interpretation import WorkoutBlock, interpret
from .services.training_transcription import AUDIO_LIMIT, AudioUnavailable, transcribe
from .services.training_usage import track_usage

IMAGE_LIMIT = 8 * 1024 * 1024


def image_directory():
    return Path(os.getenv('STORAGE_PATH', '/data/storage')) / 'training-images'


class InterpretPayload(BaseModel):
    text: str = Field(default='', max_length=12000)
    image_id: UUID | None = None


class VideoLink(BaseModel):
    analysis_id: str = Field(min_length=1, max_length=32)
    movement: str = Field(min_length=1, max_length=100)
    context: str = Field(default='', max_length=160)


class SessionPayload(BaseModel):
    trained_on: date
    title: str = Field(min_length=1, max_length=160)
    source_text: str = Field(default='', max_length=12000)
    workout: str = Field(min_length=1, max_length=12000)
    result_text: str | None = Field(default=None, max_length=4000)
    adaptations: str | None = Field(default=None, max_length=4000)
    rpe: int | None = Field(default=None, ge=1, le=10, strict=True)
    video_links: list[VideoLink] = Field(default_factory=list, max_length=30)
    blocks: list[WorkoutBlock] = Field(default_factory=list, max_length=12)
    source_image_id: UUID | None = None

    @field_validator('title', 'workout')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Completa este campo')
        return value.strip()


def fields(row):
    return {key: getattr(row, key) for key in ('id', 'trained_on', 'title', 'source_text', 'workout', 'result_text', 'adaptations', 'rpe', 'video_links', 'blocks', 'source_image_id', 'created_at')}


def router(require_athlete):
    routes = APIRouter(prefix='/api/training-sessions')

    @routes.post('/transcribe')
    def transcribe_recording(file: UploadFile = File(...), user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        raw = file.file.read(AUDIO_LIMIT + 1)
        if len(raw) > AUDIO_LIMIT:
            raise HTTPException(413, 'El audio supera 8 MB')
        if not raw:
            raise HTTPException(422, 'La grabación está vacía')
        try:
            with track_usage(session, user.id, 'TRANSCRIBE'):
                return {'text': transcribe(raw)}
        except AudioUnavailable as error:
            raise HTTPException(503, str(error)) from error
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except Exception as error:
            raise HTTPException(502, 'No se pudo transcribir. Conserva la grabación y reintenta, o escribe el entrenamiento.') from error

    def owned_image(identifier, user, session):
        row = session.scalar(select(TrainingImage).where(TrainingImage.id == identifier, TrainingImage.athlete_id == user.id))
        if row is None:
            raise HTTPException(404, 'Imagen no encontrada')
        return row

    @routes.post('/images', status_code=201)
    def upload_image(file: UploadFile = File(...), user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        raw = file.file.read(IMAGE_LIMIT + 1)
        if len(raw) > IMAGE_LIMIT:
            raise HTTPException(413, 'La imagen supera 8 MB')
        if not (raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG\r\n\x1a\n') or (raw.startswith(b'RIFF') and raw[8:12] == b'WEBP')):
            raise HTTPException(422, 'Sube una imagen JPEG, PNG o WebP válida')
        try:
            image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        except cv2.error:
            image = None
        if image is None or image.shape[0] * image.shape[1] > 24000000:
            raise HTTPException(422, 'Imagen inválida o demasiado grande (máximo 24 megapíxeles)')
        if max(image.shape[:2]) > 2400:
            factor = 2400 / max(image.shape[:2])
            image = cv2.resize(image, (round(image.shape[1] * factor), round(image.shape[0] * factor)))
        ok, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        if not ok:
            raise HTTPException(422, 'No se pudo procesar la imagen')
        identifier = uuid4()
        directory = image_directory(); directory.mkdir(parents=True, exist_ok=True)
        path = directory / f'{identifier}.jpg'
        path.write_bytes(encoded.tobytes())
        row = TrainingImage(id=identifier, athlete_id=user.id, path=path.name)
        try:
            session.add(row); session.commit()
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return {'id': identifier, 'url': f'/api/training-sessions/images/{identifier}'}

    @routes.get('/images/{identifier}')
    def get_image(identifier: UUID, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        row = owned_image(identifier, user, session)
        path = image_directory() / row.path
        if not path.is_file():
            raise HTTPException(404, 'Imagen no disponible')
        return FileResponse(path, media_type='image/jpeg', headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})

    @routes.post('/interpret')
    def interpret_workout(payload: InterpretPayload, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        if not payload.text.strip() and payload.image_id is None:
            raise HTTPException(422, 'Escribe el WOD o agrega una foto de la pizarra')
        image = None
        if payload.image_id:
            row = owned_image(payload.image_id, user, session)
            path = image_directory() / row.path
            if not path.is_file():
                raise HTTPException(404, 'Imagen no disponible')
            image = path.read_bytes()
        try:
            with track_usage(session, user.id, 'INTERPRET'):
                return interpret(payload.text, image)
        except RuntimeError as error:
            raise HTTPException(503, str(error)) from error
        except Exception as error:
            raise HTTPException(502, 'No se pudo interpretar el WOD. Reintenta o completa la ficha manualmente.') from error

    def owned(identifier, user, session):
        row = session.scalar(select(TrainingSession).where(TrainingSession.id == identifier, TrainingSession.athlete_id == user.id))
        if row is None:
            raise HTTPException(404, 'Sesión no encontrada')
        return row

    def assign(row, payload, user, session):
        if payload.source_image_id:
            owned_image(payload.source_image_id, user, session)
        for link in payload.video_links:
            analysis = session.get(Analysis, link.analysis_id)
            if analysis is None or analysis.athlete_id != user.id:
                raise HTTPException(404, 'Análisis no disponible para esta sesión')
        for key, value in payload.model_dump(mode='python').items():
            setattr(row, key, value)

    @routes.get('')
    def list_sessions(user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        rows = session.scalars(select(TrainingSession).where(TrainingSession.athlete_id == user.id).order_by(TrainingSession.trained_on.desc(), TrainingSession.created_at.desc()).limit(200)).all()
        return {'items': [fields(row) for row in rows]}

    @routes.post('', status_code=201)
    def create(payload: SessionPayload, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        row = TrainingSession(athlete_id=user.id)
        assign(row, payload, user, session)
        session.add(row)
        session.commit()
        return fields(row)

    @routes.get('/{identifier}')
    def detail(identifier: UUID, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        return fields(owned(identifier, user, session))

    @routes.put('/{identifier}')
    def update(identifier: UUID, payload: SessionPayload, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        row = owned(identifier, user, session)
        assign(row, payload, user, session)
        session.commit()
        return fields(row)

    @routes.delete('/{identifier}')
    def delete_session(identifier: UUID, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        row = owned(identifier, user, session)
        session.delete(row)
        session.commit()
        return {'deleted': True}

    return routes
