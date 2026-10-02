from app.models import CoachReview
from tests.test_coach_requests import CARLOS_ID, completed_analysis


def test_list_exposes_pending_and_completed_review_metadata(athlete_client, session):
    completed_analysis(session)
    assert athlete_client.get('/api/analyses').json()['items'][0]['coach_reviews'] == []
    created = athlete_client.post('/api/analyses/completed/request-review', json={'coach_id': str(CARLOS_ID)})
    assert created.status_code == 201
    listed = athlete_client.get('/api/analyses').json()['items'][0]
    assert listed['coach_reviews'][0]['status'] == 'PENDING'
    assert listed['coach_reviews'][0]['coach']['name'] == 'Carlos'
    review = session.get(CoachReview, created.json()['id'])
    review.status = 'COMPLETED'
    from datetime import datetime, timezone
    review.main_focus = 'Controlar profundidad'
    review.next_session = 'Tres series controladas'
    review.completed_at = datetime.now(timezone.utc)
    session.commit()
    refreshed = athlete_client.get('/api/analyses').json()['items'][0]
    assert refreshed['status'] == 'COMPLETED'
    assert refreshed['coach_reviews'][0]['status'] == 'COMPLETED'
    assert refreshed['coach_reviews'] == athlete_client.get('/api/analyses/completed').json()['coach_reviews']


def test_list_review_metadata_remains_scoped_to_logged_in_athlete(athlete_client, session):
    from uuid import uuid4
    from app.models import User, Athlete
    other = uuid4()
    session.add(User(id=other, name='Other', role='ATHLETE'))
    session.flush()
    session.add(Athlete(user_id=other))
    session.flush()
    row = completed_analysis(session, 'private')
    row.athlete_id = other
    session.add(CoachReview(analysis_id=row.id, athlete_id=other, coach_id=CARLOS_ID, status='PENDING'))
    session.commit()
    assert athlete_client.get('/api/analyses').json()['items'] == []
    assert athlete_client.get('/api/analyses/private').status_code == 404
