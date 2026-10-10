from app import main
from sqlalchemy import select
from app.models import Analysis, Annotation, Athlete, Coach, CoachReview, Repetition, User
from app.seed import DEMO_ATHLETE_ID


def finished(session, identifier, **fields):
    row = Analysis(id=identifier, athlete_id=DEMO_ATHLETE_ID, status='FAILED', error='test',
                   original_filename='shared.mp4', video_path='uploads/shared.mp4', **fields)
    session.add(row)
    session.commit()
    return row


def test_delete_preserves_shared_original_and_reanalysis(athlete_client, session):
    video = main.UPLOADS / 'shared.mp4'
    video.write_bytes(b'video')
    finished(session, 'source')
    finished(session, 'child', source_analysis_id='source')
    session.add(Repetition(analysis_id='source', number=1, start_s=0, bottom_s=1, end_s=2, metrics={}))
    session.commit()
    assert athlete_client.delete('/api/analyses/source').status_code == 204
    session.expire_all()
    assert session.get(Analysis, 'source') is None
    assert session.get(Analysis, 'child').source_analysis_id is None
    assert video.exists()
    assert athlete_client.get('/api/analyses/source').status_code == 404
    assert athlete_client.delete('/api/analyses/child').status_code == 204
    assert not video.exists()


def test_delete_rejects_processing_and_missing_analysis(athlete_client, session):
    session.add(Analysis(id='processing', athlete_id=DEMO_ATHLETE_ID, status='PROCESSING',
                         original_filename='x.mp4', video_path='uploads/x.mp4'))
    session.commit()
    assert athlete_client.delete('/api/analyses/processing').status_code == 409
    assert athlete_client.delete('/api/analyses/missing').status_code == 404


def test_delete_requires_authentication(client, session):
    finished(session, 'private')
    assert client.delete('/api/analyses/private').status_code == 401
    assert session.get(Analysis, 'private') is not None


def test_coach_cannot_delete_athlete_analysis(coach_client, session):
    finished(session, 'owned')
    assert coach_client.delete('/api/analyses/owned').status_code == 403
    assert session.get(Analysis, 'owned') is not None


def test_athlete_cannot_delete_another_athletes_analysis(athlete_client, session):
    other = User(name='Otro atleta', role='ATHLETE')
    session.add(other)
    session.flush()
    session.add(Athlete(user_id=other.id))
    session.flush()
    session.add(Analysis(id='other', athlete_id=other.id, status='FAILED', error='test',
                         original_filename='other.mp4', video_path='uploads/other.mp4'))
    session.commit()
    assert athlete_client.delete('/api/analyses/other').status_code == 404
    assert session.get(Analysis, 'other') is not None


def test_delete_removes_associated_review_and_comments(athlete_client, session):
    finished(session, 'reviewed')
    coach = session.scalars(select(Coach)).first()
    review = CoachReview(analysis_id='reviewed', athlete_id=DEMO_ATHLETE_ID, coach_id=coach.user_id)
    session.add(review)
    session.flush()
    comment = Annotation(review_id=review.id, timestamp_s=1, body='Comentario')
    session.add(comment)
    session.commit()
    review_id, comment_id = review.id, comment.id
    assert athlete_client.delete('/api/analyses/reviewed').status_code == 204
    session.expire_all()
    assert session.get(CoachReview, review_id) is None
    assert session.get(Annotation, comment_id) is None
