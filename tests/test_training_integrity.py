from uuid import UUID, uuid4
from sqlalchemy import select, func
from app.models import TrainingSession
from app.services.training_service import TrainingService
from app.seed import DEMO_ATHLETE_ID
from tests.test_training_sessions import payload


def test_s10_omitted_fields_survive_edit(athlete_client):
    created=athlete_client.post('/api/training-sessions',json=payload(adaptations='Escalado registrado')).json()
    edited=athlete_client.put('/api/training-sessions/'+created['id'],json={'trained_on':'2026-10-02','title':'Titulo corregido','workout':created['workout']})
    assert edited.status_code==200
    data=edited.json()
    lost=[key for key in ('result_text','adaptations','rpe','source_text') if data[key]!=created[key]]
    assert not lost, 'S10: omitted fields overwritten: '+', '.join(lost)


def test_s10_note_survives_unrelated_edit(athlete_client,session):
    created=athlete_client.post('/api/training-sessions',json=payload()).json()
    TrainingService(session,DEMO_ATHLETE_ID).add_athlete_note(UUID(created['id']),'Nota de prueba sintetica')
    edited=athlete_client.put('/api/training-sessions/'+created['id'],json={'trained_on':'2026-10-02','title':'Titulo corregido','workout':created['workout']})
    assert edited.status_code==200
    session.expire_all()
    assert session.get(TrainingSession,UUID(created['id'])).athlete_notes[-1]['text']=='Nota de prueba sintetica'
    assert 'Nota de prueba sintetica' in (edited.json()['adaptations'] or ''), 'S10: existing athlete note disappeared from visible record'


def test_s10_same_save_request_does_not_duplicate(athlete_client,session):
    headers={'Idempotency-Key':str(uuid4())}
    first=athlete_client.post('/api/training-sessions',json=payload(),headers=headers)
    second=athlete_client.post('/api/training-sessions',json=payload(),headers=headers)
    assert first.status_code==second.status_code==201
    count=session.scalar(select(func.count()).select_from(TrainingSession))
    assert first.json()['id']==second.json()['id'] and count==1, f'S10: same save request persisted {count} sessions'


import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from app.database import SessionLocal, engine
from app.models import TrainingSaveRequest, User, Athlete, TrainingImage, Analysis
from app.services.training_errors import TrainingNotFound, TrainingConflict


def test_key_replay_survives_new_application_process(session):
    key=uuid4();created=TrainingService(session,DEMO_ATHLETE_ID,request_key=key).create(payload())
    script="from app.database import SessionLocal; from app.services.training_service import TrainingService; from uuid import UUID; import json; s=SessionLocal(); print(json.dumps(str(TrainingService(s,UUID(%r),request_key=UUID(%r)).create(%r)['id']))); s.close()" % (str(DEMO_ATHLETE_ID),str(key),payload())
    result=subprocess.run([sys.executable,'-c',script],capture_output=True,text=True,check=True,timeout=20)
    assert json.loads(result.stdout)==str(created['id'])
    assert session.scalar(select(func.count()).select_from(TrainingSession))==1


def test_two_concurrent_keyed_saves_create_once(session):
    key=uuid4();barrier=Barrier(2)
    def save(_):
        with SessionLocal() as connection:
            barrier.wait(timeout=5)
            return TrainingService(connection,DEMO_ATHLETE_ID,request_key=key).create(payload())['id']
    with ThreadPoolExecutor(max_workers=2) as pool: ids=list(pool.map(save,range(2)))
    assert ids[0]==ids[1]
    assert session.scalar(select(func.count()).select_from(TrainingSession))==1
    assert session.scalar(select(func.count()).select_from(TrainingSaveRequest))==1


def test_conflicting_payload_and_delete_never_recreate(athlete_client,session):
    headers={'Idempotency-Key':str(uuid4())}
    first=athlete_client.post('/api/training-sessions',json=payload(),headers=headers).json()
    assert athlete_client.post('/api/training-sessions',json=payload(title='Otro'),headers=headers).status_code==409
    assert athlete_client.delete('/api/training-sessions/'+first['id']).status_code==200
    assert athlete_client.post('/api/training-sessions',json=payload(),headers=headers).status_code==404
    assert session.scalar(select(func.count()).select_from(TrainingSession))==0
    assert session.scalar(select(func.count()).select_from(TrainingSaveRequest))==1


def test_key_scope_and_legacy_unkeyed_saves(session):
    other=User(id=uuid4(),name='Fixture athlete',role='ATHLETE',is_active=True)
    session.add(other);session.flush();session.add(Athlete(user_id=other.id));session.commit()
    key=uuid4()
    a=TrainingService(session,DEMO_ATHLETE_ID,request_key=key).create(payload())
    b=TrainingService(session,other.id,request_key=key).create(payload())
    assert a['id']!=b['id']
    for _ in range(2): TrainingService(session,DEMO_ATHLETE_ID).create(payload())
    assert session.scalar(select(func.count()).select_from(TrainingSession))==4


