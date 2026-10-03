"""HTTP adapter for the shared service; existing contracts retained."""
from contextlib import contextmanager
from uuid import UUID
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from .database import get_session
from .models import User
# Re-export schemas and pipeline names for existing imports and provider test seams.
from .services.training_contracts import InterpretPayload, SessionPayload, VideoLink, WorkoutBlock
from .services.training_media import IMAGE_LIMIT, image_directory
from .services.training_transcription import AUDIO_LIMIT, transcribe
from .services.workout_interpretation import interpret
from .services.training_service import TrainingService, fields
from .services.training_errors import (
    TrainingError, TrainingInvalid, TrainingNotFound, TrainingProcessingFailed,
    TrainingTooLarge, TrainingUnavailable,
)


@contextmanager
def http_errors():
    try:
        yield
    except TrainingError as error:
        status = {
            TrainingInvalid: 422, TrainingTooLarge: 413, TrainingNotFound: 404,
            TrainingUnavailable: 503, TrainingProcessingFailed: 502,
        }[type(error)]
        raise HTTPException(status, str(error)) from error


def service(user, session):
    return TrainingService(session, user.id, interpreter=interpret, transcriber=transcribe)


def router(require_athlete):
    routes = APIRouter(prefix='/api/training-sessions')

    @routes.post('/transcribe')
    def transcribe_recording(file: UploadFile = File(...), user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        raw = file.file.read(AUDIO_LIMIT + 1)
        with http_errors():
            return {'text': service(user, session).transcribe(raw)}

    @routes.post('/images', status_code=201)
    def upload_image(file: UploadFile = File(...), user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        raw = file.file.read(IMAGE_LIMIT + 1)
        with http_errors():
            row = service(user, session).store_image(raw)
        return {'id': row.id, 'url': f'/api/training-sessions/images/{row.id}'}

    @routes.get('/images/{identifier}')
    def get_image(identifier: UUID, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        with http_errors():
            path = service(user, session).image_path(identifier)
        return FileResponse(path, media_type='image/jpeg', headers={'Cache-Control': 'private, no-store', 'X-Content-Type-Options': 'nosniff'})

    @routes.post('/interpret')
    def interpret_workout(payload: InterpretPayload, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        with http_errors():
            return service(user, session).interpret(payload)

    @routes.get('')
    def list_sessions(user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        return {'items': service(user, session).list_sessions()}

    @routes.post('', status_code=201)
    def create(payload: SessionPayload, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        with http_errors():
            return service(user, session).create(payload)

    @routes.get('/{identifier}')
    def detail(identifier: UUID, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        with http_errors():
            return service(user, session).detail(identifier)

    @routes.put('/{identifier}')
    def update(identifier: UUID, payload: SessionPayload, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        with http_errors():
            return service(user, session).update(identifier, payload)

    @routes.delete('/{identifier}')
    def delete_session(identifier: UUID, user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        with http_errors():
            return service(user, session).delete(identifier)

    return routes
