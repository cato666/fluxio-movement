from uuid import uuid4
from app.models import Analysis, Athlete, TrainingSession, User


def payload(**changes):
    return {'trained_on': '2026-10-02', 'title': 'AMRAP 12',
            'source_text': '10 thrusters y 12 burpees',
            'workout': 'AMRAP 12 minutos: 10 thrusters y 12 burpees',
            'result_text': '5 rondas + 8 thrusters', 'rpe': 8, **changes}


def test_create_read_update_without_video(athlete_client):
    response = athlete_client.post('/api/training-sessions', json=payload())
    assert response.status_code == 201, response.text
    row = response.json()
    assert row['video_links'] == []
    assert athlete_client.get('/api/training-sessions').json()['items'][0]['id'] == row['id']
    assert athlete_client.get('/api/training-sessions/' + row['id']).json()['source_text'] == payload()['source_text']
    changed = athlete_client.put('/api/training-sessions/' + row['id'], json=payload(rpe=None, result_text='6 rondas'))
    assert changed.status_code == 200
    assert changed.json()['rpe'] is None
    assert changed.json()['result_text'] == '6 rondas'


def test_validation_and_role(coach_client):
    assert coach_client.post('/api/training-sessions', json=payload()).status_code == 403


def test_invalid_fields(athlete_client):
    for changes in ({'rpe': 11}, {'rpe': 0}, {'rpe': 3.5}, {'workout': '  '}, {'title': ' '}, {'trained_on': 'invalid'}):
        assert athlete_client.post('/api/training-sessions', json=payload(**changes)).status_code == 422


def test_ownership(athlete_client, session):
    other = User(id=uuid4(), name='Otro atleta', role='ATHLETE')
    session.add(other); session.flush()
    session.add(Athlete(user_id=other.id)); session.flush()
    row = TrainingSession(athlete_id=other.id, **payload(video_links=[]))
    # SQLAlchemy Date expects a date instance.
    from datetime import date
    row.trained_on = date(2026, 10, 2)
    session.add(row)
    analysis = Analysis(id='foreign-analysis', athlete_id=other.id, original_filename='other.mp4', video_path='uploads/other.mp4')
    session.add(analysis); session.commit()
    assert athlete_client.get('/api/training-sessions/' + str(row.id)).status_code == 404
    assert athlete_client.put('/api/training-sessions/' + str(row.id), json=payload()).status_code == 404
    assert athlete_client.get('/api/training-sessions').json()['items'] == []
    assert athlete_client.post('/api/training-sessions', json=payload(video_links=[{'analysis_id': analysis.id, 'movement': 'Thruster'}])).status_code == 404


def test_link_own_analysis(athlete_client, session):
    from app.seed import DEMO_ATHLETE_ID
    session.add(Analysis(id='own-analysis', athlete_id=DEMO_ATHLETE_ID, original_filename='mine.mp4', video_path='uploads/mine.mp4'))
    session.commit()
    response = athlete_client.post('/api/training-sessions', json=payload(video_links=[{'analysis_id':'own-analysis', 'movement':'Thrusters', 'context':'Ronda 2'}]))
    assert response.status_code == 201
    assert response.json()['video_links'][0]['context'] == 'Ronda 2'


def test_requires_login(client):
    assert client.get('/api/training-sessions').status_code == 401
    assert client.get('/training', follow_redirects=False).status_code == 303