def test_keyed_failed_save_rolls_back_evidence_and_manual_retry(athlete_client,session):
    key=uuid4();headers={'Idempotency-Key':str(key)}
    assert athlete_client.post('/api/training-sessions',json=payload(source_image_id=str(uuid4())),headers=headers).status_code==404
    assert session.get(TrainingSaveRequest,(DEMO_ATHLETE_ID,key)) is None
    assert athlete_client.post('/api/training-sessions',json=payload(),headers=headers).status_code==201


def test_commit_failure_rolls_back_session_and_evidence(session,monkeypatch):
    key=uuid4()
    def fail(): raise RuntimeError('fixture persistence failure')
    with monkeypatch.context() as patch:
        patch.setattr(session,'commit',fail)
        with pytest.raises(RuntimeError): TrainingService(session,DEMO_ATHLETE_ID,request_key=key).create(payload())
    session.rollback()
    assert session.scalar(select(func.count()).select_from(TrainingSession))==0
    assert session.scalar(select(func.count()).select_from(TrainingSaveRequest))==0
    TrainingService(session,DEMO_ATHLETE_ID,request_key=key).create(payload())
    assert session.scalar(select(func.count()).select_from(TrainingSession))==1


def test_optional_photo_links_blocks_preserved_and_explicit_clear(athlete_client,session):
    image=TrainingImage(athlete_id=DEMO_ATHLETE_ID,path='training-images/fixture.jpg')
    analysis=Analysis(id='s10-owned',athlete_id=DEMO_ATHLETE_ID,original_filename='fixture.mp4',video_path='uploads/fixture.mp4')
    session.add_all([image,analysis]);session.commit()
    original=payload(source_image_id=str(image.id),video_links=[{'analysis_id':analysis.id,'movement':'Squat'}],blocks=[{'title':'Metcon','format':'amrap','prescription':'12 minutos','movements':[]}])
    created=athlete_client.post('/api/training-sessions',json=original).json();url='/api/training-sessions/'+created['id']
    minimal={k:created[k] for k in ('trained_on','title','workout')}
    edited=athlete_client.put(url,json=minimal)
    assert edited.status_code==200,edited.text
    for key in ('source_image_id','video_links','blocks'): assert edited.json()[key]==created[key]
    cleared=athlete_client.put(url,json={**minimal,'source_image_id':None,'video_links':[],'blocks':[],'result_text':None,'rpe':None})
    assert cleared.status_code==200
    assert cleared.json()['source_image_id'] is None and cleared.json()['video_links']==[] and cleared.json()['blocks']==[]
    assert cleared.json()['result_text'] is None and cleared.json()['rpe'] is None
    assert session.get(TrainingImage,image.id) is not None and session.get(Analysis,analysis.id) is not None


def test_failed_edit_does_not_overwrite_any_field(athlete_client,session):
    created=athlete_client.post('/api/training-sessions',json=payload(adaptations='Fixture note')).json()
    response=athlete_client.put('/api/training-sessions/'+created['id'],json=payload(title='Changed',source_image_id=str(uuid4())))
    assert response.status_code==404
    assert athlete_client.get('/api/training-sessions/'+created['id']).json()==created


def test_stale_session_and_concurrent_notes_preserve_latest(session):
    service=TrainingService(session,DEMO_ATHLETE_ID);row=service.create(payload(adaptations='Original'))
    service.detail(row['id'])
    with SessionLocal() as connection: TrainingService(connection,DEMO_ATHLETE_ID).add_athlete_note(row['id'],'First','whatsapp')
    service.update(row['id'],{k:payload()[k] for k in ('trained_on','title','workout')})
    assert 'First' in service.detail(row['id'])['adaptations']
    session.commit();barrier=Barrier(2)
    def note(index):
        with SessionLocal() as connection:
            worker=TrainingService(connection,DEMO_ATHLETE_ID);worker.detail(row['id']);barrier.wait(timeout=5)
            worker.add_athlete_note(row['id'],f'Note {index}','web' if index==0 else 'whatsapp')
    with ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(note,range(2)))
    session.expire_all();result=service.detail(row['id'])
    assert all(text in result['adaptations'] for text in ('Original','First','Note 0','Note 1'))
    assert len(session.get(TrainingSession,row['id']).athlete_notes)==3


