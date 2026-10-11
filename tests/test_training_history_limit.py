"""S17: the listing cap is not a retention or creation limit."""
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4
import pytest
from sqlalchemy import func, select
from app.models import Athlete, PlanInteraction, TrainingImage, TrainingSession, User
from app.seed import DEMO_ATHLETE_ID


def history(session, count, *, tied=False):
    stamp = datetime(2026, 10, 2, 12, tzinfo=timezone.utc)
    rows = [TrainingSession(id=UUID(int=index + 1), athlete_id=DEMO_ATHLETE_ID,
        trained_on=date(2026, 10, 2), title=f'Fixture {index}', source_text='',
        workout='5x5', result_text='50 kg', video_links=[], blocks=[],
        created_at=stamp if tied else stamp + timedelta(seconds=index)) for index in range(count)]
    session.add_all(rows)
    session.commit()
    return rows


@pytest.mark.parametrize('count', [199, 200, 201])
def test_boundary_listing_and_complete_week(athlete_client, session, count):
    rows = history(session, count)
    response = athlete_client.get('/api/training-sessions')
    assert response.status_code == 200
    assert set(response.json()) == {'items'}  # Preserve existing HTTP contract.
    items = response.json()['items']
    assert len(items) == min(count, 200)
    assert [item['id'] for item in items] == [str(row.id) for row in reversed(rows[-200:])]
    summary = athlete_client.get('/api/training-week?day=2026-10-02')
    assert summary.status_code == 200
    assert summary.json()['session_count'] == count
    assert len(summary.json()['items']) == count
    assert session.scalar(select(func.count()).select_from(TrainingSession)) == count
    assert athlete_client.get('/api/training-sessions/' + str(rows[0].id)).status_code == 200


def test_ties_have_repeatable_membership_at_boundary(athlete_client, session):
    rows = history(session, 201, tied=True)
    expected = [str(row.id) for row in reversed(rows[1:])]
    for _ in range(3):
        assert [item['id'] for item in athlete_client.get('/api/training-sessions').json()['items']] == expected
    assert session.scalar(select(func.count()).select_from(TrainingSession)) == 201


def test_old_detail_edit_photo_survive_cap(athlete_client, session, monkeypatch, tmp_path):
    rows = history(session, 201)
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    identifier = uuid4()
    folder = tmp_path / 'training-images'; folder.mkdir()
    photo = folder / f'{identifier}.jpg'; photo.write_bytes(b'synthetic-photo')
    session.add(TrainingImage(id=identifier, athlete_id=DEMO_ATHLETE_ID, path=photo.name))
    session.flush()
    rows[0].source_image_id = identifier
    rows[0].adaptations = 'Historical note'
    session.commit()
    oldest = str(rows[0].id)
    assert oldest not in [item['id'] for item in athlete_client.get('/api/training-sessions').json()['items']]
    url = '/api/training-sessions/' + oldest
    detail = athlete_client.get(url).json()
    assert detail['adaptations'] == 'Historical note'
    assert athlete_client.get('/api/training-sessions/images/' + str(identifier)).content == b'synthetic-photo'
    changed = athlete_client.put(url, json={'trained_on':'2026-10-02','title':'Edited old record','workout':'5x5'})
    assert changed.status_code == 200
    assert changed.json()['source_image_id'] == str(identifier)
    assert changed.json()['adaptations'] == 'Historical note'
    assert photo.exists()
    summary = athlete_client.get('/api/training-week?day=2026-10-02').json()
    assert summary['session_count'] == 201
    assert any(item['title'] == 'Edited old record' for item in summary['items'])


def test_other_athlete_cannot_access_old_records(athlete_client, session):
    rows = history(session, 201)
    foreign = User(id=uuid4(), name='Synthetic other athlete', role='ATHLETE')
    session.add(foreign); session.flush()
    session.add(Athlete(user_id=foreign.id)); session.flush()
    row = TrainingSession(athlete_id=foreign.id, trained_on=date(2026,10,2), title='Private other',
        source_text='', workout='Private', video_links=[], blocks=[])
    session.add(row); session.commit()
    assert all(item['title'] != 'Private other' for item in athlete_client.get('/api/training-sessions').json()['items'])
    foreign_url = '/api/training-sessions/' + str(row.id)
    assert athlete_client.get(foreign_url).status_code == 404
    assert athlete_client.put(foreign_url,json={'trained_on':'2026-10-02','title':'Changed','workout':'Changed'}).status_code == 404
    assert athlete_client.delete(foreign_url).status_code == 404
    assert athlete_client.get('/api/training-week?day=2026-10-02').json()['session_count'] == 201


def test_manual_creation_beyond_cap_has_no_ai_consumption(athlete_client, session, monkeypatch):
    history(session, 200)
    monkeypatch.setenv('USAGE_INTERPRET_DAILY', '0')
    monkeypatch.setenv('USAGE_TRANSCRIBE_DAILY', '0')
    monkeypatch.setenv('USAGE_GLOBAL_DAILY_USD', '0')
    before = session.scalar(select(func.count()).select_from(PlanInteraction))
    created = athlete_client.post('/api/training-sessions',json={'trained_on':'2026-10-03','title':'Manual 201','workout':'5x5'})
    assert created.status_code == 201
    assert len(athlete_client.get('/api/training-sessions').json()['items']) == 200
    assert athlete_client.get('/api/training-sessions/' + created.json()['id']).status_code == 200
    assert session.scalar(select(func.count()).select_from(TrainingSession)) == 201
    assert session.scalar(select(func.count()).select_from(PlanInteraction)) == before


def test_inactive_account_cannot_read_capped_or_old_history(athlete_client, session):
    rows = history(session, 201)
    user = session.get(User, DEMO_ATHLETE_ID); user.is_active = False; session.commit()
    for url in ('/api/training-sessions','/api/training-sessions/' + str(rows[0].id),'/api/training-week?day=2026-10-02'):
        assert athlete_client.get(url).status_code in (401,403)
    assert session.scalar(select(func.count()).select_from(TrainingSession)) == 201
