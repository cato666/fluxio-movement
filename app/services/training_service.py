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
                 interpreter=None, transcriber=None, commit=True, request_key=None, channel='web', reservation_id=None):
        self.session = session
        self.athlete_id = athlete_id
        self.media = media if media is not None else TrainingMediaStore()
        self.interpreter = interpreter if interpreter is not None else interpret
        self.transcriber = transcriber if transcriber is not None else transcribe
        self.commit = commit
        self.request_key, self.channel = request_key, channel
        self.reservation_id = reservation_id

    def _reserve(self, operation):
        from .consumption_limits import reserve, reject
        if self.reservation_id is None:
            return reserve(self.session, self.athlete_id, operation, request_key=self.request_key, channel=self.channel)
        from ..models import PlanInteraction
        from ..whatsapp.identity import active_account
        row = self.session.get(PlanInteraction, self.reservation_id)
        if active_account(self.session, self.athlete_id) is None or row is None or (
            row.user_id != self.athlete_id or row.operation != operation or row.channel != self.channel
            or row.request_key != str(self.request_key) or row.reservation_state != 'RESERVED' or row.started_at is not None):
            reject(409, 'reservation_binding_invalid')
        return row.id

    def check_provider(self, operation):
        from ..whatsapp.identity import active_account
        from .consumption_limits import reject
        user = active_account(self.session, self.athlete_id)
        if user is None:
            reject(403, 'account_inactive')
        from ..administration import usage
        entitlement = usage(self.session, user)
        if operation not in entitlement['enabled_operations']:
            reject(403, 'operation_disabled')
        if not entitlement['remaining']:
            reject(429, 'monthly_quota')
        from .workout_interpretation import interpret as native_interpret, enabled as interpretation_enabled
        from .training_transcription import transcribe as native_transcribe, enabled as transcription_enabled
        if operation == 'INTERPRET' and self.interpreter is native_interpret and not interpretation_enabled():
            raise TrainingUnavailable('La interpretación automática no está configurada. Puedes completar la ficha manualmente.')
        if operation == 'TRANSCRIBE' and self.transcriber is native_transcribe and not transcription_enabled():
            raise TrainingUnavailable('La transcripción no está configurada. Puedes escribir tu entrenamiento.')

    def _persist(self):
        # Web keeps its existing commit. Durable channels can join their transaction.
        if self.commit:
            self.session.commit()
        else:
            self.session.flush()

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
            self._persist()
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return row

    def interpret(self, payload: InterpretPayload):
        payload = InterpretPayload.model_validate(payload)
        if not payload.text.strip() and payload.image_id is None:
            raise TrainingInvalid('Escribe el WOD o agrega una foto de la pizarra')
        image = self.image_path(payload.image_id).read_bytes() if payload.image_id else None
        self.check_provider('INTERPRET')
        reservation = self._reserve('INTERPRET')
        from .consumption_limits import transition
        started = False
        def before_call():
            nonlocal started
            transition(reservation, 'STARTED')
            started = True
        succeeded = False
        try:
            with track_usage(self.session, self.athlete_id, 'INTERPRET', commit=False):
                from .workout_interpretation import interpret as native_interpret
                if self.interpreter is native_interpret:
                    result = self.interpreter(payload.text, image, before_call=before_call)
                else:
                    before_call()
                    result = self.interpreter(payload.text, image)
                succeeded = True
                return result
        except RuntimeError as error:
            raise TrainingUnavailable('La interpretación no está disponible. Puedes completar la ficha manualmente.') from error
        except Exception as error:
            raise TrainingProcessingFailed('No se pudo interpretar el WOD. Reintenta o completa la ficha manualmente.') from error
        finally:
            unknown_download = reservation in self.session.info.get('media_provider_started', set())
            state = 'CONFIRMED' if succeeded else 'UNCERTAIN' if started or unknown_download else 'RELEASED'
            transition(reservation, state, not_called=state == 'RELEASED')
            self._persist()

    def transcribe(self, raw: bytes):
        if len(raw) > AUDIO_LIMIT:
            raise TrainingTooLarge('El audio supera 8 MB')
        if not raw:
            raise TrainingInvalid('La grabación está vacía')
        self.check_provider('TRANSCRIBE')
        from .training_transcription import transcribe as native_transcribe, prepare_audio, transcribe_prepared
        prepared = None
        if self.transcriber is native_transcribe:
            try:
                prepared = prepare_audio(raw)
            except AudioUnavailable as error:
                raise TrainingUnavailable(str(error)) from error
            except ValueError as error:
                raise TrainingInvalid(str(error)) from error
        reservation = self._reserve('TRANSCRIBE')
        from .consumption_limits import transition
        started = False
        def before_call():
            nonlocal started
            transition(reservation, 'STARTED')
            started = True
        succeeded = False
        try:
            with track_usage(self.session, self.athlete_id, 'TRANSCRIBE', commit=False):
                if prepared is not None:
                    result = transcribe_prepared(prepared, before_call=before_call)
                else:
                    before_call()
                    result = self.transcriber(raw)
                succeeded = True
                return result
        except AudioUnavailable as error:
            raise TrainingUnavailable(str(error)) from error
        except ValueError as error:
            raise TrainingInvalid(str(error)) from error
        except Exception as error:
            raise TrainingProcessingFailed('No se pudo transcribir. Conserva la grabación y reintenta, o escribe el entrenamiento.') from error
        finally:
            unknown_download = reservation in self.session.info.get('media_provider_started', set())
            state = 'CONFIRMED' if succeeded else 'UNCERTAIN' if started or unknown_download else 'RELEASED'
            transition(reservation, state, not_called=state == 'RELEASED')
            self._persist()

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
        self._persist()
        return fields(row)

    def detail(self, identifier):
        return fields(self.owned(identifier))

    def update(self, identifier, payload: SessionPayload):
        payload = SessionPayload.model_validate(payload)
        row = self.owned(identifier)
        self._assign(row, payload)
        self._persist()
        return fields(row)

    def delete(self, identifier):
        row = self.owned(identifier)
        self.session.delete(row)
        self._persist()
        return {'deleted': True}

    def add_athlete_note(self, identifier, note: str, source='whatsapp'):
        if source not in {'web', 'whatsapp', 'ai'} or not note.strip() or len(note) > 4000:
            raise TrainingInvalid('Nota inválida')
        row = self.session.scalar(select(TrainingSession).where(
            TrainingSession.id == identifier, TrainingSession.athlete_id == self.athlete_id).with_for_update())
        if row is None:
            raise TrainingNotFound('Sesión no encontrada')
        addition = f'Nota del atleta ({source}): {note.strip()}'
        combined = '\n\n'.join(filter(None, [row.adaptations, addition]))
        if len(combined) > 4000:
            raise TrainingInvalid('La nota supera el espacio disponible en este entrenamiento')
        row.adaptations = combined
        row.athlete_notes = [*(row.athlete_notes or []), {'type': 'athlete_note', 'source': source, 'text': note.strip()}]
        self._persist()
        return fields(row)
