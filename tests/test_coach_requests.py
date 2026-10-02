from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.models import Analysis, Athlete, CoachReview, User
from app.seed import DEMO_ATHLETE_ID, DEMOS


CARLOS_ID = DEMOS[1][0]
ANDREA_ID = DEMOS[2][0]


def completed_analysis(session, analysis_id='completed'):
    row = Analysis(
        id=analysis_id, athlete_id=DEMO_ATHLETE_ID, status='COMPLETED',
        exercise='Sentadilla', objective='Mejorar profundidad',
        original_filename='squat.mp4', video_path='uploads/squat.mp4',
        annotated_video_path='results/completed/annotated.mp4',
        analysis_json_path='results/completed/analysis.json', result={},
        completed_at=datetime.now(timezone.utc),
    )
    session.add(row)
    session.commit()
    return row


def test_coaches_are_seeded_with_specialty_and_bio(athlete_client):
    response = athlete_client.get('/api/coaches')
    assert response.status_code == 200
    assert response.json()['items'] == [
        {'id': str(ANDREA_ID), 'name': 'Annais', 'specialty': 'Fuerza',
         'bio': 'Entrenamiento de fuerza para construir movimiento sólido y sostenible.'},
        {'id': str(CARLOS_ID), 'name': 'Carlos', 'specialty': 'Weightlifting',
         'bio': 'Técnica de levantamientos olímpicos y progresiones de fuerza.'},
        {'id': str(DEMOS[3][0]), 'name': 'Pablo', 'specialty': 'CrossFit',
         'bio': 'Rendimiento funcional y técnica aplicada a movimientos de CrossFit.'},
    ]


def test_request_review_persists_and_detail_names_coach(athlete_client, session):
    completed_analysis(session)
    response = athlete_client.post('/api/analyses/completed/request-review', json={'coach_id': str(CARLOS_ID)})
    assert response.status_code == 201, response.text
    review = response.json()
    assert review['status'] == 'PENDING'
    assert review['analysis_id'] == 'completed'
    assert review['athlete_id'] == str(DEMO_ATHLETE_ID)
    assert review['coach']['name'] == 'Carlos'
    persisted = session.get(CoachReview, review['id'])
    assert persisted.analysis_id == 'completed'
    assert persisted.athlete_id == DEMO_ATHLETE_ID
    assert persisted.coach_id == CARLOS_ID
    detail = athlete_client.get('/api/analyses/completed').json()
    assert detail['coach_reviews'][0]['status'] == 'PENDING'
    assert detail['coach_reviews'][0]['coach']['name'] == 'Carlos'
    page = athlete_client.get('/analyses/completed').text
    assert 'Tu siguiente paso' in page
    assert 'id="request-review-link"' in page
    assert athlete_client.get('/analyses/completed/request-review').status_code == 200


def test_active_request_cannot_be_duplicated_but_another_coach_is_allowed(athlete_client, session):
    completed_analysis(session)
    first = athlete_client.post('/api/analyses/completed/request-review', json={'coach_id': str(CARLOS_ID)})
    duplicate = athlete_client.post('/api/analyses/completed/request-review', json={'coach_id': str(CARLOS_ID)})
    other = athlete_client.post('/api/analyses/completed/request-review', json={'coach_id': str(ANDREA_ID)})
    assert first.status_code == 201
    assert duplicate.status_code == 409
    assert 'solicitud activa' in duplicate.json()['detail']
    assert other.status_code == 201
    assert len(session.scalars(select(CoachReview).where(CoachReview.analysis_id == 'completed')).all()) == 2


@pytest.mark.parametrize('status, expected', [('PENDING', 409), ('PROCESSING', 409), ('FAILED', 409)])
def test_request_requires_completed_analysis(athlete_client, session, status, expected):
    row = Analysis(
        id=status.lower(), athlete_id=DEMO_ATHLETE_ID, status=status,
        original_filename='squat.mp4', video_path='uploads/squat.mp4',
        error='failed' if status == 'FAILED' else None,
    )
    session.add(row)
    session.commit()
    response = athlete_client.post(f'/api/analyses/{status.lower()}/request-review', json={'coach_id': str(CARLOS_ID)})
    assert response.status_code == expected
    assert session.scalars(select(CoachReview)).all() == []


def test_request_rejects_unknown_coach_and_other_athlete_analysis(athlete_client, session):
    completed_analysis(session)
    assert athlete_client.post('/api/analyses/completed/request-review', json={'coach_id': str(uuid4())}).status_code == 404
    other_id = uuid4()
    session.add(User(id=other_id, name='Other athlete', role='ATHLETE'))
    session.flush()
    session.add(Athlete(user_id=other_id))
    session.flush()
    session.add(Analysis(
        id='other', athlete_id=other_id, status='COMPLETED',
        original_filename='other.mp4', video_path='uploads/other.mp4',
        annotated_video_path='results/other/annotated.mp4', result={},
        completed_at=datetime.now(timezone.utc),
    ))
    session.commit()
    assert athlete_client.post('/api/analyses/other/request-review', json={'coach_id': str(CARLOS_ID)}).status_code == 404
