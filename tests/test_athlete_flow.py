import copy
import json
import subprocess
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import func, select, text

from app import main
from app.database import SessionLocal, engine
from app.models import Analysis, Athlete, Repetition, User
from app.seed import DEMO_ATHLETE_ID, seed
from tests.test_api import RESULT
from tests.analysis_helpers import write_analysis


def post_analysis(athlete_client, **fields):
    form = {'exercise': 'Sentadilla', 'objective': 'Mejorar profundidad', 'load_kg': '60.5'}
    form.update(fields)
    if form.get('load_kg') == '':
        form.pop('load_kg')
    return athlete_client.post('/api/analyses', data=form, files={'file': ('squat.mp4', b'video-demo', 'video/mp4')})


def test_new_analysis_list_detail_and_repetitions(athlete_client, monkeypatch, valid_preflight):
    def analyze_existing(video, out, exercise=None, *_args, **_kwargs):
        with SessionLocal() as session:
            row = session.scalar(select(Analysis))
            assert row.status == 'PROCESSING'
            assert row.exercise == 'Sentadilla'
            assert row.load_kg == 60.5
            assert row.objective == 'Mejorar profundidad'
            assert (main.UPLOADS / f'{row.id}.mp4').read_bytes() == b'video-demo'
            assert exercise == 'Sentadilla'
        return write_analysis(out, copy.deepcopy(RESULT))
    monkeypatch.setattr(main, 'analyze_video', analyze_existing)
    response = post_analysis(athlete_client)
    assert response.status_code == 202, response.text
    item = athlete_client.get('/api/analyses/' + response.json()['id']).json()
    assert item['status'] == 'COMPLETED'
    assert item['exercise'] == 'Sentadilla'
    assert item['load_kg'] == 60.5
    assert item['objective'] == 'Mejorar profundidad'
    assert item['repetitions_detected'] == 1
    assert item['repetitions'][0]['bottom_s'] == 1
    assert athlete_client.get(item['original_video_url']).content == b'video-demo'
    with SessionLocal() as session:
        row = session.get(Analysis, item['id'])
        assert row.analysis_json_path == 'analysis/' + item['id'] + '/analysis.json'
        assert row.annotated_video_path == 'results/' + item['id'] + '/annotated.mp4'
        assert row.result['repetitions_detected'] == 1
        assert session.scalar(select(Repetition)).analysis_id == item['id']
    listed = athlete_client.get('/api/analyses').json()['items']
    assert len(listed) == 1
    assert listed[0]['id'] == item['id']
    assert listed[0]['repetitions_detected'] == 1
    assert 'analysis_json' not in listed[0]
    assert athlete_client.get('/api/analyses/' + item['id']).json() == item


def test_preflight_report_is_persisted_with_completed_analysis(athlete_client, monkeypatch):
    preflight = {
        'quality': {'status': 'WARNING', 'pose_coverage': .58, 'warnings': ['Pose intermitente'], 'blockers': []},
        'exercise': {'status': 'INCONCLUSIVE', 'confidence': 'low'},
    }
    monkeypatch.setattr(main, 'validate_video_exercise', lambda *_: preflight)
    def analyzed(_, output_dir, *__, **___):
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        (output / 'annotated.mp4').write_bytes(b'annotated')
        (output / 'analysis.json').write_text('{}')
        return copy.deepcopy(RESULT)
    monkeypatch.setattr(main, 'analyze_video', analyzed)
    athlete_client.post('/api/auth/login', json={'username': 'gaston', 'password': 'demo1234'})
    response = post_analysis(athlete_client)
    assert response.status_code == 202
    detail = athlete_client.get('/api/analyses/' + response.json()['id']).json()
    assert detail['analysis_json']['preflight'] == preflight


def test_failed_analysis_remains_in_list_and_detail(athlete_client, monkeypatch, valid_preflight):
    def fail(*_, **__):
        raise RuntimeError('technical decode error')
    monkeypatch.setattr(main, 'analyze_video', fail)
    response = post_analysis(athlete_client, load_kg='')
    assert response.status_code == 202
    job = response.json()['id']
    listed = athlete_client.get('/api/analyses').json()['items']
    assert len(listed) == 1
    assert listed[0]['status'] == 'FAILED'
    assert listed[0]['load_kg'] is None
    assert listed[0]['repetitions_detected'] == 0
    detail = athlete_client.get(f'/api/analyses/{job}').json()
    assert detail['error'] == 'technical decode error'
    assert detail['analysis_json'] is None
    assert detail['repetitions'] == []
    with SessionLocal() as session:
        assert session.get(Analysis, job).status == 'FAILED'


