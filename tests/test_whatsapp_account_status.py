"""S02 account lifecycle; all providers are simulated on disposable PostgreSQL."""
from uuid import uuid4
import pytest
from sqlalchemy import select, func
from sqlalchemy.exc import OperationalError
from app.database import SessionLocal
from app.models import User, Athlete, TrainingSession, TrainingAIUsage
from app.seed import DEMO_ATHLETE_ID
from app.whatsapp.identity import IdentityResolver, active_account
from app.whatsapp.models import AthleteIdentity, LinkChallenge, ConversationState, WhatsAppInbox, WhatsAppOutbox
from app.whatsapp.queue import dispatch_one
from app.whatsapp.worker import process_one
from app.whatsapp.security import Vault, ChannelError
from app.services.training_usage import report_usage
from tests.test_whatsapp_foundation import link
from tests.test_whatsapp_capture import channel, step, count, button, confirm
from tests.test_administration import admin
from tests.whatsapp_helpers import configure, payload, webhook, FakeProvider, PHONE


def status(client, active):
    admin(client)
    user = next(u for u in client.get('/api/admin/users').json()['items'] if u['id'] == str(DEMO_ATHLETE_ID))
    data = {k: user[k] for k in ('name', 'username', 'email', 'role', 'plan')}
    data['is_active'] = active
    response = client.put('/api/admin/users/' + user['id'], json=data)
    assert response.status_code == 200, response.text


def test_active_registers(client, channel, session):
    initial = count(session)
    step(client, channel)
    confirm(client, channel, session)
    assert count(session) == initial + 1
    assert len(channel[1]) == 1


@pytest.mark.parametrize('kind,text', [('text','Hoy hice 4 rondas'), ('image','WOD'), ('audio',''), ('text','resumen semana')])
def test_inactive_inbound_no_ai_or_reply(client, channel, session, monkeypatch, kind, text):
    status(client, False)
    monkeypatch.setattr('app.services.training_service.transcribe', lambda *_: pytest.fail('Inactive transcription'))
    channel[0].download_media = lambda *_: pytest.fail('Inactive download')
    initial = count(session)
    step(client, channel, text, kind=kind, identifier='inactive.same')
    assert not channel[1]
    assert count(session) == initial
    assert not session.scalars(select(WhatsAppOutbox)).all()
    row = session.scalar(select(WhatsAppInbox))
    assert row.payload_encrypted is None and row.error_code == 'account_inactive'
    assert webhook(client, payload(text, kind=kind, identifier='inactive.same')).json()['accepted'] == 0
    assert not process_one(channel[0], Vault())
    assert not channel[0].sent


def test_inactive_link_challenges_blocked(client, channel, session):
    resolver = IdentityResolver(session, Vault())
    code = resolver.issue(DEMO_ATHLETE_ID)['code'].split(' ', 1)[1]
    session.commit()
    status(client, False)
    session.expire_all()
    with pytest.raises(ChannelError, match='account_inactive'):
        resolver.issue(DEMO_ATHLETE_ID)
    assert resolver.verify(code, PHONE) is None
    assert resolver.resolve(PHONE) is None
    session.rollback()


@pytest.mark.parametrize('pending', ['PENDING', 'RETRY', 'SENDING'])
def test_deactivation_cancels_sensitive_pending(client, channel, session, pending):
    step(client, channel)
    row = session.scalar(select(WhatsAppOutbox))
    row.state = pending
    session.commit()
    status(client, False)
    session.expire_all()
    row = session.get(WhatsAppOutbox, row.id)
    assert row.state == 'CANCELLED' and row.payload_encrypted is None
    assert not dispatch_one(session, channel[0], Vault())
    assert not channel[0].sent
    state = session.get(ConversationState, (DEMO_ATHLETE_ID, 'whatsapp'))
    assert state.pending_action is None and state.payload_minimized is None


