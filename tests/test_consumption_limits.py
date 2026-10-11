"""S06 contract gates: disposable PostgreSQL and fake providers only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Barrier
from uuid import uuid4
import logging

import pytest
from fastapi import HTTPException
from sqlalchemy import select, func, text
from alembic import command
from alembic.config import Config
from app.database import SessionLocal, engine
from app.models import User, Athlete, PlanInteraction, AdminSetting, AdminAudit
from app.seed import DEMO_ATHLETE_ID
from app.services.consumption_limits import reserve, transition, configuration, DEFAULTS, VIDEO_COSTS, clock
from app.services.training_service import TrainingService
from app.services.training_contracts import InterpretPayload, SessionPayload
from app.whatsapp.models import WhatsAppUsage, WhatsAppInbox, WhatsAppOutbox
from app.whatsapp.queue import dispatch_one
from app.whatsapp.security import Vault
from app.whatsapp.worker import process_one
from tests.test_whatsapp_capture import draft, step, state, button
from tests.test_whatsapp_foundation import link
from tests.whatsapp_helpers import configure, payload, webhook, FakeProvider


@pytest.fixture(autouse=True)
def approved(monkeypatch):
    for name, value in DEFAULTS.items():
        monkeypatch.setenv('USAGE_' + name, str(value))
    monkeypatch.setenv('USAGE_PILOT_START', clock().date().isoformat())
    for name in VIDEO_COSTS:
        monkeypatch.setenv('USAGE_' + name, '0')


def rows(session):
    session.expire_all()
    return list(session.scalars(select(PlanInteraction)))


def second_athlete(session):
    user = User(id=uuid4(), name='Synthetic S06', role='ATHLETE', plan='PAID')
    session.add(user); session.flush(); session.add(Athlete(user_id=user.id)); session.commit()
    return user.id


def fake_service(session, calls, **kwargs):
    def interpret(*args):
        calls.append('INTERPRET'); return draft()
    def transcribe(*args):
        calls.append('TRANSCRIBE'); return 'Hoy hice 4 rondas'
    return TrainingService(session, DEMO_ATHLETE_ID, interpreter=interpret, transcriber=transcribe, **kwargs)


def test_shared_daily_web_chat_and_manual_remains_available(session):
    calls=[]
    fake_service(session, calls).interpret(InterpretPayload(text='WOD'))
    fake_service(session, calls, channel='whatsapp', request_key=uuid4()).interpret(InterpretPayload(text='WOD'))
    fake_service(session, calls).interpret(InterpretPayload(text='Correction'))
    with pytest.raises(HTTPException) as failure:
        fake_service(session, calls, channel='whatsapp').interpret(InterpretPayload(text='WOD'))
    assert failure.value.status_code == 429 and len(calls) == 3
    session.rollback()
    service=TrainingService(session, DEMO_ATHLETE_ID)
    saved=service.create(SessionPayload(trained_on=clock().date(), title='Manual', workout='3 rounds'))
    assert service.detail(saved['id'])['workout']=='3 rounds' and len(rows(session)) == 3


@pytest.mark.parametrize('operation', ['INTERPRET','TRANSCRIBE','ANALYZE'])
def test_exact_daily_operation_limits(session, operation):
    limit=int(DEFAULTS[operation+'_DAILY'])
    for _ in range(limit):
        identifier=reserve(session, DEMO_ATHLETE_ID, operation)
        transition(identifier,'STARTED'); transition(identifier,'CONFIRMED'); session.commit()
    with pytest.raises(HTTPException) as failure:
        reserve(session,DEMO_ATHLETE_ID,operation)
    assert failure.value.status_code==429 and len(rows(session))==limit


def test_audio_two_distinct_operations_same_inbox_and_replay(session):
    calls=[]; key=uuid4(); service=fake_service(session,calls,request_key=key,channel='whatsapp')
    service.transcribe(b'fixture'); service.interpret(InterpretPayload(text='WOD'))
    assert calls==['TRANSCRIBE','INTERPRET']
    assert sum(row.budget_usd for row in rows(session))==Decimal('0.08')
    with pytest.raises(HTTPException) as failure: service.transcribe(b'fixture')
    assert failure.value.status_code==409 and len(calls)==2


def test_correction_is_new_ai_call(session):
    calls=[]
    fake_service(session,calls,request_key=uuid4()).interpret(InterpretPayload(text='WOD'))
    fake_service(session,calls,request_key=uuid4()).interpret(InterpretPayload(text='WOD correction'))
    assert calls==['INTERPRET','INTERPRET'] and len(rows(session))==2


def test_provider_failure_keeps_uncertain_and_retry_does_not_call(session):
    calls=[]; key=uuid4()
    def failing(*_): calls.append(1); raise TimeoutError('PRIVATE WORKOUT TOKEN')
    service=TrainingService(session,DEMO_ATHLETE_ID,interpreter=failing,request_key=key)
    from app.services.training_errors import TrainingProcessingFailed
    with pytest.raises(TrainingProcessingFailed): service.interpret(InterpretPayload(text='WOD'))
    session.rollback()
    assert rows(session)[0].reservation_state=='UNCERTAIN'
    with pytest.raises(HTTPException): service.interpret(InterpretPayload(text='WOD'))
    assert calls==[1] and len(rows(session))==1


def test_local_transaction_rollback_does_not_erase_reservation(session):
    identifier=reserve(session,DEMO_ATHLETE_ID,'INTERPRET',request_key=uuid4()); session.rollback()
    assert session.get(PlanInteraction,identifier).reservation_state=='RESERVED'


def test_release_only_proven_before_call_and_replay_stays_blocked(session):
    key=uuid4(); identifier=reserve(session,DEMO_ATHLETE_ID,'INTERPRET',request_key=key)
    with pytest.raises(HTTPException): transition(identifier,'RELEASED')
    transition(identifier,'RELEASED',not_called=True)
    with pytest.raises(HTTPException): reserve(session,DEMO_ATHLETE_ID,'INTERPRET',request_key=key)
    session.rollback()
    second=reserve(session,DEMO_ATHLETE_ID,'INTERPRET'); transition(second,'STARTED')
    with pytest.raises(HTTPException): transition(second,'RELEASED',not_called=True)
    assert session.get(PlanInteraction,second).reservation_state=='RESERVED'


def test_inactive_account_has_no_reservation_or_provider(session):
    session.get(User,DEMO_ATHLETE_ID).is_active=False; session.commit(); calls=[]
    with pytest.raises(HTTPException): fake_service(session,calls).interpret(InterpretPayload(text='WOD'))
    assert calls==[] and rows(session)==[]


def test_parallel_web_chat_only_last_slot(session,monkeypatch):
    monkeypatch.setenv('USAGE_INTERPRET_DAILY','1'); barrier=Barrier(2)
    def attempt(channel):
        with SessionLocal() as worker:
            barrier.wait(timeout=10)
            try: reserve(worker,DEMO_ATHLETE_ID,'INTERPRET',channel=channel); worker.commit(); return 200
            except HTTPException as error: worker.rollback(); return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt,['web','whatsapp']))==[200,429]
    assert len(rows(session))==1


def test_global_budget_serialized_across_athletes(session,monkeypatch):
    other=second_athlete(session); monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0.05'); barrier=Barrier(2)
    def attempt(identifier):
        with SessionLocal() as worker:
            barrier.wait(timeout=10)
            try: reserve(worker,identifier,'INTERPRET'); worker.commit(); return 200
            except HTTPException as error: worker.rollback(); return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt,[DEMO_ATHLETE_ID,other]))==[200,429]
    assert sum(row.budget_usd for row in rows(session))==Decimal('0.05')


def test_global_budget_ai_and_whatsapp_send_shared(client,session,monkeypatch):
    configure(monkeypatch); link(session); monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0.06')
    reserve(session,DEMO_ATHLETE_ID,'INTERPRET'); session.commit()
    assert webhook(client,payload('ayuda')).status_code==200; provider=FakeProvider()
    assert process_one(provider,Vault()); assert dispatch_one(session,provider,Vault())
    assert provider.sent==[]
    assert session.scalar(select(WhatsAppOutbox)).error_code=='consumption_rejected'


def test_eighty_percent_alert_is_redacted(session,monkeypatch,caplog):
    monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0.0625')
    with caplog.at_level(logging.INFO): reserve(session,DEMO_ATHLETE_ID,'INTERPRET')
    assert 'consumption_budget_alert' in caplog.text
    assert 'gaston' not in caplog.text and str(DEMO_ATHLETE_ID) not in caplog.text


def test_pilot_budget_does_not_reset_at_month_boundary(session,monkeypatch):
    now=clock(); start=(now-timedelta(days=2)).date().isoformat()
    monkeypatch.setenv('USAGE_PILOT_START',start); monkeypatch.setenv('USAGE_GLOBAL_PILOT_USD','0.05')
    reserve(session,DEMO_ATHLETE_ID,'INTERPRET'); session.commit()
    monkeypatch.setattr('app.services.consumption_limits.clock', lambda: now+timedelta(days=10))
    with pytest.raises(HTTPException) as failure: reserve(session,DEMO_ATHLETE_ID,'TRANSCRIBE')
    assert failure.value.status_code==429 and len(rows(session))==1


def test_pilot_start_cannot_reset_budget(session,monkeypatch):
    reserve(session,DEMO_ATHLETE_ID,'INTERPRET'); session.commit()
    monkeypatch.setenv('USAGE_PILOT_START',(clock()-timedelta(days=1)).date().isoformat())
    with pytest.raises(HTTPException) as failure: reserve(session,DEMO_ATHLETE_ID,'TRANSCRIBE')
    assert failure.value.status_code==503


@pytest.mark.parametrize('bad',['NaN','Infinity','-1','0.000000001','999999999999','private-token'])
def test_invalid_configuration_fails_closed(session,monkeypatch,bad):
    monkeypatch.setenv('USAGE_INTERPRET_RESERVE_USD',bad)
    with pytest.raises(HTTPException) as failure: reserve(session,DEMO_ATHLETE_ID,'INTERPRET')
    assert failure.value.status_code==503 and rows(session)==[]


def test_production_requires_every_limit_and_video_cost(session,monkeypatch):
    monkeypatch.setenv('APP_ENV','production'); monkeypatch.delenv('USAGE_INTERPRET_DAILY')
    with pytest.raises(HTTPException): configuration(session)
    monkeypatch.setenv('USAGE_INTERPRET_DAILY','3'); monkeypatch.delenv('USAGE_VIDEO_STORAGE_RESERVE_USD')
    assert configuration(session,'INTERPRET')['INTERPRET_DAILY']==3
    with pytest.raises(HTTPException): reserve(session,DEMO_ATHLETE_ID,'ANALYZE')
    assert rows(session)==[]


def test_global_video_slot_and_extra_cost(session,monkeypatch):
    other=second_athlete(session); monkeypatch.setenv('USAGE_VIDEO_COMPUTE_RESERVE_USD','0.10')
    identifier=reserve(session,DEMO_ATHLETE_ID,'ANALYZE'); session.commit()
    assert session.get(PlanInteraction,identifier).budget_usd==Decimal('0.30')
    with pytest.raises(HTTPException): reserve(session,other,'ANALYZE')
    session.rollback(); transition(identifier,'STARTED'); transition(identifier,'CONFIRMED')
    assert reserve(session,other,'ANALYZE')


def test_admin_only_audited_complete_limits(client,session):
    values={name:str(value) for name,value in DEFAULTS.items()}
    values.update({name:'0' for name in VIDEO_COSTS}); values['PILOT_START']=clock().date().isoformat()
    client.post('/api/auth/login',json={'username':'gaston','password':'demo1234'})
    assert client.put('/api/admin/consumption-limits',json=values).status_code==403
    client.post('/api/auth/login',json={'username':'admin','password':'demo1234'})
    assert client.put('/api/admin/consumption-limits',json={}).status_code==422
    assert client.put('/api/admin/consumption-limits',json=values).status_code==200
    assert session.get(AdminSetting,'consumption_limits').value==values
    assert session.scalar(select(AdminAudit).where(AdminAudit.target=='consumption_limits')).action=='SETTINGS_UPDATED'
    reserve(session,DEMO_ATHLETE_ID,'INTERPRET'); session.commit()
    values['PILOT_START']=(clock()-timedelta(days=1)).date().isoformat()
    assert client.put('/api/admin/consumption-limits',json=values).status_code==409


def test_web_same_id_does_not_double_call(athlete_client,session,monkeypatch):
    calls=[]; monkeypatch.setattr('app.training.interpret', lambda *_: calls.append(1) or draft())
    headers={'Idempotency-Key':str(uuid4())}; data={'text':'Private workout'}
    assert athlete_client.post('/api/training-sessions/interpret',json=data,headers=headers).status_code==200
    assert athlete_client.post('/api/training-sessions/interpret',json=data,headers=headers).status_code==409
    assert calls==[1] and len(rows(session))==1


def test_webhook_duplicate_does_not_consume_and_chat_quota_is_shared(client,session,monkeypatch):
    configure(monkeypatch); link(session); calls=[]
    monkeypatch.setattr('app.services.training_service.interpret', lambda *_: calls.append(1) or draft())
    body=payload('Hoy hice 4 rondas',identifier='wamid.s06.duplicate'); provider=FakeProvider()
    assert webhook(client,body).json()['accepted']==1
    assert process_one(provider,Vault())
    assert webhook(client,body).json()['accepted']==0
    assert not process_one(provider,Vault()) and len(calls)==1 and len(rows(session))==1
    assert rows(session)[0].channel=='whatsapp'


def test_rate_rejection_is_silent_and_not_a_response_loop(client,session,monkeypatch):
    configure(monkeypatch); link(session); provider=FakeProvider()
    for _ in range(6):
        assert webhook(client,payload('ayuda')).status_code==200; assert process_one(provider,Vault())
    assert session.scalar(select(func.count()).select_from(WhatsAppOutbox))==5
    assert session.scalar(select(func.count()).select_from(WhatsAppInbox).where(WhatsAppInbox.error_code=='rate_limited'))==1
    assert not process_one(provider,Vault())
    assert rows(session)==[]


def test_inbound_daily_twenty(client,session,monkeypatch):
    configure(monkeypatch); link(session); monkeypatch.setenv('USAGE_WHATSAPP_RATE_PER_CONVERSATION','100')
    provider=FakeProvider()
    for _ in range(21):
        webhook(client,payload('ayuda')); assert process_one(provider,Vault())
    assert session.scalar(select(func.count()).select_from(WhatsAppOutbox))==20


def test_outbound_physical_sends_twenty_then_no_provider(client,session,monkeypatch):
    configure(monkeypatch); link(session); monkeypatch.setenv('USAGE_WHATSAPP_RATE_PER_CONVERSATION','100')
    monkeypatch.setenv('USAGE_WHATSAPP_INBOUND_DAILY','30'); provider=FakeProvider()
    for _ in range(21):
        webhook(client,payload('ayuda')); assert process_one(provider,Vault())
        assert dispatch_one(session,provider,Vault())
    assert len(provider.sent)==20
    assert session.scalar(select(func.count()).select_from(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))==20


def test_uncertain_send_keeps_cost_and_is_not_replayed(client,session,monkeypatch):
    from app.whatsapp.provider import ProviderError
    configure(monkeypatch); link(session); provider=FakeProvider()
    webhook(client,payload('ayuda')); process_one(provider,Vault())
    class Uncertain(FakeProvider):
        def send(self,*_): raise ProviderError('unknown',uncertain=True)
    assert dispatch_one(session,Uncertain(),Vault())
    assert not dispatch_one(session,provider,Vault()) and provider.sent==[]
    reservation=session.scalar(select(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))
    assert reservation.reservation_state=='UNCERTAIN' and reservation.cost==Decimal('0.02')


def test_migration_preserves_legacy_interaction_and_roundtrip(session):
    session.close(); config=Config('alembic.ini')
    command.downgrade(config,'0022_administration')
    with engine.begin() as connection:
        identifier=uuid4()
        connection.execute(text("INSERT INTO plan_interactions(id,user_id,operation) VALUES (:id,:user,'INTERPRET')"),{'id':identifier,'user':DEMO_ATHLETE_ID})
    command.upgrade(config,'head')
    row=session.get(PlanInteraction,identifier)
    assert row.request_key is None and row.budget_usd is None and row.reservation_state=='UNCERTAIN'
    session.close(); command.check(config)


def test_audio_webhook_consumes_transcription_and_interpretation_once(client,session,monkeypatch):
    from app.whatsapp.provider import DownloadedMedia
    configure(monkeypatch); link(session); calls=[]; provider=FakeProvider()
    provider.media=DownloadedMedia(b'fixture audio','audio/ogg')
    monkeypatch.setattr('app.services.training_service.transcribe', lambda *_: calls.append('TRANSCRIBE') or 'Hoy hice 4 rondas')
    monkeypatch.setattr('app.services.training_service.interpret', lambda *_: calls.append('INTERPRET') or draft())
    body=payload('',kind='audio',identifier='wamid.s06.audio')
    assert webhook(client,body).json()['accepted']==1; assert process_one(provider,Vault())
    assert webhook(client,body).json()['accepted']==0; assert not process_one(provider,Vault())
    assert calls==['TRANSCRIBE','INTERPRET']
    assert sorted(r.operation for r in rows(session))==['INTERPRET','TRANSCRIBE']


def test_telemetry_does_not_include_private_inputs_or_exceptions(session,caplog):
    def failing(*_): raise RuntimeError('SECRET-TOKEN PRIVATE-WORKOUT')
    from app.services.training_errors import TrainingUnavailable
    with caplog.at_level(logging.INFO):
        with pytest.raises(TrainingUnavailable):
            TrainingService(session,DEMO_ATHLETE_ID,interpreter=failing).interpret(InterpretPayload(text='PRIVATE-WORKOUT'))
    assert 'PRIVATE-WORKOUT' not in caplog.text and 'SECRET-TOKEN' not in caplog.text
    assert 'consumption_reserved' in caplog.text and rows(session)[0].reservation_state=='UNCERTAIN'


def test_analyze_post_replay_prevents_new_job(athlete_client,session,monkeypatch):
    from app import main
    monkeypatch.setattr(main,'_process_analysis',lambda *_:None)
    headers={'Idempotency-Key':str(uuid4())}
    monkeypatch.setattr(main,'_validate_upload',lambda *_:None)
    response=athlete_client.post('/api/analyses',headers=headers,data={'exercise':'Clean','objective':'Técnica'},files={'file':('clip.mp4',b'fixture','video/mp4')})
    assert response.status_code==202,response.text
    replay=athlete_client.post('/api/analyses',headers=headers,data={'exercise':'Clean','objective':'Técnica'},files={'file':('clip.mp4',b'fixture','video/mp4')})
    assert replay.status_code==409 and len(rows(session))==1


def test_parallel_video_reservation_global_one(session):
    other=second_athlete(session); barrier=Barrier(2)
    def attempt(identifier):
        with SessionLocal() as worker:
            barrier.wait(timeout=10)
            try: reserve(worker,identifier,'ANALYZE'); worker.commit(); return 200
            except HTTPException as error: worker.rollback(); return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt,[DEMO_ATHLETE_ID,other]))==[200,429]
    assert len(rows(session))==1


def test_account_lock_held_during_web_provider(session):
    from sqlalchemy.exc import OperationalError
    def interpreter(*_):
        with SessionLocal() as other:
            with pytest.raises(OperationalError):
                other.scalar(select(User).where(User.id==DEMO_ATHLETE_ID).with_for_update(nowait=True))
        return draft()
    TrainingService(session,DEMO_ATHLETE_ID,interpreter=interpreter).interpret(InterpretPayload(text='WOD'))
    assert rows(session)[0].reservation_state=='CONFIRMED'


def test_disabled_native_provider_releases_only_unstarted_reservation(session,monkeypatch):
    from app.services.training_errors import TrainingUnavailable
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    with pytest.raises(TrainingUnavailable): TrainingService(session,DEMO_ATHLETE_ID).interpret(InterpretPayload(text='WOD'))
    records=rows(session)
    assert len(records)==1 and records[0].reservation_state=='RELEASED' and records[0].started_at is None


def test_unknown_legacy_processing_video_blocks_new_job(session):
    from app.models import Analysis
    session.add(Analysis(id='legacy-inflight',athlete_id=DEMO_ATHLETE_ID,status='PROCESSING',original_filename='fixture.mp4',video_path='uploads/fixture.mp4'))
    session.commit()
    with pytest.raises(HTTPException): reserve(session,DEMO_ATHLETE_ID,'ANALYZE')
    assert rows(session)==[]


def test_empty_video_cost_blocks_only_video_in_production(session,monkeypatch):
    monkeypatch.setenv('APP_ENV','production');monkeypatch.setenv('USAGE_VIDEO_OTHER_RESERVE_USD','')
    assert configuration(session,'INTERPRET')['INTERPRET_DAILY']==3
    with pytest.raises(HTTPException): reserve(session,DEMO_ATHLETE_ID,'ANALYZE')


def test_unknown_legacy_cost_contributes_to_budget(session,monkeypatch):
    monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0.05')
    session.add(PlanInteraction(user_id=DEMO_ATHLETE_ID,operation='INTERPRET'));session.commit()
    with pytest.raises(HTTPException): reserve(session,DEMO_ATHLETE_ID,'TRANSCRIBE')
    assert len(rows(session))==1


@pytest.mark.parametrize('status,expected', [(402,'FAILED'),(429,'RETRY')])
def test_kapso_http_error_keeps_reservation_and_402_never_retries(client,session,monkeypatch,status,expected):
    from urllib.error import HTTPError
    from app.whatsapp.kapso import KapsoWhatsAppProvider
    configure(monkeypatch);link(session)
    webhook(client,payload('ayuda'));process_one(FakeProvider(),Vault())
    calls=[]
    def opener(request,timeout):
        calls.append(1);raise HTTPError(request.full_url,status,'PRIVATE RESPONSE',{},None)
    provider=KapsoWhatsAppProvider(opener=opener)
    assert dispatch_one(session,provider,Vault())
    row=session.scalar(select(WhatsAppOutbox));assert row.state==expected
    reservation=session.scalar(select(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))
    assert reservation.reservation_state=='UNCERTAIN' and reservation.cost==Decimal('0.02')
    if status==402:
        assert not dispatch_one(session,provider,Vault()) and calls==[1]
    else:
        row.next_attempt_at=clock();session.commit();assert dispatch_one(session,provider,Vault())
        assert calls==[1,1]
        assert session.scalar(select(func.count()).select_from(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation'))==2


def test_audio_at_quota_never_downloads_or_calls_ai(client,session,monkeypatch):
    configure(monkeypatch);link(session)
    for _ in range(3):
        identifier=reserve(session,DEMO_ATHLETE_ID,'TRANSCRIBE');transition(identifier,'CONFIRMED');session.commit()
    class NoDownload(FakeProvider):
        def download_media(self,*_): raise AssertionError('Provider called after quota')
    webhook(client,payload('',kind='audio'));assert process_one(NoDownload(),Vault())
    assert len(rows(session))==3
    assert session.scalar(select(WhatsAppInbox)).error_code=='consumption_rejected'


def test_legacy_outbound_cost_counted_without_double_counting_new_send(session,monkeypatch):
    monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0.06')
    session.add(WhatsAppUsage(event_key='outbound:'+str(uuid4()),category='outbound',athlete_id=DEMO_ATHLETE_ID,cost=None,units=1))
    session.commit()
    with pytest.raises(HTTPException): reserve(session,DEMO_ATHLETE_ID,'INTERPRET')
    assert rows(session)==[]


def test_pending_reservations_carry_into_next_day_budget(session,monkeypatch):
    now=clock();monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0.05')
    identifier=reserve(session,DEMO_ATHLETE_ID,'INTERPRET');session.commit()
    monkeypatch.setattr('app.services.consumption_limits.clock',lambda:now+timedelta(days=1))
    with pytest.raises(HTTPException):reserve(session,DEMO_ATHLETE_ID,'TRANSCRIBE')
    session.rollback()
    transition(identifier,'STARTED') # Already allocated last slot can be used once.
    assert session.get(PlanInteraction,identifier).reservation_state=='RESERVED'


def test_lowering_budget_blocks_reserved_provider_before_start(session,monkeypatch):
    identifier=reserve(session,DEMO_ATHLETE_ID,'INTERPRET');session.commit()
    monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0')
    with pytest.raises(HTTPException):transition(identifier,'STARTED')
    assert session.get(PlanInteraction,identifier).started_at is None
