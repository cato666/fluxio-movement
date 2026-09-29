from datetime import datetime, timezone
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError

from app.database import Base, SessionLocal, engine
from app.models import Analysis, Annotation, Athlete, Coach, Repetition, Review, User, AIObservation, AIObservationDecision
from app.seed import DEMO_ATHLETE_ID, DEMOS, seed


def analysis(session, key='a'):
    row = Analysis(id=key, athlete_id=DEMO_ATHLETE_ID, original_filename='test.mp4', video_path='uploads/test.mp4')
    session.add(row)
    session.flush()
    return row


def repetition(session, analysis_id='a', number=1):
    row = Repetition(analysis_id=analysis_id, number=number, start_s=0, bottom_s=1, end_s=2, metrics={'min_knee_angle': 85})
    session.add(row)
    session.flush()
    return row


def test_migration_roundtrip_and_no_model_drift():
    config = Config('alembic.ini')
    command.downgrade(config, 'base')
    assert set(inspect(engine).get_table_names()) == {'alembic_version'}
    command.upgrade(config, 'head')
    command.upgrade(config, 'head')
    assert set(Base.metadata.tables).issubset(inspect(engine).get_table_names())
    command.check(config)


def test_seed_is_idempotent_and_preserves_existing_data(session):
    seed(session)
    seed(session)
    session.commit()
    assert session.scalar(select(func.count()).select_from(User)) == 4
    assert session.scalar(select(func.count()).select_from(Athlete)) == 1
    assert session.scalar(select(func.count()).select_from(Coach)) == 3
    assert {(u.name, u.role) for u in session.scalars(select(User))} == {(d[2], d[3]) for d in DEMOS}
    assert set(session.scalars(select(Coach.specialty))) == {'Weightlifting', 'Fuerza', 'CrossFit'}
    session.get(User, DEMO_ATHLETE_ID).name = 'Edited demo'
    session.commit()
    seed(session)
    session.commit()
    assert session.get(User, DEMO_ATHLETE_ID).name == 'Edited demo'


def test_review_graph_survives_new_connection(session):
    analysis(session)
    rep = repetition(session)
    review = Review(analysis_id='a', athlete_id=DEMO_ATHLETE_ID, coach_id=DEMOS[1][0], best_repetition_id=rep.id,
                    work_repetition_id=rep.id, status='COMPLETED', summary='Buen control',
                    main_focus='Mantener postura', next_session='Practicar técnica',
                    completed_at=datetime.now(timezone.utc))
    session.add(review)
    observation = AIObservation(analysis_id='a', body='Observación automática', timestamp_s=1)
    session.add(observation)
    session.flush()
    annotation = Annotation(review_id=review.id, timestamp_s=1.25, body='Extiende la cadera')
    session.add_all([annotation, AIObservationDecision(review_id=review.id, observation_id=observation.id, analysis_id='a', decision='CONFIRMED')])
    session.commit()
    engine.dispose()
    with SessionLocal() as other:
        assert other.get(Annotation, annotation.id).timestamp_s == 1.25
        assert other.get(Review, review.id).best_repetition_id == rep.id
        assert other.get(Repetition, rep.id).metrics['min_knee_angle'] == 85
        assert other.get(AIObservationDecision, (review.id, observation.id)).decision == 'CONFIRMED'


@pytest.mark.parametrize('case', ['role', 'athlete_role', 'coach_role', 'missing_athlete', 'status', 'completed_analysis', 'failed_analysis', 'rep_times', 'rep_number', 'duplicate_rep', 'foreign_rep', 'missing_coach', 'review_summary', 'annotation_time', 'annotation_nan', 'annotation_body', 'foreign_observation', 'decision'])
def test_database_rejects_invalid_graphs(session, case):
    analysis(session)
    analysis(session, 'b')
    rep = repetition(session)
    foreign_rep = repetition(session, 'b')
    review = Review(analysis_id='a', athlete_id=DEMO_ATHLETE_ID, coach_id=DEMOS[1][0])
    session.add(review)
    observation = AIObservation(analysis_id='b', body='IA')
    session.add(observation)
    session.commit()
    with pytest.raises(IntegrityError):
        if case == 'role':
            session.add(User(name='X', role='ADMIN'))
        elif case == 'athlete_role':
            session.add(Athlete(user_id=DEMOS[1][0]))
        elif case == 'coach_role':
            session.add(Coach(user_id=DEMO_ATHLETE_ID, specialty='X'))
        elif case == 'missing_athlete':
            session.get(Analysis, 'a').athlete_id = uuid4()
        elif case == 'status':
            session.get(Analysis, 'a').status = 'INVALID'
        elif case == 'completed_analysis':
            session.get(Analysis, 'a').status = 'COMPLETED'
        elif case == 'failed_analysis':
            session.get(Analysis, 'a').status = 'FAILED'
        elif case == 'rep_times':
            rep.end_s = -1
        elif case == 'rep_number':
            rep.number = 0
        elif case == 'duplicate_rep':
            repetition(session)
        elif case == 'foreign_rep':
            review.best_repetition_id = foreign_rep.id
        elif case == 'missing_coach':
            review.coach_id = DEMO_ATHLETE_ID
        elif case == 'review_summary':
            review.status = 'COMPLETED'
        elif case.startswith('annotation_'):
            session.add(Annotation(review_id=review.id, timestamp_s=(-1 if case == 'annotation_time' else float('nan') if case == 'annotation_nan' else 0), body=(' ' if case == 'annotation_body' else 'test')))
        elif case in ('foreign_observation', 'decision'):
            if case == 'decision':
                observation.analysis_id = 'a'
                session.flush()
            session.add(AIObservationDecision(review_id=review.id, observation_id=observation.id, analysis_id='a', decision='INVALID' if case == 'decision' else 'CONFIRMED'))
        session.commit()
    session.rollback()
