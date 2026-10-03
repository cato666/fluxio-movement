import json
from uuid import uuid4
import cv2
import numpy as np
from app import training
from app.models import Athlete, TrainingImage, User
from app.services import workout_interpretation as ai
from tests.test_training_sessions import payload


def draft(**changes):
    return dict(title='AMRAP 12', workout='12 minutos: 10 thrusters', result_text=None,
                adaptations=None, rpe=None,
                blocks=[dict(title='Metcon', format='amrap', prescription='12 minutos',
                             movements=[dict(name='Thrusters', prescription='10 repeticiones · 30 kg')])],
                questions=['¿Cuál fue tu resultado?'], **changes)


def photo():
    return cv2.imencode('.png', np.zeros((40, 60, 3), dtype=np.uint8))[1].tobytes()


def test_private_image_and_link(athlete_client, session, monkeypatch, tmp_path):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    upload = athlete_client.post('/api/training-sessions/images', files={'file': ('board.png', photo(), 'image/png')})
    assert upload.status_code == 201, upload.text
    image = upload.json()
    response = athlete_client.get(image['url'])
    assert response.status_code == 200
    assert response.headers['content-type'] == 'image/jpeg'
    assert response.headers['cache-control'] == 'private, no-store'
    assert response.content.startswith(b'\xff\xd8')
    saved = athlete_client.post('/api/training-sessions', json=payload(source_image_id=image['id'], blocks=draft()['blocks']))
    assert saved.status_code == 201, saved.text
    assert saved.json()['source_image_id'] == image['id']
    assert saved.json()['blocks'][0]['format'] == 'amrap'
    identifier = saved.json()['id']
    assert athlete_client.get('/api/training-sessions/' + identifier).json()['blocks'] == draft()['blocks']


def test_image_validation(athlete_client, monkeypatch, tmp_path):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    for data, code in [(b'<svg></svg>', 422), (b'\x89PNG\r\n\x1a\ninvalid', 422), (b'a' * (training.IMAGE_LIMIT + 1), 413)]:
        assert athlete_client.post('/api/training-sessions/images', files={'file': ('x.png', data, 'image/png')}).status_code == code
    assert not (tmp_path/'training-images').exists()


def test_foreign_images(athlete_client, session, monkeypatch):
    other=User(id=uuid4(),name='Other',role='ATHLETE'); session.add(other); session.flush()
    session.add(Athlete(user_id=other.id));session.flush()
    image=TrainingImage(athlete_id=other.id,path='other.jpg');session.add(image);session.commit()
    def never(*args):
        raise AssertionError('Foreign image must not reach provider')
    monkeypatch.setattr(training,'interpret',never)
    assert athlete_client.get('/api/training-sessions/images/'+str(image.id)).status_code == 404
    assert athlete_client.post('/api/training-sessions/interpret',json={'image_id':str(image.id)}).status_code == 404
    assert athlete_client.post('/api/training-sessions',json=payload(source_image_id=str(image.id))).status_code == 404


def test_interpret_does_not_save(athlete_client, monkeypatch):
    monkeypatch.setattr(training,'interpret',lambda text,image: draft())
    response=athlete_client.post('/api/training-sessions/interpret',json={'text':'AMRAP 12 minutos: 10 thrusters'})
    assert response.status_code == 200
    assert response.json()['result_text'] is None
    assert response.json()['questions']
    assert athlete_client.get('/api/training-sessions').json()['items'] == []


def test_unavailable_and_invalid_provider(athlete_client, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    assert athlete_client.post('/api/training-sessions/interpret',json={'text':'AMRAP 12'}).status_code == 503
    assert athlete_client.post('/api/training-sessions/interpret',json={}).status_code == 422
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    monkeypatch.setattr(ai,'_request',lambda *args:{'output_text':'invalid'})
    assert athlete_client.post('/api/training-sessions/interpret',json={'text':'AMRAP 12'}).status_code == 502


def test_provider_contract(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY','test-key')
    captured={}
    def request(body,key):
        captured.update(body)
        return {'output_text':json.dumps(draft())}
    monkeypatch.setattr(ai,'_request',request)
    result=ai.interpret('Hice 5 rondas',b'image')
    assert result['rpe'] is None
    assert captured['store'] is False
    assert captured['text']['format']['strict'] is True
    assert captured['input'][1]['content'][1]['image_url'].startswith('data:image/jpeg;base64,')
    assert captured['text']['format']['schema']['additionalProperties'] is False


def test_photo_reaches_provider(athlete_client,monkeypatch,tmp_path):
    monkeypatch.setenv('STORAGE_PATH',str(tmp_path))
    image=athlete_client.post('/api/training-sessions/images',files={'file':('board.png',photo())}).json()
    def interpret(text,raw):
        assert raw.startswith(b'\xff\xd8')
        return draft()
    monkeypatch.setattr(training,'interpret',interpret)
    assert athlete_client.post('/api/training-sessions/interpret',json={'image_id':image['id']}).status_code == 200


def test_coach_cannot_upload_or_interpret(coach_client):
    assert coach_client.post('/api/training-sessions/images',files={'file':('board.png',photo())}).status_code == 403
    assert coach_client.post('/api/training-sessions/interpret',json={'text':'WOD'}).status_code == 403
