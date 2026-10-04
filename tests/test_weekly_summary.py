from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from uuid import uuid4
from PIL import Image
from sqlalchemy import select, func
from app.models import Athlete, User, TrainingSession, WeeklyShare
from app.seed import DEMO_ATHLETE_ID
from app.services.training_service import TrainingService
from app.services.training_contracts import SessionPayload
from app.services.weekly_summary import week_start


def create(client, **changes):
    response = client.post('/api/training-sessions', json={
        'trained_on': '2026-10-02', 'title': 'Sentadilla', 'workout': '5x5',
        'result_text': '50 kg', 'adaptations': 'Menor carga', **changes})
    assert response.status_code == 201, response.text
    return response.json()


def test_complete_week_excludes_other_athletes_and_outside_dates(athlete_client, session):
    for day in ['2026-09-27', '2026-09-28', '2026-10-04', '2026-10-05']:
        create(athlete_client, trained_on=day)
    create(athlete_client, rpe=8)
    create(athlete_client, rpe=6)
    other = User(id=uuid4(), name='Other', role='ATHLETE')
    session.add(other); session.flush(); session.add(Athlete(user_id=other.id)); session.commit()
    TrainingService(session, other.id).create(SessionPayload(trained_on='2026-10-02', title='Private', workout='Private'))
    data = athlete_client.get('/api/training-week?day=2026-10-04').json()
    assert data['week_start'] == '2026-09-28' and data['week_end'] == '2026-10-04'
    assert data['session_count'] == 4 and data['active_days'] == 3
    assert data['average_rpe'] == 7 and data['rpe_count'] == 2
    assert all(item['title'] != 'Private' for item in data['items'])


def test_summary_not_limited_to_200_rows(athlete_client, session):
    session.add_all([TrainingSession(athlete_id=DEMO_ATHLETE_ID, trained_on=date(2026, 10, 2),
        title='WOD', source_text='', workout='WOD', video_links=[], blocks=[]) for _ in range(205)])
    session.commit()
    assert athlete_client.get('/api/training-week?day=2026-10-02').json()['session_count'] == 205


def test_empty_week_and_santiago_boundary(athlete_client, monkeypatch):
    monkeypatch.setattr('app.services.weekly_summary.now', lambda: datetime(2026, 10, 5, 1, tzinfo=timezone.utc))
    assert week_start() == date(2026, 9, 28)  # Sunday evening in Santiago.
    data = athlete_client.get('/api/training-week').json()
    assert data['session_count'] == 0 and data['average_rpe'] is None
    assert athlete_client.get('/api/training-week?day=bad').status_code == 422


def test_snapshot_public_escape_no_private_metadata_and_revocation(athlete_client, session):
    item = create(athlete_client, title='<script>alert(1)</script>', source_text='SECRET_SOURCE')
    response = athlete_client.post('/api/training-week/shares', json={'day': '2026-10-02'})
    assert response.status_code == 201
    share = response.json(); token = share['path'].split('/')[-1]
    row = session.get(WeeklyShare, share['id'])
    assert row.token_hash != token and len(row.token_hash) == 64
    athlete_client.put('/api/training-sessions/' + item['id'], json={
        'trained_on':'2026-10-02', 'title':'Changed', 'workout':'Changed'})
    athlete_client.post('/api/auth/logout')
    public = athlete_client.get(share['path'])
    assert public.status_code == 200
    assert '&lt;script&gt;' in public.text and '<script>' not in public.text
    assert 'SECRET_SOURCE' not in public.text and 'Changed' not in public.text
    for key, value in [('cache-control','no-store'), ('referrer-policy','no-referrer'), ('x-robots-tag','noindex, nofollow')]:
        assert public.headers[key] == value
    assert athlete_client.get('/api/training-week').status_code == 401
    athlete_client.post('/api/auth/login', json={'username':'gaston','password':'demo1234'})
    assert athlete_client.delete('/api/training-week/shares/' + share['id']).status_code == 200
    assert athlete_client.get(share['path']).status_code == 404
    assert athlete_client.get('/api/training-week/shares?day=2026-10-02').json()['items'] == []


