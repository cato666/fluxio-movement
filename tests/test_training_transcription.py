import io
import json
import wave
import subprocess
import pytest
from app import training
from app.services import training_transcription as voice


def wav(seconds=1):
    output=io.BytesIO()
    with wave.open(output,'wb') as audio:
        audio.setnchannels(1);audio.setsampwidth(2);audio.setframerate(16000)
        audio.writeframes(b'\0\0'*int(16000*seconds))
    return output.getvalue()


def test_transcription_appends_no_session(athlete_client,monkeypatch):
    monkeypatch.setattr(training,'transcribe',lambda raw:'Hice cinco rondas con treinta kilos.')
    response=athlete_client.post('/api/training-sessions/transcribe',files={'file':('recording.wav',wav())})
    assert response.status_code==200
    assert response.json()['text']=='Hice cinco rondas con treinta kilos.'
    assert athlete_client.get('/api/training-sessions').json()['items']==[]


def test_audio_limits(athlete_client):
    for raw,status in [(b'',422),(b'a'*(voice.AUDIO_LIMIT+1),413)]:
        assert athlete_client.post('/api/training-sessions/transcribe',files={'file':('x.wav',raw)}).status_code==status


def test_unconfigured_and_provider_failure(athlete_client,monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    assert athlete_client.post('/api/training-sessions/transcribe',files={'file':('x.wav',wav())}).status_code==503
    def failure(raw):raise ConnectionError('Private provider detail')
    monkeypatch.setattr(training,'transcribe',failure)
    response=athlete_client.post('/api/training-sessions/transcribe',files={'file':('x.wav',wav())})
    assert response.status_code==502
    assert 'Private' not in response.text


def test_coach_and_guest_denied(coach_client):
    assert coach_client.post('/api/training-sessions/transcribe',files={'file':('x.wav',wav())}).status_code==403
    coach_client.post('/api/auth/logout')
    assert coach_client.post('/api/training-sessions/transcribe',files={'file':('x.wav',wav())}).status_code==401


def test_actual_decode_and_multipart(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self):return json.dumps({'text':'  AMRAP de doce minutos.  '}).encode()
    def request(req,timeout):
        assert req.full_url.endswith('/audio/transcriptions')
        assert timeout==45
        assert b'name="language"\r\n\r\nes' in req.data
        assert b'filename="recording.wav"' in req.data
        assert b'RIFF' in req.data
        return Response()
    monkeypatch.setattr(voice,'urlopen',request)
    assert voice.transcribe(wav())=='AMRAP de doce minutos.'


@pytest.mark.parametrize('raw',[b'not audio',wav(181)],ids=['invalid','over_three_minutes'])
def test_invalid_or_long_audio_not_sent(raw,monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    def never(*args,**kwargs):raise AssertionError('Invalid audio must not reach provider')
    monkeypatch.setattr(voice,'urlopen',never)
    with pytest.raises(ValueError):voice.transcribe(raw)


def test_empty_transcript(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self):return b'{"text":""}'
    monkeypatch.setattr(voice,'urlopen',lambda *args,**kwargs:Response())
    with pytest.raises(ValueError,match='legible'):voice.transcribe(wav())


def test_webm_without_duration_header(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    raw=subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','sine=frequency=440:duration=1','-c:a','libopus','-f','webm','-live','1','pipe:1'],capture_output=True,check=True,timeout=10).stdout
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self):return b'{"text":"Cinco rondas"}'
    monkeypatch.setattr(voice,'urlopen',lambda *args,**kwargs:Response())
    assert voice.transcribe(raw)=='Cinco rondas'
