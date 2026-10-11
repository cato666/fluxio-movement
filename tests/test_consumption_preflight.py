"""S09: no real provider, PostgreSQL disposable and real bounded FFmpeg preflight."""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from fastapi import HTTPException
from sqlalchemy import select
from app.database import SessionLocal
from app.models import PlanInteraction
from app.seed import DEMO_ATHLETE_ID
from app.services.consumption_limits import reserve, transition, abandon_media
from app.services.training_contracts import InterpretPayload
from app.services.training_errors import TrainingInvalid, TrainingUnavailable, TrainingProcessingFailed
from app.services.training_service import TrainingService
from app.services import training_transcription as voice
from tests.test_training_transcription import wav
from tests.test_whatsapp_capture import channel, step, state, draft
from tests.whatsapp_helpers import DownloadedMedia
from app.whatsapp.capture import snapshot
from app.whatsapp.security import Vault


def records(session):
    session.expire_all();return list(session.scalars(select(PlanInteraction)))

@pytest.mark.parametrize('raw',[b'not audio',wav(181),b'RIFFbrokenWAVE'],ids=['invalid-header','too-long','broken-wave'])
def test_invalid_native_audio_precedes_reservation_and_external_call(session,monkeypatch,raw):
    monkeypatch.setenv('OPENAI_API_KEY','fixture-s09')
    def never(*args,**kwargs): raise AssertionError('provider must not run')
    monkeypatch.setattr(voice,'urlopen',never)
    with pytest.raises(TrainingInvalid): TrainingService(session,DEMO_ATHLETE_ID).transcribe(raw)
    assert records(session)==[]

@pytest.mark.parametrize('operation',['INTERPRET','TRANSCRIBE'])
def test_disabled_native_provider_never_reserves(session,monkeypatch,operation):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    service=TrainingService(session,DEMO_ATHLETE_ID)
    with pytest.raises(TrainingUnavailable):
        service.interpret(InterpretPayload(text='WOD')) if operation=='INTERPRET' else service.transcribe(wav())
    assert records(session)==[]


def test_missing_ffmpeg_before_call_does_not_consume(session,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','fixture-s09')
    def unavailable(*args,**kwargs): raise FileNotFoundError('private local path')
    monkeypatch.setattr(voice.subprocess,'run',unavailable)
    with pytest.raises(TrainingUnavailable): TrainingService(session,DEMO_ATHLETE_ID).transcribe(wav())
    assert records(session)==[]


def test_reserved_preflight_without_any_provider_is_released_idempotently(session):
    event=uuid4();identifier=reserve(session,DEMO_ATHLETE_ID,'TRANSCRIBE',request_key=event,channel='whatsapp')
    session.info['media_reservations']={(event,'TRANSCRIBE'):identifier}
    abandon_media(session,event);abandon_media(session,event);transition(identifier,'RELEASED',not_called=True)
    assert records(session)[0].reservation_state=='RELEASED'
    with pytest.raises(HTTPException): reserve(session,DEMO_ATHLETE_ID,'TRANSCRIBE',request_key=event,channel='whatsapp')


def test_download_evidence_keeps_unknown_costs(session):
    event=uuid4();identifier=reserve(session,DEMO_ATHLETE_ID,'TRANSCRIBE',request_key=event,channel='whatsapp')
    session.info['media_reservations']={(event,'TRANSCRIBE'):identifier}
    session.info['media_provider_started']={identifier}
    abandon_media(session,event)
    assert records(session)[0].reservation_state=='UNCERTAIN'
    with pytest.raises(HTTPException): transition(identifier,'RELEASED',not_called=True)


def test_release_concurrent_idempotent_then_last_slot_can_be_used(session,monkeypatch):
    monkeypatch.setenv('USAGE_INTERPRET_DAILY','1');key=uuid4()
    identifier=reserve(session,DEMO_ATHLETE_ID,'INTERPRET',request_key=key);session.commit()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda _:transition(identifier,'RELEASED',not_called=True),range(2)))==[None,None]
    second=reserve(session,DEMO_ATHLETE_ID,'INTERPRET');session.commit();transition(second,'STARTED')
    with pytest.raises(HTTPException): transition(second,'RELEASED',not_called=True)
    assert records(session)[0].reservation_state in ('RELEASED','RESERVED')
    assert sorted(row.reservation_state for row in records(session))==['RELEASED','RESERVED']


def test_audio_result_failure_after_external_call_is_uncertain(session,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','fixture-s09');calls=[]
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self): return b'{"text":""}'
    monkeypatch.setattr(voice,'urlopen',lambda *args,**kwargs:calls.append(1) or Response())
    with pytest.raises(TrainingInvalid): TrainingService(session,DEMO_ATHLETE_ID).transcribe(wav())
    row=records(session)[0]
    assert calls==[1] and row.started_at is not None and row.reservation_state=='UNCERTAIN'
    with pytest.raises(HTTPException): transition(row.id,'RELEASED',not_called=True)