def test_expiry_and_share_ownership(athlete_client, session):
    create(athlete_client)
    share = athlete_client.post('/api/training-week/shares', json={'day':'2026-10-02'}).json()
    row = session.get(WeeklyShare, share['id']); row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1); session.commit()
    response = athlete_client.get(share['path'])
    assert response.status_code == 404 and response.headers['cache-control'] == 'no-store'
    assert athlete_client.get('/shared/week/invalid').status_code == 404
    other = User(id=uuid4(), name='Other', role='ATHLETE')
    session.add(other); session.flush(); session.add(Athlete(user_id=other.id)); session.flush()
    row.athlete_id = other.id; session.commit()
    assert athlete_client.delete('/api/training-week/shares/' + share['id']).status_code == 404


def test_shared_photos_scoped_to_snapshot_and_revocable(athlete_client, monkeypatch, tmp_path):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    raw = BytesIO(); Image.new('RGB', (100, 100)).save(raw, format='PNG')
    image = athlete_client.post('/api/training-sessions/images', files={'file':('board.png',raw.getvalue(),'image/png')}).json()
    create(athlete_client, source_image_id=image['id'])
    share = athlete_client.post('/api/training-week/shares', json={'day':'2026-10-02'}).json()
    photo = share['path'] + '/images/' + image['id']
    athlete_client.post('/api/auth/logout')
    assert athlete_client.get(photo).status_code == 200
    assert athlete_client.get(photo).headers['cache-control'] == 'no-store'
    assert athlete_client.get(share['path'] + '/images/' + str(uuid4())).status_code == 404
    assert athlete_client.get('/api/training-sessions/images/' + image['id']).status_code == 401
    athlete_client.post('/api/auth/login', json={'username':'gaston','password':'demo1234'})
    athlete_client.delete('/api/training-week/shares/' + share['id'])
    assert athlete_client.get(photo).status_code == 404


def test_coach_cannot_operate_week(coach_client):
    assert coach_client.get('/api/training-week').status_code == 403
    assert coach_client.post('/api/training-week/shares', json={}).status_code == 403


def test_revoke_week_includes_every_link_but_preserves_other_weeks(athlete_client):
    first = athlete_client.post('/api/training-week/shares', json={'day':'2026-10-02'}).json()
    second = athlete_client.post('/api/training-week/shares', json={'day':'2026-10-04'}).json()
    previous = athlete_client.post('/api/training-week/shares', json={'day':'2026-09-25'}).json()
    assert athlete_client.delete('/api/training-week/shares?day=2026-10-02').status_code == 200
    assert athlete_client.get(first['path']).status_code == 404
    assert athlete_client.get(second['path']).status_code == 404
    assert athlete_client.get(previous['path']).status_code == 200


def test_whatsapp_week_summary_share_replay_and_revoke(client, session, monkeypatch):
    from tests.whatsapp_helpers import configure, payload, webhook, FakeProvider
    from tests.test_whatsapp_foundation import link
    from app.whatsapp.worker import process_one
    from app.whatsapp.security import Vault
    from app.whatsapp.models import WhatsAppOutbox
    configure(monkeypatch); link(session)
    monkeypatch.setenv('PUBLIC_BASE_URL', 'https://fluxio.example')
    provider = FakeProvider(); vault = Vault()
    for command in ['resumen semanal', 'resumen semana pasada', 'compartir semana']:
        body = payload(command)
        assert webhook(client, body).status_code == 200
        assert process_one(provider, vault)
        assert webhook(client, body).json()['accepted'] == 0
    session.expire_all()
    assert session.scalar(select(func.count()).select_from(WeeklyShare)) == 1
    texts = [vault.decrypt(row.payload_encrypted, row.key_version)['text']
        for row in session.scalars(select(WhatsAppOutbox))]
    assert any('días activos' in text for text in texts)
    assert any('https://fluxio.example/shared/week/' in text for text in texts)
    assert webhook(client, payload('revocar semana')).status_code == 200
    assert process_one(provider, vault)
    session.expire_all(); assert session.scalar(select(WeeklyShare)).revoked_at is not None
