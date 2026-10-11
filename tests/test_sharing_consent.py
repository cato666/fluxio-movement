"""S05 consent/security gates, all identities and media are disposable fixtures."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from uuid import UUID, uuid4

import pytest
from PIL import Image
from sqlalchemy import func, select
from app.database import SessionLocal
from app.models import User, WeeklyShare, TrainingSession
from app.seed import DEMO_ATHLETE_ID
from app.services.weekly_summary import WeeklySummaryService, token_hash
from app.services.training_service import TrainingService
from app.services.training_contracts import SessionPayload
from app.services.training_errors import TrainingInvalid, TrainingNotFound
from app.whatsapp.models import WhatsAppInbox, WhatsAppOutbox, ConversationState
from app.whatsapp.security import Vault
from app.whatsapp.worker import process_one
from tests.share_helpers import consent_payload
from tests.whatsapp_helpers import payload, webhook
from tests.test_weekly_summary import create
from tests.test_whatsapp_capture import channel, step, button, confirm, own_session, state


def shares(session):
    session.expire_all()
    return session.scalar(select(func.count()).select_from(WeeklyShare))


@pytest.mark.parametrize('changes', [
    {'consent': False}, {'consent': None}, {'consent': 'true'}, {'consent': 1},
    {'consent_version': None}, {'consent_version': 'outdated'}, {'request_id': None}, {'request_id': 'bad'}])
def test_api_requires_exact_explicit_consent(athlete_client, session, changes):
    assert athlete_client.post('/api/training-week/shares', json=consent_payload('2026-10-02') | changes).status_code == 422
    assert shares(session) == 0


def test_legacy_api_and_internal_call_do_not_publish(athlete_client, session):
    assert athlete_client.post('/api/training-week/shares', json={'day': '2026-10-02'}).status_code == 422
    with pytest.raises(TrainingInvalid):
        WeeklySummaryService(session, DEMO_ATHLETE_ID).create_share(date(2026, 10, 2))
    assert shares(session) == 0


def test_web_save_edit_and_note_remain_private(athlete_client, session):
    saved = create(athlete_client)
    assert athlete_client.put('/api/training-sessions/' + saved['id'], json={
        'trained_on': '2026-10-02', 'title': 'Edited', 'workout': 'Private note workout'}).status_code == 200
    TrainingService(session, DEMO_ATHLETE_ID).add_athlete_note(UUID(saved['id']), 'Private personal note')
    assert shares(session) == 0


def test_acceptance_receipt_is_minimal_and_replays_do_not_publish(athlete_client, session, caplog):
    data = consent_payload('2026-10-02')
    first = athlete_client.post('/api/training-week/shares', json=data)
    assert first.status_code == 201
    link = first.json()
    repeated = athlete_client.post('/api/training-week/shares', json=data).json()
    assert repeated['id'] == link['id'] and repeated['path'] is None and repeated['already_created']
    assert shares(session) == 1
    row = session.get(WeeklyShare, UUID(link['id']))
    assert set(row.snapshot) == {'consent', 'protected_link'}
    assert row.snapshot['consent'] == {'version': 'weekly-live-v1', 'accepted': True,
        'channel': 'web', 'request_id': data['request_id'], 'accepted_at': row.snapshot['consent']['accepted_at']}
    assert datetime.fromisoformat(row.snapshot['consent']['accepted_at']).tzinfo is not None
    assert link['path'].split('/')[-1] not in caplog.text
    assert athlete_client.get(link['path']).status_code == 200


@pytest.mark.parametrize('terminal', ['revoked', 'expired'])
def test_replaying_consent_never_revives_or_extends_link(athlete_client, session, terminal):
    data = consent_payload('2026-10-02')
    link = athlete_client.post('/api/training-week/shares', json=data).json()
    row = session.get(WeeklyShare, UUID(link['id']))
    if terminal == 'revoked':
        athlete_client.delete('/api/training-week/shares/' + link['id'])
    else:
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        session.commit()
    session.expire_all()
    original = session.get(WeeklyShare, row.id).expires_at
    assert athlete_client.post('/api/training-week/shares', json=data).json()['path'] is None
    assert shares(session) == 1
    assert session.get(WeeklyShare, row.id).expires_at == original
    assert athlete_client.get(link['path']).status_code == 404


def test_same_consent_cannot_be_reused_for_another_week(athlete_client, session):
    data = consent_payload('2026-10-02')
    athlete_client.post('/api/training-week/shares', json=data)
    assert athlete_client.post('/api/training-week/shares', json=data | {'day': '2026-10-09'}).status_code == 422
    assert shares(session) == 1


def test_concurrent_identical_consent_creates_one_row(session):
    from threading import Barrier
    data = consent_payload('2026-10-02')
    barrier = Barrier(2)
    def publish():
        with SessionLocal() as separate:
            barrier.wait(timeout=10)
            return WeeklySummaryService(separate, DEMO_ATHLETE_ID).create_share(date(2026, 10, 2),
                consent=True, consent_version=data['consent_version'], request_id=data['request_id'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: publish(), range(2)))
    assert len({result['id'] for result in results}) == 1
    assert sum(result['path'] is not None for result in results) == 1
    assert shares(session) == 1


@pytest.mark.parametrize('restriction', ['expired', 'revoked', 'inactive', 'historical'])
def test_html_and_photo_access_fail_closed(athlete_client, session, monkeypatch, tmp_path, restriction):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    raw = BytesIO(); Image.new('RGB', (80, 80)).save(raw, format='PNG')
    photo = athlete_client.post('/api/training-sessions/images', files={'file': ('fixture.png', raw.getvalue(), 'image/png')}).json()
    create(athlete_client, source_image_id=photo['id'], adaptations='Sensitive note')
    link = athlete_client.post('/api/training-week/shares', json=consent_payload('2026-10-02')).json()
    public_photo = link['path'] + '/images/' + photo['id']
    assert athlete_client.get(link['path']).status_code == athlete_client.get(public_photo).status_code == 200
    row = session.get(WeeklyShare, UUID(link['id']))
    if restriction == 'expired':
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    elif restriction == 'revoked':
        row.revoked_at = datetime.now(timezone.utc)
    elif restriction == 'inactive':
        session.get(User, DEMO_ATHLETE_ID).is_active = False
    else:
        row.snapshot = {'items': [{'adaptations': 'Historical private data'}]}
    session.commit()
    for path in (link['path'], public_photo):
        response = athlete_client.get(path)
        assert response.status_code == 404
        assert response.headers['cache-control'] == 'no-store'
        assert 'Sensitive note' not in response.text
    if restriction == 'inactive':
        assert athlete_client.post('/api/training-week/shares', json=consent_payload()).status_code == 401
        with pytest.raises(TrainingNotFound):
            WeeklySummaryService(session, DEMO_ATHLETE_ID).create_share(consent=True,
                consent_version='weekly-live-v1', request_id=uuid4())


def test_historical_link_stays_blocked_after_new_consent_and_is_revocable(athlete_client, session):
    token = 'h' * 43
    legacy = WeeklyShare(athlete_id=DEMO_ATHLETE_ID, token_hash=token_hash(token),
        week_start=date(2026, 9, 28), snapshot={'items': []}, expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
    session.add(legacy);session.commit()
    preserved = (legacy.id, legacy.token_hash, legacy.expires_at, legacy.snapshot)
    items = athlete_client.get('/api/training-week/shares?day=2026-10-02').json()['items']
    assert items[0]['consent_required'] is True
    assert athlete_client.get('/shared/week/' + token).status_code == 404
    created = athlete_client.post('/api/training-week/shares', json=consent_payload('2026-10-02')).json()
    assert created['id'] != str(legacy.id)
    assert athlete_client.get(created['path']).status_code == 200
    assert athlete_client.get('/shared/week/' + token).status_code == 404
    session.expire_all();legacy = session.get(WeeklyShare, legacy.id)
    assert (legacy.id, legacy.token_hash, legacy.expires_at, legacy.snapshot) == preserved
    assert athlete_client.delete('/api/training-week/shares/' + str(legacy.id)).status_code == 200


def test_whatsapp_save_workout_and_note_create_no_links(client, channel, session):
    step(client, channel);confirm(client, channel, session)
    step(client, channel, 'nota Me sentí bien');confirm(client, channel, session)
    assert shares(session) == 0
    messages = [Vault().decrypt(row.payload_encrypted, row.key_version)['text'] for row in session.scalars(select(WhatsAppOutbox))]
    assert any('Nota guardada' in text for text in messages)
    assert not any('/shared/week/' in text for text in messages)


def test_whatsapp_command_discloses_and_cancel_does_not_publish(client, channel, session, monkeypatch):
    monkeypatch.setenv('PUBLIC_BASE_URL', 'https://fluxio-s05.invalid')
    step(client, channel, 'compartir semana')
    assert shares(session) == 0
    row = session.scalar(select(WhatsAppOutbox).order_by(WhatsAppOutbox.created_at.desc()))
    text = Vault().decrypt(row.payload_encrypted, row.key_version)['text']
    for value in ('después', 'fotografías', 'notas', '7 días', 'revocarlo'):
        assert value in text
    confirm(client, channel, session, 'cancel')
    assert shares(session) == 0


def test_whatsapp_acceptance_exactly_once_with_inbox_receipt(client, channel, session, monkeypatch):
    monkeypatch.setenv('PUBLIC_BASE_URL', 'https://fluxio-s05.invalid')
    step(client, channel, 'compartir semana pasada')
    action = button(session, 'share')
    proposed_day = __import__('app.whatsapp.capture', fromlist=['snapshot']).snapshot(state(session), Vault())['day']
    event = payload('', kind='interactive', action=action, identifier='s05.accept')
    assert webhook(client, event).status_code == 200
    assert process_one(channel[0], Vault())
    assert webhook(client, event).json()['accepted'] == 0
    before = session.scalar(select(func.count()).select_from(WhatsAppOutbox))
    assert not process_one(channel[0], Vault())
    session.expire_all()
    assert session.scalar(select(func.count()).select_from(WhatsAppOutbox)) == before
    step(client, channel, '', kind='interactive', action=action)
    assert shares(session) == 1
    share = session.scalar(select(WeeklyShare))
    assert share.week_start.isoformat() == proposed_day
    receipt = share.snapshot['consent']
    assert receipt['accepted'] and receipt['channel'] == 'whatsapp'
    inbox = session.get(WhatsAppInbox, UUID(receipt['event_id']))
    assert inbox.athlete_id == DEMO_ATHLETE_ID and inbox.state == 'DONE'
    assert channel[1] == []  # No interpretation/transcription calls.


@pytest.mark.parametrize('interruption', ['cancel', 'expire', 'deactivate', 'revoke'])
def test_pending_whatsapp_acceptance_cannot_survive_interruption(client, channel, session, monkeypatch, interruption):
    monkeypatch.setenv('PUBLIC_BASE_URL', 'https://fluxio-s05.invalid')
    step(client, channel, 'compartir semana')
    action = button(session, 'share')
    if interruption == 'cancel':
        confirm(client, channel, session, 'cancel')
    elif interruption == 'expire':
        state(session).expires_at = datetime.now(timezone.utc) - timedelta(seconds=1);session.commit()
    elif interruption == 'deactivate':
        from tests.test_whatsapp_account_status import status
        status(client, False)
    else:
        step(client, channel, 'revocar semana')
    step(client, channel, '', kind='interactive', action=action)
    assert shares(session) == 0


def test_plain_guardar_is_not_acceptance_to_publish(client, channel, session, monkeypatch):
    monkeypatch.setenv('PUBLIC_BASE_URL', 'https://fluxio-s05.invalid')
    step(client, channel, 'compartir semana')
    step(client, channel, 'guardar')
    assert shares(session) == 0
    assert state(session).state == 'SHARE_CONSENT'


def test_api_cannot_choose_another_athlete_or_forge_receipt(athlete_client, session):
    for fields in ({'athlete_id': str(uuid4())}, {'snapshot': {'consent': {'accepted': True}}}):
        assert athlete_client.post('/api/training-week/shares', json=consent_payload() | fields).status_code == 422
    assert shares(session) == 0


@pytest.mark.parametrize('ttl', ['0', '169', 'invalid'])
def test_invalid_expiry_configuration_never_publishes(athlete_client, session, monkeypatch, ttl):
    monkeypatch.setenv('WEEKLY_SHARE_TOKEN_TTL_HOURS', ttl)
    assert athlete_client.post('/api/training-week/shares', json=consent_payload()).status_code == 422
    assert shares(session) == 0


def test_owner_recovers_encrypted_link_after_new_request(athlete_client, session, caplog):
    result = athlete_client.post('/api/training-week/shares', json=consent_payload('2026-10-02')).json()
    row = session.get(WeeklyShare, UUID(result['id']))
    assert result['path'].split('/')[-1] not in str(row.snapshot)
    response = athlete_client.get('/api/training-week/shares?day=2026-10-02')
    assert response.json()['items'][0]['path'] == result['path']
    assert response.headers['cache-control'] == 'no-store'
    assert result['path'].split('/')[-1] not in caplog.text
    assert WeeklySummaryService(session, uuid4()).list_shares(date(2026, 10, 2)) == []
    athlete_client.delete('/api/training-week/shares/' + result['id'])
    assert athlete_client.get('/api/training-week/shares?day=2026-10-02').json()['items'] == []


@pytest.mark.parametrize('failure', ['missing', 'invalid', 'tampered', 'expired', 'inactive', 'historical'])
def test_link_recovery_fails_closed(athlete_client, session, monkeypatch, failure):
    result = athlete_client.post('/api/training-week/shares', json=consent_payload('2026-10-02')).json()
    row = session.get(WeeklyShare, UUID(result['id']))
    if failure == 'missing': monkeypatch.delenv('WEEKLY_SHARE_ENCRYPTION_KEY')
    elif failure == 'invalid': monkeypatch.setenv('WEEKLY_SHARE_ENCRYPTION_KEY', 'invalid')
    elif failure == 'tampered': row.snapshot = row.snapshot | {'protected_link': {'version': '1', 'ciphertext': 'invalid'}}
    elif failure == 'expired': row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    elif failure == 'inactive': session.get(User, DEMO_ATHLETE_ID).is_active = False
    elif failure == 'historical': row.snapshot = {'consent': row.snapshot['consent']}
    session.commit()
    items = WeeklySummaryService(session, DEMO_ATHLETE_ID).list_shares(date(2026, 10, 2))
    assert not items or items[0]['path'] is None


def test_missing_link_key_prevents_new_publication(athlete_client, session, monkeypatch):
    monkeypatch.delenv('WEEKLY_SHARE_ENCRYPTION_KEY')
    response = athlete_client.post('/api/training-week/shares', json=consent_payload())
    assert response.status_code == 503
    assert shares(session) == 0


def test_link_key_rotation_preserves_old_links_and_binds_owner(athlete_client, session, monkeypatch):
    import json, os
    from cryptography.fernet import Fernet
    from app.services.weekly_summary import recovered_path
    old_key = os.environ['WEEKLY_SHARE_ENCRYPTION_KEY']
    result = athlete_client.post('/api/training-week/shares', json=consent_payload('2026-10-02')).json()
    row = session.get(WeeklyShare, UUID(result['id']))
    monkeypatch.delenv('WEEKLY_SHARE_ENCRYPTION_KEY')
    monkeypatch.setenv('WEEKLY_SHARE_KEY_VERSION', '2')
    monkeypatch.setenv('WEEKLY_SHARE_ENCRYPTION_KEYS', json.dumps({'1': old_key, '2': Fernet.generate_key().decode()}))
    assert recovered_path(row) == result['path']
    another = athlete_client.post('/api/training-week/shares', json=consent_payload('2026-10-02')).json()
    assert session.get(WeeklyShare, UUID(another['id'])).snapshot['protected_link']['version'] == '2'
    row.athlete_id = uuid4()
    assert recovered_path(row) is None
    session.rollback()
