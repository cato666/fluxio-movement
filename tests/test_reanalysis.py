from sqlalchemy import select

from app import main
from app.models import Analysis
from app.seed import DEMO_ATHLETE_ID


def test_reanalysis_creates_a_new_analysis_with_same_original_video(athlete_client, session, monkeypatch):
    source_file = main.UPLOADS / 'source.mp4'
    source_file.write_bytes(b'original-video')
    source = Analysis(
        id='source', athlete_id=DEMO_ATHLETE_ID, status='FAILED', error='Selecciona otro ejercicio',
        exercise='Peso muerto', view='side', objective='Técnica', original_filename='source.mp4',
        video_path='uploads/source.mp4', progress=100,
    )
    session.add(source); session.commit()
    monkeypatch.setattr(main, '_process_analysis', lambda *_: None)
    response = athlete_client.post('/api/analyses/source/reanalyze', json={'exercise': 'Thruster', 'view': 'side'})
    assert response.status_code == 202, response.text
    payload = response.json()
    assert payload['id'] != 'source'
    assert payload['status'] == 'PROCESSING'
    assert payload['exercise'] == 'Thruster'
    assert payload['view'] == 'side'
    created = session.scalar(select(Analysis).where(Analysis.id == payload['id']))
    assert created.source_analysis_id == 'source'
    assert created.video_path == 'uploads/source.mp4'


def test_reanalysis_requires_a_finished_owned_analysis(athlete_client, session):
    source = Analysis(id='working', athlete_id=DEMO_ATHLETE_ID, status='PROCESSING', exercise='Press', view='side', objective='Técnica', original_filename='x.mp4', video_path='uploads/x.mp4')
    session.add(source); session.commit()
    assert athlete_client.post('/api/analyses/working/reanalyze', json={'exercise': 'Press', 'view': 'side'}).status_code == 409
