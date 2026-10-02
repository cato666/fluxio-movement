from datetime import datetime, timezone

from app.models import Analysis, CoachReview, Repetition
from app.seed import DEMO_ATHLETE_ID, DEMOS


CARLOS_ID = DEMOS[1][0]
ANDREA_ID = DEMOS[2][0]


def review(session, analysis_id, coach_id=CARLOS_ID, status='PENDING'):
    analysis = Analysis(
        id=analysis_id, athlete_id=DEMO_ATHLETE_ID, status='COMPLETED',
        exercise='Sentadilla', load_kg=80, objective='Mejorar profundidad',
        original_filename='squat.mp4', video_path=f'uploads/{analysis_id}.mp4',
        annotated_video_path=f'results/{analysis_id}/annotated.mp4',
        analysis_json_path=f'results/{analysis_id}/analysis.json',
        result={'summary_metrics': {'min_knee_angle': 80}}, completed_at=datetime.now(timezone.utc),
    )
    session.add(analysis)
    session.flush()
    session.add(Repetition(
        analysis_id=analysis_id, number=1, start_s=0, bottom_s=1, end_s=2, metrics={},
    ))
    item = CoachReview(
        analysis_id=analysis_id, athlete_id=DEMO_ATHLETE_ID, coach_id=coach_id,
        status=status,
        summary='Revisión terminada' if status == 'COMPLETED' else None,
        main_focus='Profundidad consistente' if status == 'COMPLETED' else None,
        next_session='Practicar pausas' if status == 'COMPLETED' else None,
        completed_at=datetime.now(timezone.utc) if status == 'COMPLETED' else None,
    )
    session.add(item)
    session.commit()
    return item


def test_list_is_scoped_to_selected_coach_and_can_filter_status(coach_client, session):
    pending = review(session, 'pending')
    in_review = review(session, 'in-review', status='IN_REVIEW')
    completed = review(session, 'completed', status='COMPLETED')
    other = review(session, 'andrea', coach_id=ANDREA_ID)

    listed = coach_client.get(f'/api/coach/reviews?coach_id={CARLOS_ID}')
    assert listed.status_code == 200
    assert {item['id'] for item in listed.json()['items']} == {
        str(pending.id), str(in_review.id), str(completed.id),
    }
    assert str(other.id) not in {item['id'] for item in listed.json()['items']}
    assert {item['status'] for item in listed.json()['items']} == {'PENDING', 'IN_REVIEW', 'COMPLETED'}
    assert listed.json()['items'][0]['athlete']['name'] == 'Gastón Demo'
    assert listed.json()['items'][0]['analysis']['repetitions_detected'] == 1

    filtered = coach_client.get(f'/api/coach/reviews?coach_id={CARLOS_ID}&status=IN_REVIEW')
    assert filtered.status_code == 200
    assert [item['status'] for item in filtered.json()['items']] == ['IN_REVIEW']
    assert coach_client.get(f'/api/coach/reviews?coach_id={CARLOS_ID}&status=INVALID').status_code == 400


def test_detail_contains_assigned_review_analysis_and_repetitions(coach_client, session):
    item = review(session, 'detail')
    response = coach_client.get(f'/api/coach/reviews/{item.id}?coach_id={CARLOS_ID}')
    assert response.status_code == 200
    payload = response.json()
    assert payload['athlete']['name'] == 'Gastón Demo'
    assert payload['analysis']['exercise'] == 'Sentadilla'
    assert payload['analysis']['original_video_url'] == '/uploads/detail.mp4'
    assert payload['analysis']['annotated_video_url'] == '/results/detail/annotated.mp4'
    assert payload['analysis']['repetitions'][0]['start_s'] == 0


def test_other_coach_cannot_read_assigned_review(coach_client, session):
    item = review(session, 'private')
    assert coach_client.get(f'/api/coach/reviews/{item.id}?coach_id={ANDREA_ID}').status_code == 403
    assert coach_client.patch(f'/api/coach/reviews/{item.id}/start?coach_id={ANDREA_ID}').status_code == 403


def test_start_review_is_idempotent_and_does_not_reopen_completed(coach_client, session):
    pending = review(session, 'start')
    first = coach_client.patch(f'/api/coach/reviews/{pending.id}/start?coach_id={CARLOS_ID}')
    second = coach_client.patch(f'/api/coach/reviews/{pending.id}/start?coach_id={CARLOS_ID}')
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()['status'] == second.json()['status'] == 'IN_REVIEW'
    session.expire_all()
    assert session.get(CoachReview, pending.id).status == 'IN_REVIEW'

    completed = review(session, 'done', status='COMPLETED')
    response = coach_client.patch(f'/api/coach/reviews/{completed.id}/start?coach_id={CARLOS_ID}')
    assert response.status_code == 200
    assert response.json()['status'] == 'COMPLETED'
    assert session.get(CoachReview, completed.id).status == 'COMPLETED'


def test_missing_review_returns_404(coach_client):
    assert coach_client.get(f'/api/coach/reviews/00000000-0000-4000-8000-000000000099?coach_id={CARLOS_ID}').status_code == 404
    assert coach_client.patch(f'/api/coach/reviews/00000000-0000-4000-8000-000000000099/start?coach_id={CARLOS_ID}').status_code == 404