def test_queued_inbound_cancelled_before_processing(client, channel, session):
    assert webhook(client, payload('Hoy hice 4 rondas')).status_code == 200
    status(client, False)
    assert not process_one(channel[0], Vault())
    session.expire_all()
    row = session.scalar(select(WhatsAppInbox))
    assert row.state == 'CANCELLED' and row.payload_encrypted is None
    assert not channel[1]


def test_reactivation_requires_fresh_identity_and_no_old_actions(client, channel, session):
    step(client, channel)
    old_button = button(session, 'save')
    initial = count(session)
    status(client, False)
    status(client, True)
    session.expire_all()
    resolver = IdentityResolver(session, Vault())
    assert resolver.resolve(PHONE) is None
    step(client, channel, '', kind='interactive', action=old_button)
    assert count(session) == initial
    link(session)
    step(client, channel, '', kind='interactive', action=old_button)
    assert count(session) == initial
    step(client, channel)
    confirm(client, channel, session)
    assert count(session) == initial + 1


def test_dispatch_rechecks_inactive_even_if_changed_outside_admin(client, channel, session):
    step(client, channel)
    session.get(User, DEMO_ATHLETE_ID).is_active = False
    session.commit()
    assert dispatch_one(session, channel[0], Vault())
    row = session.scalar(select(WhatsAppOutbox))
    assert row.state == 'CANCELLED' and row.payload_encrypted is None
    assert IdentityResolver(session, Vault()).resolve(PHONE) is None
    assert session.scalar(select(AthleteIdentity)).revoked_at is not None
    assert not channel[0].sent


def test_claim_then_deactivate_reactivate_never_replays(client, channel, session, monkeypatch):
    step(client, channel)
    def intervening(db, identifier):
        with SessionLocal() as other:
            other.get(User, identifier).is_active = False
            IdentityResolver(other, Vault()).revoke(identifier)
            other.commit()
            other.get(User, identifier).is_active = True
            other.commit()
            link(other)
        return active_account(db, identifier)
    monkeypatch.setattr('app.whatsapp.queue.active_account', intervening)
    assert dispatch_one(session, channel[0], Vault())
    assert not channel[0].sent
    session.expire_all()
    assert session.scalar(select(WhatsAppOutbox)).state == 'CANCELLED'


def assert_account_locked():
    with SessionLocal() as other:
        with pytest.raises(OperationalError):
            other.scalar(select(User).where(User.id == DEMO_ATHLETE_ID).with_for_update(nowait=True))
        other.rollback()


def test_account_lock_survives_ai_accounting_commits(client, channel, monkeypatch):
    from tests.test_whatsapp_capture import draft
    def interpreter(*_):
        report_usage('fixture')
        assert_account_locked()
        return draft()
    monkeypatch.setattr('app.services.training_service.interpret', interpreter)
    step(client, channel)
    with SessionLocal() as db:
        assert db.scalar(select(TrainingAIUsage)).status == 'COMPLETED'


def test_account_lock_held_during_provider_send(client, channel, session):
    step(client, channel)
    send = channel[0].send
    def locked_send(*args):
        assert_account_locked()
        return send(*args)
    channel[0].send = locked_send
    assert dispatch_one(session, channel[0], Vault())
    assert len(channel[0].sent) == 1


def test_other_active_identity_unaffected(client, channel, session):
    status(client, False)
    other = uuid4()
    session.add(User(id=other, name='Fixture other', role='ATHLETE'))
    session.flush()
    session.add(Athlete(user_id=other))
    session.commit()
    # Reassigned valid identity wins over historical inactive phone association.
    link(session, athlete_id=other)
    step(client, channel)
    assert len(channel[1]) == 1
    row = session.scalar(select(WhatsAppOutbox))
    assert row.athlete_id == other
    assert dispatch_one(session, channel[0], Vault())
    assert len(channel[0].sent) == 1