def test_partial_audio_uses_encrypted_existing_context_without_retranscribing(client,session,channel,monkeypatch):
    transcriptions=[];interpretations=[];downloads=[]
    monkeypatch.setattr('app.services.training_service.transcribe',lambda raw:transcriptions.append(1) or 'Hice cuatro rondas')
    def interpret(*args):
        interpretations.append(1)
        if len(interpretations)==1: raise ConnectionError('private provider content')
        return draft()
    monkeypatch.setattr('app.services.training_service.interpret',interpret)
    channel[0].media=DownloadedMedia(wav(),'audio/wav')
    original=channel[0].download_media
    channel[0].download_media=lambda *args:downloads.append(1) or original(*args)
    step(client,channel,'',kind='audio')
    assert state(session).state=='CLARIFY'
    protected=state(session).payload_minimized
    assert 'Hice cuatro rondas' not in protected
    assert snapshot(state(session),Vault())['audio_source']['transcript']=='Hice cuatro rondas'
    step(client,channel,'',kind='audio')
    assert state(session).state=='CONFIRM'
    assert transcriptions==[1] and downloads==[1] and interpretations==[1,1]
    assert sorted((row.operation,row.reservation_state) for row in records(session))==[
        ('INTERPRET','CONFIRMED'),('INTERPRET','UNCERTAIN'),('TRANSCRIBE','CONFIRMED')]


def test_exhausted_budget_prevents_native_transcription(session,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','fixture-s09');monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0')
    monkeypatch.setattr(voice,'urlopen',lambda *args,**kwargs:pytest.fail('provider at exhausted budget'))
    with pytest.raises(HTTPException) as error: TrainingService(session,DEMO_ATHLETE_ID).transcribe(wav())
    assert error.value.status_code==429 and records(session)==[]

@pytest.mark.parametrize('path,data,name',[
    ('/api/analyze',{},'invalid.txt'),
    ('/api/analyses',{'exercise':'air_squat','objective':'review','view':'diagonal'},'clip.mp4'),
    ('/api/analyses',{'exercise':'air_squat','objective':'','view':'side'},'clip.mp4')])
def test_invalid_video_metadata_precedes_reservation(athlete_client,session,path,data,name):
    response=athlete_client.post(path,data=data,files={'file':(name,b'invalid','video/mp4')})
    assert response.status_code==400 and records(session)==[]


@pytest.mark.parametrize('operation',['INTERPRET','TRANSCRIBE'])
def test_local_accounting_failure_between_reserve_and_provider_releases(session,monkeypatch,operation):
    monkeypatch.setenv('OPENAI_API_KEY','fixture-s09')
    def failure(*args,**kwargs): raise RuntimeError('PRIVATE ACCOUNTING DETAIL')
    monkeypatch.setattr('app.services.training_usage.report_usage',failure)
    monkeypatch.setattr(voice,'urlopen',lambda *args,**kwargs:pytest.fail('provider must not run'))
    monkeypatch.setattr('app.services.workout_interpretation._request',lambda *args,**kwargs:pytest.fail('provider must not run'))
    service=TrainingService(session,DEMO_ATHLETE_ID)
    with pytest.raises((TrainingUnavailable,TrainingProcessingFailed)) as error:
        service.interpret(InterpretPayload(text='WOD')) if operation=='INTERPRET' else service.transcribe(wav())
    assert 'PRIVATE' not in str(error.value)
    row=records(session)[0]
    assert row.reservation_state=='RELEASED' and row.started_at is None


@pytest.mark.parametrize('failure',['disabled','invalid-url','invalid-actions'])
def test_local_kapso_preflight_never_reserves_or_calls_transport(client,session,monkeypatch,failure):
    from tests.test_whatsapp_delivery_operations import queued
    from app.whatsapp.kapso import KapsoWhatsAppProvider
    from app.whatsapp.queue import dispatch_one
    from app.whatsapp.models import WhatsAppUsage
    from tests.whatsapp_helpers import configure
    configure(monkeypatch);row,_=queued(client,session)
    provider=KapsoWhatsAppProvider(opener=lambda *args,**kwargs:pytest.fail('transport must not run'))
    if failure=='disabled': provider.key=''
    elif failure=='invalid-url': provider.base='http://rejected.invalid'
    else:
        protected=Vault().decrypt(row.payload_encrypted,row.key_version)
        protected['actions']=[{'id':'fixture','title':'fixture'}]*4
        row.payload_encrypted=Vault().encrypt(protected);session.commit()
    assert dispatch_one(session,provider,Vault())
    assert row.state=='FAILED'
    assert session.scalar(select(WhatsAppUsage).where(WhatsAppUsage.category=='send_reservation')) is None
