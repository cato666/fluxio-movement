import copy
import json
import subprocess

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import OperationalError

from app import main
from app.database import SessionLocal, get_session
from app.models import Analysis, Repetition
from tests.analysis_helpers import write_analysis


RESULT = {
    'video': {'fps': 30, 'frames': 90, 'duration_s': 3, 'resolution': [320, 240]},
    'pose_frames': 20, 'repetitions_detected': 1,
    'repetitions': [{'repetition': 1, 'start_s': 0.0, 'bottom_s': 1.0, 'end_s': 2.0, 'min_knee_angle': 85.0}],
    'summary_metrics': {'min_knee_angle': 85.0, 'min_hip_angle': 70.0, 'max_trunk_from_vertical': 20.0},
    'timeline': [], 'notes': ['MVP técnico'],
}


def test_health_and_existing_ui(athlete_client):
    assert athlete_client.get('/api/health').json() == {'ok': True, 'database': 'ready'}
    assert athlete_client.get('/').status_code == 200
    assert athlete_client.get('/static/app.js').status_code == 200


def test_health_schema_not_ready(athlete_client, session):
    original_revision = session.scalar(text('SELECT version_num FROM alembic_version'))
    session.execute(text("UPDATE alembic_version SET version_num = 'outdated'"))
    session.commit()
    try:
        assert athlete_client.get('/api/health').status_code == 503
    finally:
        session.execute(text('UPDATE alembic_version SET version_num = :revision'), {'revision': original_revision})
        session.commit()


def test_database_unavailable(athlete_client):
    class Unavailable:
        def execute(self, *args):
            raise OperationalError('connect', {}, Exception('offline'))
        get = execute
        def rollback(self):
            pass
    main.app.dependency_overrides[get_session] = lambda: Unavailable()
    try:
        assert athlete_client.get('/api/health').status_code == 503
        assert athlete_client.post('/api/analyze', files={'file': ('x.mp4', b'x', 'video/mp4')}).status_code == 503
        assert not list(main.UPLOADS.iterdir())
    finally:
        main.app.dependency_overrides.clear()


def test_unsupported_upload_has_no_side_effects(athlete_client, session):
    assert athlete_client.post('/api/analyze', files={'file': ('bad.txt', b'bad')}).status_code == 400
    assert athlete_client.post('/api/analyze').status_code == 422
    assert session.scalar(select(func.count()).select_from(Analysis)) == 0
    assert not list(main.UPLOADS.iterdir())


def test_missing_seed_returns_actionable_error(athlete_client, session):
    session.execute(text('DELETE FROM athletes'))
    session.commit()
    response = athlete_client.post('/api/analyze', files={'file': ('squat.mp4', b'demo')})
    assert response.status_code == 503
    assert 'seed' in response.json()['detail']
    assert not list(main.UPLOADS.iterdir())


def test_analyze_preserves_contract_and_commits_repetitions(athlete_client, monkeypatch, valid_preflight):
    monkeypatch.setattr(main, 'analyze_video', lambda _video, output, *_: write_analysis(output, copy.deepcopy(RESULT)))
    response = athlete_client.post('/api/analyze', files={'file': ('squat.mp4', b'demo', 'video/mp4')})
    assert response.status_code == 200
    data = response.json()
    assert all(data[key] == value for key, value in RESULT.items())
    with SessionLocal() as session:
        row = session.get(Analysis, data['job_id'])
        assert row.status == 'COMPLETED'
        assert row.result == data
        assert row.completed_at.tzinfo is not None
        assert session.scalar(select(Repetition)).metrics == RESULT['repetitions'][0]


@pytest.mark.parametrize('mode', ['analyzer_failure', 'invalid_repetition'])
def test_failure_is_persisted_without_partial_results(athlete_client, monkeypatch, session, mode, valid_preflight):
    def fail(_video, output, *_):
        if mode == 'analyzer_failure':
            raise RuntimeError('decode failure')
        result = copy.deepcopy(RESULT)
        result['repetitions'][0]['end_s'] = -1
        return write_analysis(output, result)
    monkeypatch.setattr(main, 'analyze_video', fail)
    response = athlete_client.post('/api/analyze', files={'file': ('bad.mp4', b'bad')})
    assert response.status_code == 500
    assert isinstance(response.json()['detail'], str)
    row = session.scalar(select(Analysis))
    assert row.status == 'FAILED'
    assert row.error
    assert row.result is None
    assert session.scalar(select(func.count()).select_from(Repetition)) == 0


def test_real_mp4_without_pose_is_rejected_and_failure_persists(athlete_client, tmp_path):
    """Real preflight rejects a black clip; a video container alone is insufficient."""
    source = tmp_path / 'synthetic.mp4'
    subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x240:r=15:d=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(source)], check=True, capture_output=True)
    with source.open('rb') as video:
        response = athlete_client.post('/api/analyze', files={'file': ('synthetic.mp4', video, 'video/mp4')})
    assert response.status_code == 500, response.text
    with SessionLocal() as session:
        row = session.scalar(select(Analysis))
        assert row.status == 'FAILED'
        assert 'pose suficiente' in row.error
        assert row.result is None
        assert session.scalar(select(func.count()).select_from(Repetition)) == 0
