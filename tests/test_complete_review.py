from datetime import datetime, timezone

from app.models import Analysis, CoachReview, Repetition
from app.seed import DEMO_ATHLETE_ID, DEMOS


CARLOS_ID = DEMOS[1][0]
ANDREA_ID = DEMOS[2][0]


def review(session, analysis_id='complete-review'):
    session.add(Analysis(
        id=analysis_id, athlete_id=DEMO_ATHLETE_ID, status='COMPLETED',
        exercise='Press', objective='Bloqueo estable', original_filename='press.mp4',
        video_path=f'uploads/{analysis_id}.mp4', annotated_video_path=f'results/{analysis_id}/annotated.mp4',
        analysis_json_path=f'results/{analysis_id}/analysis.json',
        result={'video': {'duration_s': 12}, 'summary_metrics': {}},
        completed_at=datetime.now(timezone.utc),
    ))
    session.flush()
    repetitions = []
    for number, start in enumerate((1, 4, 7), 1):
        rep = Repetition(analysis_id=analysis_id, number=number, start_s=start, bottom_s=start + .5, end_s=start + 1, metrics={})
        session.add(rep)
        repetitions.append(rep)
    item = CoachReview(analysis_id=analysis_id, athlete_id=DEMO_ATHLETE_ID, coach_id=CARLOS_ID, status='IN_REVIEW')
    session.add(item)
    session.commit()
    return item, repetitions


def base_url(item, coach_id=CARLOS_ID):
    return f'/api/coach/reviews/{item.id}?coach_id={coach_id}'


def repetition_url(item, repetition, coach_id=CARLOS_ID):
    return f'/api/coach/reviews/{item.id}/repetitions/{repetition.id}?coach_id={coach_id}'


def add_annotation(client, item):
    return client.post(f'/api/coach/reviews/{item.id}/annotations?coach_id={CARLOS_ID}', json={
        'timestamp_s': 2, 'type': 'PRIORITY', 'text': 'Mantén la barra cerca.', 'repetition_number': 1,
    })


def save_required_summary(client, item):
    return client.patch(f'/api/coach/reviews/{item.id}/summary?coach_id={CARLOS_ID}', json={
        'strengths': 'Buen control inicial', 'main_focus': 'Bloquear los codos arriba',
        'next_session': 'Tres series de press con pausa', 'summary': 'Progreso sólido.',
    })


def test_best_and_needs_work_are_single_review_classifications(client, session):
    item, reps = review(session)
    assert client.patch(repetition_url(item, reps[0]), json={'classification': 'BEST'}).status_code == 200
    assert client.patch(repetition_url(item, reps[1]), json={'classification': 'BEST'}).status_code == 200
    assert client.patch(repetition_url(item, reps[2]), json={'classification': 'NEEDS_WORK'}).status_code == 200
    detail = client.get(base_url(item)).json()
    assert [rep['classification'] for rep in detail['analysis']['repetitions']] == ['NORMAL', 'BEST', 'NEEDS_WORK']
    session.expire_all()
    persisted = session.get(CoachReview, item.id)
    assert persisted.best_repetition_id == reps[1].id
    assert persisted.work_repetition_id == reps[2].id


def test_summary_is_persisted_and_other_coach_cannot_change_or_complete(client, session):
    item, reps = review(session)
    saved = save_required_summary(client, item)
    assert saved.status_code == 200
    assert saved.json()['main_focus'] == 'Bloquear los codos arriba'
    other_summary = f'/api/coach/reviews/{item.id}/summary?coach_id={ANDREA_ID}'
    other_complete = f'/api/coach/reviews/{item.id}/complete?coach_id={ANDREA_ID}'
    assert client.patch(other_summary, json={'main_focus': 'No permitido'}).status_code == 404
    assert client.patch(repetition_url(item, reps[0], ANDREA_ID), json={'classification': 'BEST'}).status_code == 404
    assert client.post(other_complete).status_code == 404


def test_complete_validates_requirements_and_locks_review(client, session):
    item, reps = review(session)
    complete_url = f'/api/coach/reviews/{item.id}/complete?coach_id={CARLOS_ID}'
    assert client.post(complete_url).status_code == 409
    assert add_annotation(client, item).status_code == 201
    assert client.post(complete_url).status_code == 409
    assert save_required_summary(client, item).status_code == 200
    completed = client.post(complete_url)
    assert completed.status_code == 200
    assert completed.json()['status'] == 'COMPLETED'
    assert completed.json()['completed_at']
    session.expire_all()
    assert session.get(CoachReview, item.id).completed_at is not None
    assert client.patch(repetition_url(item, reps[0]), json={'classification': 'BEST'}).status_code == 409
    assert client.patch(f'/api/coach/reviews/{item.id}/summary?coach_id={CARLOS_ID}', json={'main_focus': 'Cambio'}).status_code == 409
    assert client.post(f'/api/coach/reviews/{item.id}/annotations?coach_id={CARLOS_ID}', json={
        'timestamp_s': 3, 'type': 'COMMENT', 'text': 'Bloqueada',
    }).status_code == 409


def test_athlete_receives_completed_feedback_and_annotations(client, session):
    item, reps = review(session, 'athlete-feedback')
    assert add_annotation(client, item).status_code == 201
    assert client.patch(repetition_url(item, reps[0]), json={'classification': 'BEST'}).status_code == 200
    assert client.patch(repetition_url(item, reps[1]), json={'classification': 'NEEDS_WORK'}).status_code == 200
    assert save_required_summary(client, item).status_code == 200
    assert client.post(f'/api/coach/reviews/{item.id}/complete?coach_id={CARLOS_ID}').status_code == 200
    detail = client.get('/api/analyses/athlete-feedback')
    assert detail.status_code == 200
    feedback = detail.json()['completed_coach_reviews'][0]
    assert feedback['coach'] == {'id': str(CARLOS_ID), 'name': 'Carlos', 'specialty': 'Weightlifting'}
    assert feedback['best_repetition']['number'] == 1
    assert feedback['work_repetition']['number'] == 2
    assert feedback['main_focus'] == 'Bloquear los codos arriba'
    assert feedback['annotations'][0]['timestamp_s'] == 2
    assert feedback['annotations'][0]['text'] == 'Mantén la barra cerca.'
