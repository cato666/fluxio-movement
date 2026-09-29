import copy
import json
import subprocess

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import OperationalError

from app import main
from app.database import SessionLocal, get_session
from app.models import Analysis, Repetition


RESULT = {
    'video': {'fps': 30, 'frames': 90, 'duration_s': 3, 'resolution': [320, 240]},
    'pose_frames': 20, 'repetitions_detected': 1,
    'repetitions': [{'repetition': 1, 'start_s': 0.0, 'bottom_s': 1.0, 'end_s': 2.0, 'min_knee_angle': 85.0}],
    'summary_metrics': {'min_knee_angle': 85.0, 'min_hip_angle': 70.0, 'max_trunk_from_vertical': 20.0},
    'timeline': [], 'notes': ['MVP técnico'],
}


def test_health_and_existing_ui(client):
    assert client.get('/api/health').json() == {'ok': True, 'database': 'ready'}
    assert client.get('/').status_code == 200
    assert client.get('/static/app.js').status_code == 200


def test_health_schema_not_ready(client, session):
    session.execute(text("UPDATE alembic_version SET version_num = 'outdated'"))
    session.commit()
    try:
        assert client.get('/api/health').status_code == 503
    finally:
        session.execute(text("UPDATE alembic_version SET version_num = '0002_f12_athlete_analysis'"))
        session.commit()


def test_database_unavailable(client):
    class Unavailable:
        def execute(self, *args):
            raise OperationalError('connect', {}, Exception('offline'))
        get = execute
        def rollback(self):
            pass
    main.app.dependency_overrides[get_session] = lambda: Unavailable()
    try:
        assert client.get('/api/health').status_code == 503
        assert client.post('/api/analyze', files={'file': ('x.mp4', b'x', 'video/mp4')}).status_code == 503
        assert not list(main.UPLOADS.iterdir())
    finally:
        main.app.dependency_overrides.clear()


def test_unsupported_upload_has_no_side_effects(client, session):
    assert client.post('/api/analyze', files={'file': ('bad.txt', b'bad')}).status_code == 400
    assert client.post('/api/analyze').status_code == 422
    assert session.scalar(select(func.count()).select_from(Analysis)) == 0
    assert not list(main.UPLOADS.iterdir())


def test_missing_seed_returns_actionable_error(client, session):
    session.execute(text('DELETE FROM athletes'))
    session.commit()
    response = client.post('/api/analyze', files={'file': ('squat.mp4', b'demo')})
    assert response.status_code == 503
    assert 'seed' in response.json()['detail']
    assert not list(main.UPLOADS.iterdir())


def test_analyze_preserves_contract_and_commits_repetitions(client, monkeypatch):
    monkeypatch.setattr(main, 'analyze_video', lambda *_: copy.deepcopy(RESULT))
    response = client.post('/api/analyze', files={'file': ('squat.mp4', b'demo', 'video/mp4')})
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
def test_failure_is_persisted_without_partial_results(client, monkeypatch, session, mode):
    def fail(*_):
        if mode == 'analyzer_failure':
            raise RuntimeError('decode failure')
        result = copy.deepcopy(RESULT)
        result['repetitions'][0]['end_s'] = -1
        return result
    monkeypatch.setattr(main, 'analyze_video', fail)
    response = client.post('/api/analyze', files={'file': ('bad.mp4', b'bad')})
    assert response.status_code == 500
    assert isinstance(response.json()['detail'], str)
    row = session.scalar(select(Analysis))
    assert row.status == 'FAILED'
    assert row.error
    assert row.result is None
    assert session.scalar(select(func.count()).select_from(Repetition)) == 0


def test_real_mp4_to_analysis_files_and_postgres(client, tmp_path):
    """F1.1 E2E: real decoding, MediaPipe, FFmpeg, API and PostgreSQL, no mocks."""
    source = tmp_path / 'synthetic.mp4'
    subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x240:r=15:d=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(source)], check=True, capture_output=True)
    with source.open('rb') as video:
        response = client.post('/api/analyze', files={'file': ('synthetic.mp4', video, 'video/mp4')})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['video']['frames'] == 15
    assert result['repetitions_detected'] == 0
    assert client.get(result['annotated_video_url']).status_code == 200
    assert client.get(result['analysis_url']).json()['video'] == result['video']
    annotated = main.RESULTS / result['job_id'] / 'annotated.mp4'
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(annotated)], check=True, capture_output=True, text=True)
    assert json.loads(probe.stdout)['streams'][0]['codec_name'] == 'h264'
    with SessionLocal() as session:
        assert session.get(Analysis, result['job_id']).result == result
