from datetime import datetime, timezone

import pytest

from app.models import Analysis, CoachAnnotation, CoachReview, Repetition
from app.seed import DEMO_ATHLETE_ID, DEMOS


CARLOS_ID = DEMOS[1][0]
ANDREA_ID = DEMOS[2][0]


def review(session, analysis_id='review', status='IN_REVIEW'):
    session.add(Analysis(
        id=analysis_id, athlete_id=DEMO_ATHLETE_ID, status='COMPLETED',
        exercise='Clean', objective='Trayectoria de barra', original_filename='clean.mp4',
        video_path='uploads/clean.mp4', annotated_video_path=f'results/{analysis_id}/annotated.mp4',
        analysis_json_path=f'results/{analysis_id}/analysis.json',
        result={'video': {'duration_s': 12.5}}, completed_at=datetime.now(timezone.utc),
    ))
    session.flush()
    session.add(Repetition(analysis_id=analysis_id, number=1, start_s=1, bottom_s=2, end_s=3, metrics={}))
    item = CoachReview(
        analysis_id=analysis_id, athlete_id=DEMO_ATHLETE_ID, coach_id=CARLOS_ID,
        status=status,
        summary='Lista para atleta' if status == 'COMPLETED' else None,
        main_focus='Mantener la barra cerca' if status == 'COMPLETED' else None,
        next_session='Practicar con carga ligera' if status == 'COMPLETED' else None,
        completed_at=datetime.now(timezone.utc) if status == 'COMPLETED' else None,
    )
    session.add(item)
    session.commit()
    return item


def annotation_url(item):
    return f'/api/coach/reviews/{item.id}/annotations?coach_id={CARLOS_ID}'


def annotation_item_url(item, annotation_id, coach_id=CARLOS_ID):
    return f'/api/coach/reviews/{item.id}/annotations/{annotation_id}?coach_id={coach_id}'


def test_create_annotation_persists_and_starts_pending_review(coach_client, session):
    item = review(session, status='PENDING')
    response = coach_client.post(annotation_url(item), json={
        'timestamp_s': 2.74, 'type': 'PRIORITY',
        'text': 'Aquí la barra se desplaza hacia delante.', 'repetition_number': 1,
    })
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload['timestamp_s'] == 2.74
    assert payload['type'] == 'PRIORITY'
    assert payload['repetition_number'] == 1
    session.expire_all()
    assert session.get(CoachAnnotation, payload['id']).text == 'Aquí la barra se desplaza hacia delante.'
    assert session.get(CoachReview, item.id).status == 'IN_REVIEW'


def test_list_annotations_orders_by_timestamp(coach_client, session):
    item = review(session)
    for timestamp in (8, 1.5, 4):
        assert coach_client.post(annotation_url(item), json={
            'timestamp_s': timestamp, 'type': 'COMMENT', 'text': f'Comentario {timestamp}',
        }).status_code == 201
    response = coach_client.get(annotation_url(item))
    assert response.status_code == 200
    assert [entry['timestamp_s'] for entry in response.json()['items']] == [1.5, 4, 8]


def test_edit_and_delete_annotation(coach_client, session):
    item = review(session)
    created = coach_client.post(annotation_url(item), json={
        'timestamp_s': 2, 'type': 'COMMENT', 'text': 'Ajustar postura',
    }).json()
    update_url = annotation_item_url(item, created['id'])
    updated = coach_client.patch(update_url, json={
        'type': 'CORRECT', 'text': 'Extiende la cadera', 'repetition_number': 1,
    })
    assert updated.status_code == 200
    assert updated.json()['type'] == 'CORRECT'
    assert updated.json()['text'] == 'Extiende la cadera'
    assert coach_client.delete(update_url).status_code == 204
    assert coach_client.get(annotation_url(item)).json()['items'] == []


def test_annotations_are_isolated_between_coaches(coach_client, session):
    item = review(session)
    created = coach_client.post(annotation_url(item), json={
        'timestamp_s': 2, 'type': 'COMMENT', 'text': 'Comentario privado',
    }).json()
    other = f'/api/coach/reviews/{item.id}/annotations?coach_id={ANDREA_ID}'
    other_item = annotation_item_url(item, created['id'], ANDREA_ID)
    assert coach_client.get(other).status_code == 403
    assert coach_client.post(other, json={'timestamp_s': 2, 'type': 'COMMENT', 'text': 'No permitido'}).status_code == 403
    assert coach_client.patch(other_item, json={'text': 'No permitido'}).status_code == 403
    assert coach_client.delete(other_item).status_code == 403


@pytest.mark.parametrize('timestamp', [-0.1, 12.51])
def test_annotation_rejects_invalid_timestamp(coach_client, session, timestamp):
    item = review(session)
    response = coach_client.post(annotation_url(item), json={
        'timestamp_s': timestamp, 'type': 'COMMENT', 'text': 'Fuera de rango',
    })
    assert response.status_code == 400


def test_missing_review_returns_404_for_annotations(coach_client):
    url = '/api/coach/reviews/00000000-0000-4000-8000-000000000099/annotations?coach_id=' + str(CARLOS_ID)
    assert coach_client.get(url).status_code == 404
    assert coach_client.post(url, json={'timestamp_s': 1, 'type': 'COMMENT', 'text': 'Nada'}).status_code == 404


def test_completed_review_blocks_annotation_mutations(coach_client, session):
    item = review(session)
    created = coach_client.post(annotation_url(item), json={
        'timestamp_s': 2, 'type': 'COMMENT', 'text': 'Antes de completar',
    }).json()
    item.status = 'COMPLETED'
    item.summary = 'Revisión final'
    item.main_focus = 'Mantener la barra cerca'
    item.next_session = 'Practicar con carga ligera'
    item.completed_at = datetime.now(timezone.utc)
    session.commit()
    update_url = annotation_item_url(item, created['id'])
    assert coach_client.get(annotation_url(item)).status_code == 200
    assert coach_client.post(annotation_url(item), json={'timestamp_s': 3, 'type': 'COMMENT', 'text': 'Bloqueada'}).status_code == 409
    assert coach_client.patch(update_url, json={'text': 'Bloqueada'}).status_code == 409
    assert coach_client.delete(update_url).status_code == 409
