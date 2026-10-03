"""Exercise a second caller directly: no HTTP requests or session cookies."""
from uuid import uuid4
import pytest
from pydantic import ValidationError
from app.models import Athlete, TrainingSession, User
from app.seed import DEMO_ATHLETE_ID
from app.services.training_contracts import InterpretPayload, SessionPayload
from app.services.training_errors import TrainingNotFound, TrainingProcessingFailed
from app.services.training_service import TrainingService
from tests.test_training_sessions import payload
from tests.test_training_interpretation import draft, photo
from tests.test_training_transcription import wav


def test_direct_create_is_visible_and_editable_by_existing_web(athlete_client, session):
    service = TrainingService(session, DEMO_ATHLETE_ID)
    created = service.create(SessionPayload.model_validate(payload()))
    url = '/api/training-sessions/' + str(created['id'])
    assert athlete_client.get(url).json()['workout'] == payload()['workout']
    assert athlete_client.put(url, json=payload(result_text='6 rondas')).status_code == 200
    session.expire_all()
    assert service.detail(created['id'])['result_text'] == '6 rondas'
    service.delete(created['id'])
    assert athlete_client.get(url).status_code == 404


def test_direct_draft_and_audio_require_explicit_save(session, monkeypatch, tmp_path):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    received = []
    def interpret(text, image):
        received.append((text, image))
        return draft()
    service = TrainingService(session, DEMO_ATHLETE_ID, interpreter=interpret,
                              transcriber=lambda raw: 'Hice 5 rondas')
    image = service.store_image(photo())
    text = service.transcribe(wav())
    proposal = service.interpret(InterpretPayload(text=text, image_id=image.id))
    assert received[0][0] == text
    assert received[0][1].startswith(b'\xff\xd8')
    assert proposal['questions'] and service.list_sessions() == []
    saved = service.create(payload(source_image_id=image.id, blocks=proposal['blocks']))
    assert service.detail(saved['id'])['source_image_id'] == image.id


def test_direct_caller_cannot_access_another_athletes_records(session, monkeypatch, tmp_path):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    other = User(id=uuid4(), name='Other', role='ATHLETE')
    session.add(other); session.flush()
    session.add(Athlete(user_id=other.id)); session.commit()
    owner = TrainingService(session, DEMO_ATHLETE_ID)
    row = owner.create(payload())
    image = owner.store_image(photo())
    def never(*args):
        pytest.fail('Foreign content must not reach AI')
    stranger = TrainingService(session, other.id, interpreter=never)
    for operation in (
        lambda: stranger.detail(row['id']),
        lambda: stranger.update(row['id'], payload()),
        lambda: stranger.delete(row['id']),
        lambda: stranger.image_path(image.id),
        lambda: stranger.interpret(InterpretPayload(image_id=image.id)),
        lambda: stranger.create(payload(source_image_id=image.id)),
    ):
        with pytest.raises(TrainingNotFound):
            operation()
    assert stranger.list_sessions() == []
    assert session.get(TrainingSession, row['id']) is not None


def test_direct_invalid_payload_does_not_persist(session):
    service = TrainingService(session, DEMO_ATHLETE_ID)
    for changes in ({'rpe': 11}, {'workout': ' '}, {'title': ' '}):
        with pytest.raises(ValidationError):
            service.create(payload(**changes))
    assert service.list_sessions() == []


def test_failed_image_persistence_removes_private_artifact(session, monkeypatch, tmp_path):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    def fail():
        raise RuntimeError('Simulated persistence failure')
    monkeypatch.setattr(session, 'commit', fail)
    with pytest.raises(RuntimeError):
        TrainingService(session, DEMO_ATHLETE_ID).store_image(photo())
    assert list((tmp_path / 'training-images').iterdir()) == []
    session.rollback()


def test_direct_provider_failure_is_safe_and_does_not_save(session):
    def fail(*args):
        raise ConnectionError('Private provider content')
    service = TrainingService(session, DEMO_ATHLETE_ID, interpreter=fail, transcriber=fail)
    for operation in (lambda: service.interpret(InterpretPayload(text='WOD')),
                      lambda: service.transcribe(wav())):
        with pytest.raises(TrainingProcessingFailed) as error:
            operation()
        assert 'Private' not in str(error.value)
    assert service.list_sessions() == []
