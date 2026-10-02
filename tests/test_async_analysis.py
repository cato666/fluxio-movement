import copy
import json
from pathlib import Path

from sqlalchemy import select

from app import main
from app.database import SessionLocal
from app.models import Analysis
from app.seed import DEMO_ATHLETE_ID


def test_background_worker_completes_persisted_analysis(session, monkeypatch):
    job = 'async-completes'
    source = main.UPLOADS / f'{job}.mp4'
    source.write_bytes(b'not-a-real-video')
    session.add(Analysis(
        id=job, athlete_id=DEMO_ATHLETE_ID, status='PROCESSING',
        original_filename='clean.mp4', video_path=f'uploads/{source.name}',
        progress=5, stage='analyzing',
    ))
    session.commit()

    def fake_analyzer(_video, output_dir, *_args, **_kwargs):
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        (output / 'annotated.mp4').write_bytes(b'annotated')
        result = {
            'video': {'duration_s': 3.0},
            'repetitions': [{'repetition': 1, 'start_s': 0.0, 'bottom_s': 1.0, 'end_s': 2.0}],
        }
        (output / 'analysis.json').write_text(json.dumps(result), encoding='utf-8')
        return copy.deepcopy(result)

    monkeypatch.setattr(main, 'analyze_video', fake_analyzer)
    monkeypatch.setattr(main, '_thumbnail', lambda *_: False)
    main._process_analysis(job, 'Clean', 'side')

    session.expire_all()
    completed = session.get(Analysis, job)
    assert completed.status == 'COMPLETED'
    assert completed.progress == 100
    assert completed.stage is None
    assert completed.annotated_video_path == f'results/{job}/annotated.mp4'


def test_analysis_returns_202_and_persists_processing_progress(athlete_client, monkeypatch):
    monkeypatch.setattr(main, '_process_analysis', lambda *_: None)
    response = athlete_client.post('/api/analyses', data={'exercise': 'Clean', 'objective': 'Trayectoria'}, files={'file': ('clean.mp4', b'video', 'video/mp4')})
    assert response.status_code == 202
    payload = response.json()
    assert payload['status'] == 'PROCESSING'
    assert payload['progress'] == 5
    assert payload['stage'] == 'analyzing'


def test_thumbnail_url_is_exposed_and_null_when_missing(athlete_client, session):
    thumbnail = main.RESULTS / 'with-thumb' / 'thumbnail.jpg'
    thumbnail.parent.mkdir()
    thumbnail.write_bytes(b'jpg')
    session.add_all([
        Analysis(id='with-thumb', athlete_id=DEMO_ATHLETE_ID, status='COMPLETED', original_filename='x.mp4', video_path='uploads/x.mp4', annotated_video_path='results/with-thumb/annotated.mp4', result={}, completed_at=main.datetime.now(main.timezone.utc), thumbnail_path='results/with-thumb/thumbnail.jpg', progress=100),
        Analysis(id='without-thumb', athlete_id=DEMO_ATHLETE_ID, status='COMPLETED', original_filename='y.mp4', video_path='uploads/y.mp4', annotated_video_path='results/without-thumb/annotated.mp4', result={}, completed_at=main.datetime.now(main.timezone.utc), progress=100),
    ])
    session.commit()
    items = {item['id']: item for item in athlete_client.get('/api/analyses').json()['items']}
    assert items['with-thumb']['thumbnail_url'] == '/results/with-thumb/thumbnail.jpg'
    assert items['without-thumb']['thumbnail_url'] is None
    assert athlete_client.get(items['with-thumb']['thumbnail_url']).status_code == 200


def test_recovery_marks_interrupted_processing_as_failed(session):
    row = Analysis(id='interrupted', athlete_id=DEMO_ATHLETE_ID, status='PROCESSING', original_filename='x.mp4', video_path='uploads/x.mp4', progress=42, stage='analyzing')
    session.add(row); session.commit()
    main.recover_interrupted_analyses()
    session.expire_all()
    saved = session.get(Analysis, 'interrupted')
    assert saved.status == 'FAILED'
    assert 'reinició' in saved.error
