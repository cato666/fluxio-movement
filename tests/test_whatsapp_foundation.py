from datetime import timedelta
import json
from uuid import UUID, uuid4
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from app.database import engine
from app.models import Athlete, User
from app.seed import DEMO_ATHLETE_ID
from app.whatsapp.identity import IdentityResolver, now
from app.whatsapp.kapso import KapsoWhatsAppProvider
from app.whatsapp.models import AthleteIdentity, LinkChallenge, WhatsAppInbox, WhatsAppOutbox, ConversationState
from app.whatsapp.provider import ProviderError
from app.whatsapp.queue import dispatch_one
from app.whatsapp.security import Vault, ChannelError
from app.whatsapp.worker import process_one
from tests.whatsapp_helpers import PHONE, FakeProvider, configure, payload, webhook


@pytest.fixture(autouse=True)
def channel(monkeypatch):
    configure(monkeypatch)


def link(session, athlete_id=DEMO_ATHLETE_ID, phone=PHONE):
    resolver = IdentityResolver(session, Vault())
    code = resolver.issue(athlete_id)['code'].split(' ', 1)[1]
    session.commit()
    assert resolver.verify(code, phone) == athlete_id
    session.commit()
    return resolver


def test_identity_verified_encrypted_lookup_and_revocation(session):
    resolver = link(session)
    assert resolver.resolve(PHONE) == DEMO_ATHLETE_ID
    assert resolver.resolve('+56922223333') is None
    row = session.scalar(select(AthleteIdentity))
    assert PHONE not in row.phone_encrypted and PHONE not in row.phone_hash
    assert Vault().decrypt(row.phone_encrypted, row.key_version) == PHONE
    resolver.revoke(DEMO_ATHLETE_ID); session.commit()
    assert resolver.resolve(PHONE) is None


def test_link_code_single_use_expiration_and_attempt_limit(session):
    resolver = IdentityResolver(session, Vault())
    issued = resolver.issue(DEMO_ATHLETE_ID)
    code = issued['code'].split(' ', 1)[1]
    session.commit()
    wrong = code.split('.')[0] + '.wrong'
    for _ in range(5):
        assert resolver.verify(wrong, PHONE) is None
    assert resolver.verify(code, PHONE) is None
    session.commit()
    issued = resolver.issue(DEMO_ATHLETE_ID)
    code = issued['code'].split(' ', 1)[1]
    session.flush()
    challenge = session.get(LinkChallenge, UUID(code.split('.')[0]))
    challenge.expires_at = now() - timedelta(seconds=1)
    assert resolver.verify(code, PHONE) is None


def test_duplicate_phone_never_reassigns_athlete(session):
    resolver = link(session)
    other = User(id=uuid4(), name='Other', role='ATHLETE')
    session.add(other); session.flush(); session.add(Athlete(user_id=other.id)); session.commit()
    code = resolver.issue(other.id)['code'].split(' ', 1)[1]; session.commit()
    assert resolver.verify(code, PHONE) is None
    assert resolver.resolve(PHONE) == DEMO_ATHLETE_ID
    session.add(AthleteIdentity(athlete_id=other.id, phone_hash=Vault().phone_hash(PHONE),
        phone_encrypted='protected', key_version='1', verified_at=now()))
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_web_link_permissions_and_hidden_phone(athlete_client, session):
    issued = athlete_client.post('/api/whatsapp/link-challenges')
    assert issued.status_code == 201
    code = issued.json()['code']
    assert PHONE not in issued.text
    assert webhook(athlete_client, payload(code)).json()['accepted'] == 1
    assert session.scalar(select(AthleteIdentity)) is None  # ACK did not run worker.
    assert process_one(FakeProvider(), Vault())
    identity = athlete_client.get('/api/whatsapp/identity')
    assert identity.json()['linked'] and PHONE not in identity.text
    assert athlete_client.delete('/api/whatsapp/identity').json() == {'linked':False}


def test_coach_cannot_link_and_disabled_channel(coach_client, monkeypatch):
    assert coach_client.post('/api/whatsapp/link-challenges').status_code == 403
    monkeypatch.setenv('WHATSAPP_ENABLED', 'false')
    assert webhook(coach_client, payload()).status_code == 404


def test_webhook_signature_body_limit_and_configuration(client, monkeypatch):
    assert webhook(client, payload(), signature='0'*64).status_code == 401
    assert client.post('/webhooks/whatsapp/kapso', content=b'x'*(256*1024+1)).status_code == 413
    monkeypatch.delenv('WHATSAPP_ENCRYPTION_KEY')
    assert webhook(client, payload()).status_code == 503


def test_dedup_replay_and_batch_retransmission(client, session):
    body = payload()
    assert webhook(client, body).json()['accepted'] == 1
    assert webhook(client, body).json()['accepted'] == 0
    batch = {'type':'whatsapp.message.received', 'batch':True, 'data':[body, payload()]}
    assert webhook(client, batch).json()['accepted'] == 1
    for item in batch['data']:
        assert webhook(client, item).json()['accepted'] == 0
    body['message']['timestamp'] = '1'
    assert webhook(client, body).status_code == 400
    assert len(session.scalars(select(WhatsAppInbox)).all()) == 2
    assert all(PHONE not in row.payload_encrypted and 'PRIVATE NAME' not in row.payload_encrypted
               for row in session.scalars(select(WhatsAppInbox)))


