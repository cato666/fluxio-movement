from datetime import timedelta
from uuid import uuid4
import json
import pytest
from sqlalchemy import select
from app.models import TrainingImage
from app.seed import DEMO_ATHLETE_ID
from app.whatsapp.models import ConversationState
from app.whatsapp.identity import now
from app.whatsapp.worker import cleanup
from app.services.photo_retention import inventory


def photo(session, tmp_path, monkeypatch):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    directory = tmp_path / 'training-images'
    directory.mkdir(exist_ok=True)
    identifier = uuid4()
    path = directory / f'{identifier}.jpg'
    path.write_bytes(b'synthetic-private-photo')
    image = TrainingImage(id=identifier, athlete_id=DEMO_ATHLETE_ID, path=path.name)
    session.add(image)
    session.commit()
    return image, path


def test_observation_never_authorizes_cleanup(session, tmp_path, monkeypatch):
    image, path = photo(session, tmp_path, monkeypatch)
    for _ in range(2):
        report = inventory(session)
        assert report['counts'] == {'unreferenced_observation': 1}
        assert report['eligible_for_deletion'] == 0
        assert report['effective_cleanup'] == 'BLOCKED_S16'
        cleanup(session)
        assert path.read_bytes() == b'synthetic-private-photo'
        assert session.get(TrainingImage, image.id) is not None
    assert 'synthetic-private-photo' not in json.dumps(report)
    assert image.path not in json.dumps(report)
    assert str(DEMO_ATHLETE_ID) not in json.dumps(report)


@pytest.mark.parametrize('expired', [False, True])
def test_context_conservative_without_decryption(session, tmp_path, monkeypatch, expired):
    image, path = photo(session, tmp_path, monkeypatch)
    session.add(ConversationState(athlete_id=DEMO_ATHLETE_ID, channel='whatsapp',
        state='CONFIRM', payload_minimized='undecipherable-private-payload', key_version='missing',
        expires_at=now() + timedelta(hours=-1 if expired else 1)))
    session.commit()
    expected = 'unreferenced_observation' if expired else 'active_context'
    assert inventory(session)['counts'] == {expected: 1}
    cleanup(session)
    assert path.exists()


@pytest.mark.parametrize('kind', ['legacy', 'missing', 'symlink'])
def test_ambiguous_paths_preserved(session, tmp_path, monkeypatch, kind):
    image, path = photo(session, tmp_path, monkeypatch)
    if kind == 'legacy':
        image.path = '../outside-private.jpg'
        session.commit()
        expected = 'legacy'
    elif kind == 'missing':
        path.unlink()  # only synthetic fixture
        expected = 'missing'
    else:
        outside = tmp_path / 'outside.jpg'
        outside.write_bytes(b'private')
        path.unlink()  # only synthetic fixture
        path.symlink_to(outside)
        expected = 'unsafe_path'
    assert inventory(session)['counts'] == {expected: 1}
    assert session.get(TrainingImage, image.id) is not None


def test_read_only_no_autoflush_or_commit(session, tmp_path, monkeypatch):
    photo(session, tmp_path, monkeypatch)
    session.add(TrainingImage(id=uuid4(), athlete_id=DEMO_ATHLETE_ID, path='pending-private'))
    def forbidden(*args, **kwargs):
        raise AssertionError('inventory must not flush or commit')
    monkeypatch.setattr(session, 'flush', forbidden)
    monkeypatch.setattr(session, 'commit', forbidden)
    assert len(inventory(session)['items']) == 1


def test_failed_cleanup_commit_cannot_remove_photo(session, tmp_path, monkeypatch):
    image, path = photo(session, tmp_path, monkeypatch)
    def failed():
        raise RuntimeError('synthetic commit failure')
    monkeypatch.setattr(session, 'commit', failed)
    with pytest.raises(RuntimeError, match='synthetic'):
        cleanup(session)
    session.rollback()
    assert path.exists()
    assert session.get(TrainingImage, image.id) is not None