def test_deactivation_blocks_replay_and_does_not_create(session):
    key=uuid4();TrainingService(session,DEMO_ATHLETE_ID,request_key=key).create(payload())
    session.get(User,DEMO_ATHLETE_ID).is_active=False;session.commit()
    with pytest.raises(TrainingNotFound): TrainingService(session,DEMO_ATHLETE_ID,request_key=key).create(payload())
    assert session.scalar(select(func.count()).select_from(TrainingSession))==1


def test_idempotency_evidence_does_not_store_private_payload(session):
    key=uuid4();TrainingService(session,DEMO_ATHLETE_ID,request_key=key).create(payload(workout='PRIVATE FIXTURE'))
    row=session.get(TrainingSaveRequest,(DEMO_ATHLETE_ID,key))
    assert len(row.payload_hash)==64
    assert set(row.__table__.columns.keys())=={'athlete_id','request_key','session_id','payload_hash','created_at'}
    assert 'PRIVATE' not in row.payload_hash



def test_manual_keyed_save_works_without_budget_or_providers(athlete_client,session,monkeypatch):
    from app.models import PlanInteraction
    monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD','0');monkeypatch.setenv('OPENAI_API_KEY','');monkeypatch.setenv('KAPSO_API_KEY','')
    headers={'Idempotency-Key':str(uuid4())}
    response=athlete_client.post('/api/training-sessions',json=payload(),headers=headers)
    assert response.status_code==201
    assert session.scalar(select(func.count()).select_from(PlanInteraction))==0


def test_additive_migration_keeps_legacy_sessions_and_model_contract(session):
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect
    assert engine.url.database=='movement_test'
    row=TrainingService(session,DEMO_ATHLETE_ID).create(payload());identifier=row['id'];session.commit()
    config=Config('alembic.ini');command.downgrade(config,'0023_consumption_reservations')
    assert 'training_save_requests' not in inspect(engine).get_table_names()
    command.upgrade(config,'head');command.check(config)
    session.expire_all()
    assert TrainingService(session,DEMO_ATHLETE_ID).detail(identifier)['workout']==row['workout']
    assert session.scalar(select(func.count()).select_from(TrainingSaveRequest))==0


def test_delete_keeps_whatsapp_media_and_image_references(athlete_client,session,tmp_path,monkeypatch):
    from datetime import datetime,timezone
    from app.whatsapp.models import WhatsAppInbox,WhatsAppMedia
    from tests.test_training_interpretation import photo
    monkeypatch.setenv('STORAGE_PATH',str(tmp_path))
    service=TrainingService(session,DEMO_ATHLETE_ID)
    image=service.store_image(photo())
    row=service.create(payload(source_image_id=image.id))
    instant=datetime.now(timezone.utc)
    inbox=WhatsAppInbox(id=uuid4(),provider='fixture',provider_message_id='s10-fixture',message_type='image',payload_encrypted='fixture',key_version='fixture',state='PROCESSED',happened_at=instant,expires_at=instant)
    session.add(inbox);session.flush()
    media=WhatsAppMedia(athlete_id=DEMO_ATHLETE_ID,training_session_id=row['id'],inbox_id=inbox.id,path='fixture',media_type='image',expires_at=None)
    session.add(media);session.commit()
    path=service.image_path(image.id)
    assert athlete_client.delete('/api/training-sessions/'+str(row['id'])).status_code==200
    session.expire_all();assert session.get(WhatsAppMedia,media.id).training_session_id is None
    assert session.get(TrainingImage,image.id) is not None and path.is_file()
    # Retention/cleanup belongs to S11: no file deletion here.



def test_web_and_whatsapp_notes_have_same_visible_canonical_week(athlete_client,session):
    row=athlete_client.post('/api/training-sessions',json=payload()).json()
    service=TrainingService(session,DEMO_ATHLETE_ID)
    service.add_athlete_note(UUID(row['id']),'Note from web','web')
    service.add_athlete_note(UUID(row['id']),'Note from chat','whatsapp')
    url='/api/training-sessions/'+row['id']
    minimal={k:row[k] for k in ('trained_on','title','workout')}
    assert athlete_client.put(url,json=minimal).status_code==200
    detail=athlete_client.get(url).json()
    weekly=athlete_client.get('/api/training-week?day=2026-10-02').json()['items'][0]
    assert detail['adaptations']==weekly['adaptations']
    assert 'Note from web' in detail['adaptations'] and 'Note from chat' in detail['adaptations']
    assert athlete_client.put(url,json={**minimal,'adaptations':'Edited athlete note'}).status_code==200
    weekly=athlete_client.get('/api/training-week?day=2026-10-02').json()['items'][0]
    assert weekly['adaptations']=='Edited athlete note'
    assert 'Note from chat' not in weekly['adaptations']