@pytest.mark.parametrize('kind', ['text','image','audio','video','interactive'])
def test_normalized_types_do_not_propagate_provider_json(kind):
    message = KapsoWhatsAppProvider().normalize(json.dumps(payload(kind=kind, action='opaque')).encode(), 'whatsapp.message.received')[0]
    assert message.message_type == kind
    assert 'kapso' not in message.minimized() and 'conversation' not in message.minimized()


def test_help_durable_restart_and_single_outbox(client, session):
    link(session)
    webhook(client, payload('ayuda'))
    row = session.scalar(select(WhatsAppInbox))
    row.state, row.lease_until = 'PROCESSING', now() - timedelta(seconds=1)
    session.commit()
    provider = FakeProvider()
    assert process_one(provider, Vault())
    assert not process_one(provider, Vault())
    session.expire_all()
    assert session.scalar(select(ConversationState)).state == 'IDLE'
    assert len(session.scalars(select(WhatsAppOutbox)).all()) == 1
    assert dispatch_one(session, provider, Vault())
    assert not dispatch_one(session, provider, Vault())
    assert len(provider.sent) == 1


def test_outbox_safe_retry_and_uncertain_send(client, session):
    link(session); webhook(client, payload()); process_one(FakeProvider(), Vault())
    class Retry(FakeProvider):
        def send(self, *args):
            raise ProviderError('rate_limited', safe_retry=True)
    dispatch_one(session, Retry(), Vault())
    row = session.scalar(select(WhatsAppOutbox)); assert row.state == 'RETRY'
    row.next_attempt_at = now(); session.commit()
    class Uncertain(FakeProvider):
        def send(self, *args):
            raise ProviderError('timeout', uncertain=True)
    dispatch_one(session, Uncertain(), Vault())
    assert row.state == 'UNCERTAIN'
    assert not dispatch_one(session, FakeProvider(), Vault())


def test_stale_sending_never_retried(client, session):
    link(session); webhook(client, payload()); process_one(FakeProvider(), Vault())
    row = session.scalar(select(WhatsAppOutbox))
    row.state, row.lease_until = 'SENDING', now() - timedelta(seconds=1); session.commit()
    provider = FakeProvider(); assert not dispatch_one(session, provider, Vault())
    assert row.state == 'UNCERTAIN' and not provider.sent


def test_new_migration_roundtrip_is_additive(session):
    config = Config('alembic.ini')
    session.close()
    command.downgrade(config, '0018_training_ai_usage')
    assert 'training_sessions' in inspect(engine).get_table_names()
    assert 'athlete_identity' not in inspect(engine).get_table_names()
    command.upgrade(config, 'head')
    assert 'whatsapp_inbox' in inspect(engine).get_table_names()
    command.check(config)


def test_valid_link_code_cannot_be_reused(session):
    resolver = IdentityResolver(session, Vault())
    code = resolver.issue(DEMO_ATHLETE_ID)['code'].split(' ', 1)[1]; session.commit()
    assert resolver.verify(code, PHONE) == DEMO_ATHLETE_ID
    session.commit()
    assert resolver.verify(code, '+56922223333') is None
    assert resolver.resolve('+56922223333') is None


def test_batch_invalid_member_rolls_back_entire_accept(client, session):
    invalid = payload(); invalid['phone_number_id'] = 'other-number'
    body = {'type':'whatsapp.message.received','batch':True,'data':[payload(), invalid]}
    assert webhook(client, body).status_code == 400
    assert session.scalar(select(WhatsAppInbox)) is None


def test_status_delivery_is_deduplicated_and_does_not_regress(client, session):
    link(session); webhook(client, payload()); process_one(FakeProvider(), Vault())
    dispatch_one(session, FakeProvider(), Vault())
    status = payload(event='read', identifier='sent.1')
    assert webhook(client, status, 'read').json()['accepted'] == 1
    process_one(FakeProvider(), Vault()); session.expire_all()
    assert session.scalar(select(WhatsAppOutbox)).state == 'READ'
    assert webhook(client, status, 'read').json()['accepted'] == 0
    webhook(client, payload(event='delivered', identifier='sent.1'), 'delivered')
    process_one(FakeProvider(), Vault()); session.expire_all()
    assert session.scalar(select(WhatsAppOutbox)).state == 'READ'


def test_kapso_signature_no_trust_in_mutable_event_header():
    provider = KapsoWhatsAppProvider()
    with pytest.raises(ProviderError):
        provider.normalize(json.dumps(payload(event='sent')).encode(), 'whatsapp.message.read')


def test_kapso_send_download_errors_and_ssrf():
    class Response:
        def __init__(self, data, mime='application/json'):
            self.data, self.headers = data, {'Content-Type':mime}
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self,limit): return self.data[:limit]
    calls=[]
    def opener(request, timeout):
        calls.append(request)
        if request.data:
            return Response(b'{"messages":[{"id":"sent.1"}]}')
        if 'media_download' in request.full_url:
            assert not request.has_header('X-api-key')
            return Response(b'photo', 'image/jpeg')
        return Response(b'{"download_url":"https://api.kapso.ai/meta/whatsapp/media_download?token=fixture","file_size":5}')
    provider = KapsoWhatsAppProvider(opener=opener)
    assert provider.send(PHONE,'Propuesta',[{'id':'opaque','title':'Guardar'}]) == 'sent.1'
    assert provider.download_media('media-id',8).data == b'photo'
    with pytest.raises(ProviderError): provider._read('https://localhost/private')
    with pytest.raises(ProviderError): provider.download_media('http://localhost',8)
    def invalid(*args,**kwargs): return Response(b'not json')
    with pytest.raises(ProviderError) as error:
        KapsoWhatsAppProvider(opener=invalid).send(PHONE,'Hola')
    assert error.value.uncertain
