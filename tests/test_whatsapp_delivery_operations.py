"""S08: fake Kapso only, durable PostgreSQL delivery and admin recovery."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from uuid import uuid4
from urllib.error import HTTPError, URLError
import socket
import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from app.database import SessionLocal
from app.models import User, AdminAudit
from app.seed import DEMO_ATHLETE_ID
from app.whatsapp.identity import now, IdentityResolver
from app.whatsapp.kapso import KapsoWhatsAppProvider
from app.whatsapp.models import WhatsAppInbox, WhatsAppOutbox, WhatsAppUsage
from app.whatsapp.operations import clear_credit, recover, credit_status, ClearancePayload, RecoveryPayload
from app.whatsapp.provider import ProviderError
from app.whatsapp.queue import dispatch_one, reply
from app.whatsapp.security import Vault
from app.whatsapp.worker import process_one
from tests.test_whatsapp_foundation import link
from tests.whatsapp_helpers import configure, payload, webhook, FakeProvider, PHONE

@pytest.fixture(autouse=True)
def channel(monkeypatch):
    configure(monkeypatch)

class Failure(FakeProvider):
    def __init__(self, error):
        super().__init__(); self.error = error; self.calls = 0
    def send(self, *args):
        self.calls += 1
        raise self.error

def queued(client, session, text='ayuda'):
    link(session); body=payload(text)
    assert webhook(client, body).json()['accepted']==1
    assert process_one(FakeProvider(), Vault())
    session.expire_all()
    return session.scalar(select(WhatsAppOutbox)), body

def admin(session):
    return session.scalar(select(User).where(User.role=='SYSTEM_ADMIN'))

def clear(session):
    data=ClearancePayload(request_id=uuid4(), evidence_reference=uuid4(), balance_verified=True)
    return clear_credit(session,admin(session),data), data

def recovery_payload(clearance):
    return RecoveryPayload(request_id=uuid4(), clearance_id=clearance['clearance_id'], evidence_reference=uuid4(), rejection_verified=True)

@pytest.mark.parametrize('status,code,retry,uncertain', [(402,'insufficient_credits',False,False),(429,'rate_limited',True,False),(500,'provider_http_error',False,True),(503,'provider_http_error',False,True),(408,'provider_http_error',False,True),(400,'provider_http_error',False,False)])
def test_adapter_http_classification_without_reading_private_body(status,code,retry,uncertain):
    class ForbiddenBody:
        def read(self,*args): raise AssertionError('must not read error body')
        def close(self): pass
    def opener(*args,**kwargs):
        raise HTTPError('https://api.kapso.ai',status,'private reason',{'Retry-After':'80'},ForbiddenBody())
    with pytest.raises(ProviderError) as error:
        KapsoWhatsAppProvider(opener=opener).send(PHONE,'PRIVATE')
    assert (error.value.code,error.value.safe_retry,error.value.uncertain)==(code,retry,uncertain)
    if status==429: assert error.value.retry_after==80
    assert 'PRIVATE' not in str(error.value) and 'private reason' not in str(error.value)

@pytest.mark.parametrize('reason,retry,uncertain', [(socket.gaierror(),True,False),(ConnectionRefusedError(),True,False),(TimeoutError(),False,True)])
def test_adapter_connection_evidence(reason,retry,uncertain):
    def opener(*args,**kwargs): raise URLError(reason)
    with pytest.raises(ProviderError) as error: KapsoWhatsAppProvider(opener=opener).send(PHONE,'fixture')
    assert (error.value.safe_retry,error.value.uncertain)==(retry,uncertain)

@pytest.mark.parametrize('error,state', [(ProviderError('pre_send_timeout',safe_retry=True,not_sent=True),'RETRY'),(ProviderError('timeout',uncertain=True),'UNCERTAIN'),(ProviderError('provider_http_error',uncertain=True),'UNCERTAIN'),(TimeoutError('PRIVATE'),'UNCERTAIN'),(ProviderError('unclassified'),'UNCERTAIN')])
def test_dispatch_failure_policy(client,session,error,state):
    row,_=queued(client,session); provider=Failure(error)
    assert dispatch_one(session,provider,Vault()) and row.state==state
    assert row.attempts==1 and row.payload_encrypted and row.lease_until is None
    if state=='UNCERTAIN': assert not dispatch_one(session,provider,Vault())
    assert provider.calls==1
    reservation=session.scalar(select(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))
    assert reservation.reservation_state=='UNCERTAIN'

def test_402_circuit_preserves_pending_and_reservations(client,session,caplog):
    row,_=queued(client,session); provider=Failure(ProviderError('insufficient_credits',not_sent=True))
    assert dispatch_one(session,provider,Vault())
    assert row.state=='FAILED' and row.error_code=='insufficient_credits' and row.payload_encrypted
    assert credit_status(session)['blocked']
    extra=WhatsAppOutbox(id=uuid4(),dedupe_key=str(uuid4())+':reply',action='reply',payload_encrypted=Vault().encrypt({'phone':PHONE,'text':'PRIVATE'}),key_version=Vault().version,expires_at=now()+timedelta(hours=1))
    session.add(extra);session.commit()
    assert not dispatch_one(session,provider,Vault()) and extra.state=='PENDING'
    assert provider.calls==1 and session.scalar(select(func.count()).select_from(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))==1
    assert 'insufficient_credits' in caplog.text and PHONE not in caplog.text and 'PRIVATE' not in caplog.text

def test_429_five_attempts_and_retry_after(client,session):
    row,_=queued(client,session); provider=Failure(ProviderError('rate_limited',safe_retry=True,not_sent=True,retry_after=80))
    for attempt in range(1,6):
        before=now(); assert dispatch_one(session,provider,Vault())
        assert row.attempts==attempt and row.next_attempt_at>=before+timedelta(seconds=max(80,min(300,10*2**attempt)))
        assert row.state==('FAILED' if attempt==5 else 'RETRY')
        row.next_attempt_at=now();session.commit()
    assert not dispatch_one(session,provider,Vault()) and provider.calls==5
    assert session.scalar(select(func.count()).select_from(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))==5

@pytest.mark.parametrize('lease', [None, 'expired'])
def test_restart_and_expired_lease_never_replay(client,session,lease):
    row,_=queued(client,session); row.state='SENDING';row.attempts=1
    row.lease_until=now()-timedelta(seconds=1) if lease else None;session.commit();session.close()
    with SessionLocal() as restarted:
        provider=FakeProvider();assert not dispatch_one(restarted,provider,Vault())
        saved=restarted.get(WhatsAppOutbox,row.id)
        assert saved.state=='UNCERTAIN' and saved.error_code=='send_interrupted' and not provider.sent

def test_fragment_failure_holds_successors_until_individual_recovery(client,session):
    row,_=queued(client,session); inbox=session.scalar(select(WhatsAppInbox));session.delete(row);session.commit()
    reply(session,Vault(),inbox,PHONE,'A'*1000+'B'*1000+'C'*1000+'D'*1000+'E'*1000,athlete_id=DEMO_ATHLETE_ID)
    session.commit();fragments=list(session.scalars(select(WhatsAppOutbox).order_by(WhatsAppOutbox.dedupe_key)))
    stamp=now()
    for fragment in fragments: fragment.created_at=stamp
    session.commit();good=FakeProvider()
    assert dispatch_one(session,good,Vault()) and good.sent[0][1]=='A'*1000
    assert dispatch_one(session,Failure(ProviderError('insufficient_credits',not_sent=True)),Vault())
    assert fragments[1].state=='FAILED' and all(x.state=='PENDING' and x.payload_encrypted for x in fragments[2:])
    clearance,_=clear(session)
    assert not dispatch_one(session,good,Vault())
    recover(session,admin(session),fragments[1].id,recovery_payload(clearance))
    for _ in range(4): assert dispatch_one(session,good,Vault())
    assert [message[1][0] for message in good.sent]==list('ABCDE')
    assert all(x.state=='SENT' for x in fragments)

@pytest.mark.parametrize('state', ['RETRY','UNCERTAIN','FAILED'])
def test_fragment_predecessor_blocks_without_consuming(client,session,state):
    row,_=queued(client,session);inbox=session.scalar(select(WhatsAppInbox))
    row.state=state;row.next_attempt_at=now()+timedelta(hours=1);session.commit()
    reply(session,Vault(),inbox,PHONE,'next',athlete_id=DEMO_ATHLETE_ID,action='z-successor');session.commit()
    provider=FakeProvider();assert not dispatch_one(session,provider,Vault()) and not provider.sent
    assert session.scalar(select(func.count()).select_from(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))==0

def test_authorized_recovery_is_individual_idempotent_and_audited(client,session):
    row,body=queued(client,session);identifier=row.id;dedupe=row.dedupe_key;expiry=row.expires_at
    dispatch_one(session,Failure(ProviderError('insufficient_credits',not_sent=True)),Vault())
    clearance,clear_payload=clear(session)
    assert row.state=='FAILED' and clear_credit(session,admin(session),clear_payload)['already_authorized']
    data=recovery_payload(clearance)
    assert not recover(session,admin(session),row.id,data)['already_authorized']
    assert recover(session,admin(session),row.id,data)['already_authorized']
    provider=FakeProvider();assert dispatch_one(session,provider,Vault())
    assert row.id==identifier and row.dedupe_key==dedupe and row.expires_at==expiry and row.attempts==2
    assert recover(session,admin(session),row.id,data)['already_authorized']
    assert not dispatch_one(session,provider,Vault()) and len(provider.sent)==1
    assert webhook(client,body).json()['accepted']==0 and not process_one(provider,Vault())
    audit=session.scalar(select(AdminAudit).where(AdminAudit.action=='WHATSAPP_RECOVERY'))
    assert audit.actor_id==admin(session).id and audit.target==str(identifier)
    assert PHONE not in str(audit.changes) and 'text' not in audit.changes

@pytest.mark.parametrize('condition', ['uncertain','provider_id','expired','purged','inactive','revoked','anonymous','wrong_clearance','unverified'])
def test_recovery_denies_insufficient_evidence(client,session,condition):
    row,_=queued(client,session);dispatch_one(session,Failure(ProviderError('insufficient_credits',not_sent=True)),Vault())
    clearance,_=clear(session); data=recovery_payload(clearance)
    if condition=='uncertain': row.state='UNCERTAIN'
    elif condition=='provider_id': row.provider_message_id='known-send'
    elif condition=='expired': row.expires_at=now()-timedelta(seconds=1)
    elif condition=='purged': row.payload_encrypted=None
    elif condition=='inactive': session.get(User,DEMO_ATHLETE_ID).is_active=False
    elif condition=='revoked': IdentityResolver(session,Vault()).revoke(DEMO_ATHLETE_ID)
    elif condition=='anonymous': row.athlete_id=None
    elif condition=='wrong_clearance': data.clearance_id=uuid4()
    elif condition=='unverified': data.rejection_verified=False
    session.commit()
    with pytest.raises(HTTPException): recover(session,admin(session),row.id,data)
    session.rollback()
    assert session.scalar(select(func.count()).select_from(AdminAudit).where(AdminAudit.action=='WHATSAPP_RECOVERY'))==0

def test_concurrent_workers_only_one_physical_send(client,session):
    row,_=queued(client,session); started=Event();finish=Event()
    class Blocking(FakeProvider):
        def send(self,*args):
            started.set();assert finish.wait(10);return super().send(*args)
    provider=Blocking()
    def run():
        with SessionLocal() as worker: return dispatch_one(worker,provider,Vault())
    with ThreadPoolExecutor(max_workers=2) as pool:
        first=pool.submit(run)
        try:
            assert started.wait(10)
            assert pool.submit(run).result(timeout=10) is False
        finally: finish.set()
        assert first.result(timeout=10)
    assert len(provider.sent)==1

def test_admin_operations_acl_origin_and_minimal_metadata(athlete_client,session,monkeypatch):
    row,_=queued(athlete_client,session)
    dispatch_one(session,Failure(ProviderError('insufficient_credits',not_sent=True)),Vault())
    assert athlete_client.get('/api/admin/whatsapp/operations').status_code==403
    username='admin'
    assert athlete_client.post('/api/auth/login',json={'username':username,'password':'demo1234'}).status_code==200
    status=athlete_client.get('/api/admin/whatsapp/operations')
    assert status.status_code==200 and status.json()['credit_blocked']
    assert PHONE not in status.text and 'payload_encrypted' not in status.text and 'key_version' not in status.text
    data={'request_id':str(uuid4()),'evidence_reference':str(uuid4()),'balance_verified':True}
    monkeypatch.setenv('WEB_ALLOWED_ORIGINS','http://testserver')
    assert athlete_client.post('/api/admin/whatsapp/credit-clearances',json=data,headers={'Origin':'https://evil.invalid'}).status_code==403
    assert athlete_client.post('/api/admin/whatsapp/credit-clearances',json=data,headers={'Origin':'http://testserver'}).status_code==200

def test_expiration_keeps_privacy_ttl_during_credit_block(client,session):
    row,_=queued(client,session);dispatch_one(session,Failure(ProviderError('insufficient_credits',not_sent=True)),Vault())
    inbox=session.scalar(select(WhatsAppInbox));reply(session,Vault(),inbox,PHONE,'private successor',athlete_id=DEMO_ATHLETE_ID,action='z-next');session.commit()
    pending=session.scalar(select(WhatsAppOutbox).where(WhatsAppOutbox.state=='PENDING'))
    pending.expires_at=now()-timedelta(seconds=1);session.commit()
    assert not dispatch_one(session,FakeProvider(),Vault())
    assert pending.state=='EXPIRED' and pending.payload_encrypted is None

def test_manual_recovery_cannot_override_exhausted_budget(client,session,monkeypatch):
    row,_=queued(client,session);dispatch_one(session,Failure(ProviderError('insufficient_credits',not_sent=True)),Vault())
    clearance,_=clear(session);recover(session,admin(session),row.id,recovery_payload(clearance))
    monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0.02')
    provider=FakeProvider();assert dispatch_one(session,provider,Vault())
    assert row.state=='FAILED' and row.error_code=='consumption_rejected' and not provider.sent

def test_pending_deactivated_account_never_sends(client,session):
    row,_=queued(client,session);session.get(User,DEMO_ATHLETE_ID).is_active=False;session.commit()
    provider=FakeProvider();assert dispatch_one(session,provider,Vault())
    assert row.state=='CANCELLED' and row.payload_encrypted is None and not provider.sent
    assert session.scalar(select(func.count()).select_from(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))==0

def test_unknown_provider_error_never_persists_private_details(client,session,caplog):
    row,_=queued(client,session)
    dispatch_one(session,Failure(ProviderError('PRIVATE '+PHONE,uncertain=True)),Vault())
    assert row.error_code=='provider_error' and row.state=='UNCERTAIN'
    assert 'PRIVATE' not in caplog.text and PHONE not in caplog.text

def test_missing_provider_identifier_is_uncertain(client,session):
    row,_=queued(client,session)
    class Missing(FakeProvider):
        def send(self,*args): return None
    dispatch_one(session,Missing(),Vault())
    assert row.state=='UNCERTAIN' and row.provider_message_id is None


def test_worker_interrupted_inside_send_keeps_durable_unknown_reservation(client,session):
    row,_=queued(client,session)
    class Interrupted(FakeProvider):
        def send(self,*args): raise SystemExit('simulated worker termination')
    with pytest.raises(SystemExit): dispatch_one(session,Interrupted(),Vault())
    session.rollback();session.refresh(row)
    assert row.state=='SENDING' and row.attempts==1
    reservation=session.scalar(select(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))
    assert reservation.reservation_state=='RESERVED'
    row.lease_until=now()-timedelta(seconds=1);session.commit()
    provider=FakeProvider();assert not dispatch_one(session,provider,Vault())
    session.refresh(reservation)
    assert row.state=='UNCERTAIN' and reservation.reservation_state=='UNCERTAIN' and not provider.sent


def test_late_failure_receipt_cannot_erase_confirmed_read(client,session):
    row,_=queued(client,session);dispatch_one(session,FakeProvider(),Vault())
    for event in ('read','failed','delivered'):
        assert webhook(client,payload(identifier=row.provider_message_id,event=event),event=event).json()['accepted']==1
        assert process_one(FakeProvider(),Vault())
    session.refresh(row)
    assert row.state=='READ' and row.error_code is None


def test_different_athlete_continues_while_first_response_uncertain(client,session):
    from tests.test_consumption_limits import second_athlete
    row,_=queued(client,session);dispatch_one(session,Failure(ProviderError('timeout',uncertain=True)),Vault())
    other=second_athlete(session);other_phone='+56922223333';link(session,other,other_phone)
    assert webhook(client,payload('ayuda',phone=other_phone)).json()['accepted']==1
    assert process_one(FakeProvider(),Vault())
    provider=FakeProvider();assert dispatch_one(session,provider,Vault())
    assert len(provider.sent)==1 and provider.sent[0][0]==other_phone and row.state=='UNCERTAIN'


def test_anonymous_conversation_order_survives_unlinked_identity(client,session):
    assert webhook(client,payload()).json()['accepted']==1;assert process_one(FakeProvider(),Vault())
    first=session.scalar(select(WhatsAppOutbox));dispatch_one(session,Failure(ProviderError('timeout',uncertain=True)),Vault())
    assert webhook(client,payload()).json()['accepted']==1;assert process_one(FakeProvider(),Vault())
    provider=FakeProvider();assert not dispatch_one(session,provider,Vault()) and not provider.sent
    assert first.state=='UNCERTAIN'


def test_expired_old_response_does_not_block_new_conversation(client,session):
    row,_=queued(client,session);dispatch_one(session,Failure(ProviderError('timeout',uncertain=True)),Vault())
    row.expires_at=now()-timedelta(seconds=1);session.commit()
    assert webhook(client,payload()).json()['accepted']==1;assert process_one(FakeProvider(),Vault())
    provider=FakeProvider();assert dispatch_one(session,provider,Vault()) and len(provider.sent)==1
    assert row.state=='UNCERTAIN'


def test_manual_clearance_and_recovery_require_active_admin_and_truthful_attestation(client,session):
    row,_=queued(client,session);dispatch_one(session,Failure(ProviderError('insufficient_credits',not_sent=True)),Vault())
    data=ClearancePayload(request_id=uuid4(),evidence_reference=uuid4(),balance_verified=False)
    with pytest.raises(HTTPException): clear_credit(session,admin(session),data)
    session.rollback();assert credit_status(session)['blocked']
    data.balance_verified=True
    with pytest.raises(HTTPException): clear_credit(session,session.get(User,DEMO_ATHLETE_ID),data)
    session.rollback();clearance,_=clear(session); recovery=recovery_payload(clearance)
    actor=admin(session);actor.is_active=False;session.commit()
    with pytest.raises(HTTPException): recover(session,actor,row.id,recovery)
    session.rollback();assert row.state=='FAILED'


def test_recovery_request_id_conflict_cannot_reauthorize(client,session):
    row,_=queued(client,session);dispatch_one(session,Failure(ProviderError('insufficient_credits',not_sent=True)),Vault())
    clearance,_=clear(session);data=recovery_payload(clearance);recover(session,admin(session),row.id,data)
    data.evidence_reference=uuid4()
    with pytest.raises(HTTPException) as error: recover(session,admin(session),row.id,data)
    assert error.value.status_code==409;session.rollback()
    assert session.scalar(select(func.count()).select_from(AdminAudit).where(AdminAudit.action=='WHATSAPP_RECOVERY'))==1