@pytest.mark.parametrize('kind', ['image', 'audio'])
def test_active_media_retains_account_lock_through_ai(client, channel, session, monkeypatch, kind):
    from io import BytesIO
    from PIL import Image
    from app.whatsapp.provider import DownloadedMedia
    from tests.test_whatsapp_capture import draft
    if kind == 'image':
        buf = BytesIO()
        Image.new('RGB', (24,24)).save(buf, format='PNG')
        media = DownloadedMedia(buf.getvalue(), 'image/png')
    else:
        media = DownloadedMedia(b'fixture-audio', 'audio/wav')
    def download(*_):
        assert_account_locked()
        return media
    def transcriber(*_):
        report_usage('fixture-transcription')
        assert_account_locked()
        return 'Hoy hice 4 rondas de remo'
    def interpreter(*_):
        report_usage('fixture-interpretation')
        assert_account_locked()
        return draft()
    channel[0].download_media = download
    monkeypatch.setattr('app.services.training_service.transcribe', transcriber)
    monkeypatch.setattr('app.services.training_service.interpret', interpreter)
    initial = count(session)
    step(client, channel, 'Hoy hice 4 rondas' if kind == 'image' else '', kind=kind)
    confirm(client, channel, session)
    assert count(session) == initial + 1


def test_challenge_cached_before_deactivation_cannot_revive(session, monkeypatch):
    configure(monkeypatch)
    resolver = IdentityResolver(session, Vault())
    code = resolver.issue(DEMO_ATHLETE_ID)['code'].split(' ',1)[1]
    session.commit()
    def intervening(db, identifier):
        with SessionLocal() as other:
            other.get(User, identifier).is_active = False
            IdentityResolver(other, Vault()).revoke(identifier)
            other.commit()
            other.get(User, identifier).is_active = True
            other.commit()
        return active_account(db, identifier)
    monkeypatch.setattr('app.whatsapp.identity.active_account', intervening)
    assert resolver.verify(code, PHONE) is None
    assert resolver.resolve(PHONE) is None
    session.rollback()


def test_claimed_inbox_cancelled_during_reactivation(client, channel, session, monkeypatch):
    from app.whatsapp import runtime
    handle = runtime.handle
    def intervening(db, inbox, message, vault, provider):
        status(client, False)
        status(client, True)
        return handle(db, inbox, message, vault, provider)
    monkeypatch.setattr(runtime, 'handle', intervening)
    step(client, channel)
    assert not channel[1]
    session.expire_all()
    row = session.scalar(select(WhatsAppInbox))
    assert row.state == 'CANCELLED' and row.payload_encrypted is None
    assert not session.scalars(select(WhatsAppOutbox)).all()


def test_inactive_cannot_confirm_old_proposal(client, channel, session):
    step(client, channel)
    old_button = button(session, 'save')
    initial = count(session)
    status(client, False)
    step(client, channel, '', kind='interactive', action=old_button)
    assert count(session) == initial
    assert len(channel[1]) == 1  # Only the proposal before deactivation.
    session.expire_all()
    assert all(row.state == 'CANCELLED' for row in session.scalars(select(WhatsAppOutbox)))


def test_photo_ai_failure_retains_media_and_minimal_accounting(client, channel, session, monkeypatch):
    from io import BytesIO
    from PIL import Image
    from app.models import TrainingImage
    from app.whatsapp.provider import DownloadedMedia
    from tests.test_whatsapp_capture import draft, state, snapshot
    buf = BytesIO()
    Image.new('RGB', (24,24)).save(buf, format='PNG')
    channel[0].download_media = lambda *_: DownloadedMedia(buf.getvalue(), 'image/png')
    def failed(*_):
        report_usage('fixture-failed')
        assert_account_locked()
        raise ValueError('fixture invalid interpretation')
    monkeypatch.setattr('app.services.training_service.interpret', failed)
    initial = count(session)
    step(client, channel, 'Hoy hice 4 rondas', kind='image')
    assert state(session).state == 'CLARIFY'
    assert session.scalar(select(TrainingImage)) is not None
    assert snapshot(state(session), Vault()).get('image_id')
    assert session.scalar(select(TrainingAIUsage)).status == 'FAILED'
    monkeypatch.setattr('app.services.training_service.interpret', lambda *_: draft())
    step(client, channel, '4 rondas de remo')
    confirm(client, channel, session)
    assert count(session) == initial + 1