@pytest.mark.parametrize('form,filename,expected', [
    ({'exercise': '   '}, 'squat.mp4', 400),
    ({'objective': '   '}, 'squat.mp4', 400),
    ({'load_kg': '-1'}, 'squat.mp4', 400),
    ({'load_kg': 'Infinity'}, 'squat.mp4', 400),
    ({'load_kg': 'oops'}, 'squat.mp4', 422),
    ({}, 'notes.txt', 400),
])
def test_invalid_input_has_no_analysis(athlete_client, session, form, filename, expected):
    data = {'exercise': 'Sentadilla', 'objective': 'Mejorar técnica', 'load_kg': '10'}
    data.update(form)
    response = athlete_client.post('/api/analyses', data=data, files={'file': (filename, b'video')})
    assert response.status_code == expected
    assert session.scalar(select(func.count()).select_from(Analysis)) == 0


def test_pending_is_persisted_before_upload_finishes(athlete_client, monkeypatch, valid_preflight):
    original_copy = main.shutil.copyfileobj
    def inspect_before_copy(src, dest):
        with SessionLocal() as session:
            row = session.scalar(select(Analysis))
            assert row.status == 'PENDING'
        return original_copy(src, dest)
    monkeypatch.setattr(main.shutil, 'copyfileobj', inspect_before_copy)
    monkeypatch.setattr(main, 'analyze_video', lambda _video, output, *_, **__: write_analysis(output, copy.deepcopy(RESULT)))
    assert post_analysis(athlete_client).status_code == 202


def test_logical_restart_reads_from_postgres(athlete_client, monkeypatch, valid_preflight):
    monkeypatch.setattr(main, 'analyze_video', lambda _video, output, *_, **__: write_analysis(output, copy.deepcopy(RESULT)))
    job = post_analysis(athlete_client).json()['id']
    engine.dispose()
    with SessionLocal() as fresh_session:
        assert fresh_session.get(Analysis, job).status == 'COMPLETED'
    assert athlete_client.get('/api/analyses').json()['items'][0]['id'] == job
    assert athlete_client.get(f'/api/analyses/{job}').json()['repetitions'][0]['number'] == 1


def test_demo_only_list_and_detail(athlete_client, session):
    other_id = uuid4()
    session.add(User(id=other_id, name='Other athlete', role='ATHLETE'))
    session.flush()
    session.add(Athlete(user_id=other_id))
    session.flush()
    session.add(Analysis(id='other', athlete_id=other_id, original_filename='other.mp4', video_path='uploads/other.mp4'))
    session.commit()
    assert athlete_client.get('/api/analyses').json()['items'] == []
    assert athlete_client.get('/api/analyses/other').status_code == 404
    assert athlete_client.get('/api/analyses/missing').status_code == 404


def test_f11_row_survives_f12_migration(athlete_client, session):
    config = Config('alembic.ini')
    session.execute(text("DELETE FROM users WHERE role = 'SYSTEM_ADMIN'"))
    session.commit()
    session.close()
    command.downgrade(config, '0001_f1_persistence')
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO analyses (id, athlete_id, status, original_filename, video_path, annotated_video_path, result, completed_at) VALUES ('legacy', :athlete, 'COMPLETED', 'old.mp4', 'uploads/old.mp4', 'results/legacy/annotated.mp4', '{}'::jsonb, now())"), {'athlete': DEMO_ATHLETE_ID})
    try:
        command.upgrade(config, 'head')
        with SessionLocal.begin() as seeded:
            seed(seeded)
        athlete_client.post('/api/auth/login', json={'username': 'gaston', 'password': 'demo1234'})
        detail = athlete_client.get('/api/analyses/legacy').json()
        assert detail['exercise'] is None
        assert detail['load_kg'] is None
        assert detail['analysis_json_url'] == '/results/legacy/analysis.json'
        assert athlete_client.get('/api/analyses').json()['items'][0]['id'] == 'legacy'
        command.check(config)
    finally:
        command.upgrade(config, 'head')


def test_athlete_mp4_e2e_and_pages(athlete_client, tmp_path):
    for page in ('/', '/analyses/new', '/analyses'):
        assert athlete_client.get(page).status_code == 200
    html = athlete_client.get('/analyses/new').text
    for phrase in ('Nuevo análisis', 'Mis análisis', 'Gastón Demo', 'Tu siguiente paso'):
        assert phrase in html
    source = tmp_path / 'athlete.mp4'
    subprocess.run(['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=c=black:s=320x240:r=15:d=1', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(source)], check=True, capture_output=True)
    with source.open('rb') as video:
        response = athlete_client.post('/api/analyses', data={'exercise': 'Clean', 'objective': 'Ver trayectoria'}, files={'file': ('athlete.mp4', video, 'video/mp4')})
    assert response.status_code == 202, response.text
    item = athlete_client.get('/api/analyses/' + response.json()['id']).json()
    assert item['status'] == 'FAILED'
    assert 'pose suficiente' in item['error']
    assert item['repetitions_detected'] == 0
    assert athlete_client.get(item['original_video_url']).status_code == 200
    assert item['annotated_video_url'] is None
    assert item['analysis_json_url'] is None
    assert athlete_client.get('/analyses/' + item['id']).status_code == 200
    engine.dispose()
    assert athlete_client.get('/api/analyses').json()['items'][0]['id'] == item['id']

