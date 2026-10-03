import json
from sqlalchemy import select
from app.models import TrainingAIUsage
from app.services import workout_interpretation as ai, training_transcription as voice
from tests.test_training_interpretation import draft
from tests.test_training_transcription import wav


def test_each_interpretation_records_real_usage_without_saving_session(athlete_client, session, monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    monkeypatch.setattr(ai,'_request',lambda *_:{'model':'reported-model','usage':{'input_tokens':120,'output_tokens':80,'output_tokens_details':{'reasoning_tokens':30}},'output_text':json.dumps(draft())})
    for _ in range(2):
        assert athlete_client.post('/api/training-sessions/interpret',json={'text':'AMRAP 12'}).status_code==200
    rows=session.scalars(select(TrainingAIUsage)).all()
    assert len(rows)==2
    assert all(row.model=='reported-model' and row.status=='COMPLETED' and row.input_tokens==120 and row.output_tokens==80 and row.reasoning_tokens==30 for row in rows)
    assert athlete_client.get('/api/training-sessions').json()['items']==[]
    athlete_client.post('/api/auth/logout')
    assert athlete_client.post('/api/auth/login',json={'username':'admin','password':'demo1234'}).status_code==200
    data=athlete_client.get('/api/internal/ai-usage').json()
    assert data['totals']['total_tokens']==400
    assert data['totals']['reasoning_tokens']==60
    assert data['totals']['training_runs']==2
    assert data['training_by_athlete'][0]['total_tokens']==400
    assert data['training_by_athlete'][0]['input_tokens']==240
    assert data['training_by_athlete'][0]['output_tokens']==160
    assert data['recent_runs'][0]['operation']=='INTERPRET'
    assert data['recent_runs'][0]['athlete_name']


def test_failed_draft_still_counts_reported_consumption(athlete_client,session,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    monkeypatch.setattr(ai,'_request',lambda *_:{'usage':{'input_tokens':100,'output_tokens':20},'output_text':'PRIVATE invalid content'})
    assert athlete_client.post('/api/training-sessions/interpret',json={'text':'PRIVATE user source'}).status_code==502
    row=session.scalar(select(TrainingAIUsage))
    assert row.status=='FAILED' and row.input_tokens==100 and row.output_tokens==20
    assert 'PRIVATE' not in row.error
    athlete_client.post('/api/auth/logout');athlete_client.post('/api/auth/login',json={'username':'admin','password':'demo1234'})
    assert athlete_client.get('/api/internal/ai-usage').json()['totals']['total_tokens']==120


def test_transport_failure_is_unknown_not_zero_and_invalid_requests_not_recorded(athlete_client,session,monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    assert athlete_client.post('/api/training-sessions/interpret',json={'text':'AMRAP'}).status_code==503
    assert session.scalar(select(TrainingAIUsage)) is None
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    def fail(*_):raise ConnectionError('Private key or provider text')
    monkeypatch.setattr(ai,'_request',fail)
    assert athlete_client.post('/api/training-sessions/interpret',json={'text':'AMRAP'}).status_code==502
    row=session.scalar(select(TrainingAIUsage))
    assert row.status=='FAILED' and row.input_tokens is None and row.error=='ConnectionError'
    assert athlete_client.get('/api/internal/ai-usage').status_code==403
    athlete_client.post('/api/auth/logout');athlete_client.post('/api/auth/login',json={'username':'admin','password':'demo1234'})
    data=athlete_client.get('/api/internal/ai-usage').json()
    assert data['recent_runs'][0]['total_tokens'] is None
    assert data['totals']['unreported_training_runs']==1


def test_audio_records_tokens_and_duration_then_duration_only(athlete_client,session,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    provider={'text':'AMRAP 12','usage':{'type':'tokens','input_tokens':45,'output_tokens':12}}
    class Response:
        def __enter__(self):return self
        def __exit__(self,*_):pass
        def read(self):return json.dumps(provider).encode()
    monkeypatch.setattr(voice,'urlopen',lambda *_,**__:Response())
    assert athlete_client.post('/api/training-sessions/transcribe',files={'file':('audio.wav',wav())}).status_code==200
    provider['usage']={'type':'duration','seconds':1}
    assert athlete_client.post('/api/training-sessions/transcribe',files={'file':('audio.wav',wav())}).status_code==200
    rows=session.scalars(select(TrainingAIUsage).order_by(TrainingAIUsage.created_at)).all()
    assert len(rows)==2 and all(row.duration_seconds==1 and row.operation=='TRANSCRIBE' for row in rows)
    assert rows[0].input_tokens==45 and rows[0].output_tokens==12
    assert rows[1].input_tokens is None and rows[1].output_tokens is None
    assert athlete_client.post('/api/training-sessions/transcribe',files={'file':('audio.wav',b'invalid')}).status_code==422
    assert len(session.scalars(select(TrainingAIUsage)).all())==2
