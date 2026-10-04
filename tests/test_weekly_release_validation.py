"""Release gates only. Never connects to real messaging providers."""
import hashlib
import json
import os
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from PIL import Image
from sqlalchemy import select, text, func
from app.database import engine
from app.models import Athlete, User, TrainingSession, WeeklyShare
from app.seed import DEMO_ATHLETE_ID
from app.services.auth import hash_password
from app.services.training_contracts import SessionPayload
from app.services.training_service import TrainingService
from app.services.weekly_summary import WeeklySummaryService
from tests.whatsapp_helpers import configure, payload, webhook, FakeProvider, PHONE


def evidence(name, data):
    directory = Path(os.getenv('WEEKLY_RELEASE_REPORT_DIR', 'results/releases/weekly-sharing-20261004'))
    directory.mkdir(parents=True, exist_ok=True)
    (directory / (name + '.json')).write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')


def dump_preexisting():
    with engine.connect() as connection:
        tables = connection.scalars(text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename NOT IN ('alembic_version','weekly_shares') ORDER BY tablename"))
        data = {}
        for table in list(tables):
            # Names are database catalog identifiers, never user input.
            rows = connection.scalars(text(f'SELECT row_to_json(t) FROM "{table}" t')).all()
            data[table] = sorted(json.dumps(row, sort_keys=True, default=str) for row in rows)
        return data


def test_exact_0020_0021_roundtrip_preserves_all_preexisting_rows(session, monkeypatch, tmp_path):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    configure(monkeypatch)
    from tests.test_whatsapp_foundation import link
    link(session)
    raw = BytesIO(); Image.new('RGB', (80, 80), 'green').save(raw, format='PNG')
    service = TrainingService(session, DEMO_ATHLETE_ID)
    photo = service.store_image(raw.getvalue())
    saved = service.create(SessionPayload(trained_on='2026-10-02', title='Preexisting workout',
        workout='5x5', result_text='50 kg', adaptations='Preexisting adaptation',
        rpe=7, source_image_id=photo.id))
    service.add_athlete_note(saved['id'], 'Preexisting personal note')
    photo_path = service.image_path(photo.id)
    photo_hash = hashlib.sha256(photo_path.read_bytes()).hexdigest()
    session.close()
    config = Config('alembic.ini')
    command.downgrade(config, '0020_whatsapp_capture')
    original = dump_preexisting()
    stages = []
    for operation, revision in [('upgrade','0021_weekly_shares'),
                                ('downgrade','0020_whatsapp_capture'),
                                ('upgrade','0021_weekly_shares')]:
        getattr(command, operation)(config, revision)
        assert dump_preexisting() == original
        assert hashlib.sha256(photo_path.read_bytes()).hexdigest() == photo_hash
        with engine.connect() as connection:
            actual = connection.scalar(text('SELECT version_num FROM alembic_version'))
            present = connection.scalar(text("SELECT to_regclass('public.weekly_shares') IS NOT NULL"))
        assert actual == revision
        assert present == (operation == 'upgrade')
        stages.append({'operation':operation,'revision':actual,'preexisting_rows_identical':True,'photo_identical':True})
        if operation == 'upgrade' and len(stages) == 1:
            WeeklySummaryService(session, DEMO_ATHLETE_ID).create_share()
            session.close()
    assert session.scalar(select(func.count()).select_from(WeeklyShare)) == 0
    command.check(config)
    evidence('migration-roundtrip', {'stages':stages,
        'table_counts':{name:len(rows) for name,rows in original.items()},
        'preexisting_digest':hashlib.sha256(json.dumps(original,sort_keys=True).encode()).hexdigest(),
        'downgrade_drops_new_share_records':True,'metadata_matches_head':True})


def fixture_photo(client):
    raw = BytesIO(); Image.new('RGB', (80, 80), 'green').save(raw, format='PNG')
    response = client.post('/api/training-sessions/images', files={'file':('board.png',raw.getvalue(),'image/png')})
    assert response.status_code == 201
    return response.json()['id']


@pytest.mark.parametrize('state', ['valid','expired','revoked','nonexistent'])
def test_public_content_and_security_matrix(athlete_client, session, monkeypatch, tmp_path, state):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    configure(monkeypatch)
    from tests.test_whatsapp_foundation import link
    link(session)  # The phone identity exists; omission is not an empty-data artifact.
    photo = fixture_photo(athlete_client)
    response = athlete_client.post('/api/training-sessions', json={
        'trained_on':'2026-10-02','title':'AUTHORIZED_WORKOUT','workout':'AUTHORIZED_PRESCRIPTION',
        'result_text':'AUTHORIZED_RESULT','adaptations':'AUTHORIZED_NOTE','rpe':7,
        'source_text':'PRIVATE_INTERPRETATION_SOURCE','source_image_id':photo})
    assert response.status_code == 201
    share = athlete_client.post('/api/training-week/shares',json={'day':'2026-10-02'}).json()
    row = session.get(WeeklyShare, UUID(share['id']))
    if state == 'expired':
        row.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1); session.commit()
    if state == 'revoked':
        assert athlete_client.delete('/api/training-week/shares/'+share['id']).status_code == 200
    if state == 'nonexistent':
        share['path'] = '/shared/week/' + 'z'*43
    athlete_client.post('/api/auth/logout')
    page = athlete_client.get(share['path'])
    image = athlete_client.get(share['path']+'/images/'+photo)
    expected = 200 if state == 'valid' else 404
    assert page.status_code == image.status_code == expected
    for result in [page,image]:
        assert result.headers['cache-control'] == 'no-store'
        assert result.headers['x-robots-tag'] == 'noindex, nofollow'
        assert result.headers['referrer-policy'] == 'no-referrer'
    assert 'frame-ancestors' in page.headers['content-security-policy']
    assert 'name="robots" content="noindex,nofollow"' in page.text
    assert 'athlete_id' not in page.text and str(DEMO_ATHLETE_ID) not in page.text
    assert PHONE not in page.text and 'PRIVATE_INTERPRETATION_SOURCE' not in page.text
    if state == 'valid':
        for value in ['AUTHORIZED_WORKOUT','AUTHORIZED_PRESCRIPTION','AUTHORIZED_RESULT','AUTHORIZED_NOTE']:
            assert value in page.text
        assert image.headers['content-type'] == 'image/jpeg'
        assert image.headers['x-content-type-options'] == 'nosniff'
        Image.open(BytesIO(image.content)).verify()
        assert photo in page.text
        assert set(row.snapshot['items'][0]) == {'title','workout','result_text','adaptations','rpe','trained_on','source_image_id'}
    else:
        assert 'AUTHORIZED_WORKOUT' not in page.text
    evidence('public-'+state, {'html_status':page.status_code,'photo_status':image.status_code,
        'headers':{key:page.headers[key] for key in ['cache-control','x-robots-tag','referrer-policy','content-security-policy']},
        'identity_metadata_absent':True,'authorized_fields_only':True})


def test_two_athletes_cannot_cross_private_or_shared_resources(athlete_client, session, monkeypatch, tmp_path):
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    athlete_b = User(id=uuid4(), name='Release athlete B', demo_key='release-b', role='ATHLETE', password_hash=hash_password('fixture-password'))
    session.add(athlete_b); session.flush(); session.add(Athlete(user_id=athlete_b.id)); session.commit()
    bservice = TrainingService(session, athlete_b.id)
    raw = BytesIO(); Image.new('RGB',(80,80),'blue').save(raw,format='PNG')
    bphoto = bservice.store_image(raw.getvalue())
    bsession = bservice.create(SessionPayload(trained_on='2026-10-02',title='PRIVATE_B_WORKOUT',workout='PRIVATE_B_CONTENT',source_image_id=bphoto.id))
    bshare = WeeklySummaryService(session,athlete_b.id).create_share(date(2026,10,2))
    ashare = athlete_client.post('/api/training-week/shares',json={'day':'2026-10-02'}).json()
    assert athlete_client.get('/api/training-sessions/'+str(bsession['id'])).status_code == 404
    assert athlete_client.get('/api/training-sessions/images/'+str(bphoto.id)).status_code == 404
    assert athlete_client.delete('/api/training-week/shares/'+bshare['id']).status_code == 404
    assert athlete_client.get(ashare['path']+'/images/'+str(bphoto.id)).status_code == 404
    assert 'PRIVATE_B_WORKOUT' not in athlete_client.get(ashare['path']).text
    assert all(item['id'] != bshare['id'] for item in athlete_client.get('/api/training-week/shares?day=2026-10-02').json()['items'])
    # A bearer link deliberately permits its recipient to read B's authorized copy.
    assert athlete_client.get(bshare['path']).status_code == 200
    evidence('athlete-isolation', {'private_session_denied':True,'private_photo_denied':True,
        'cross_revoke_denied':True,'cross_token_photo_denied':True,
        'bearer_link_authorized_copy_readable':True})


def test_configurable_ttl_without_waiting(athlete_client, monkeypatch):
    fixed = datetime(2026,10,4,12,tzinfo=timezone.utc)
    monkeypatch.setattr('app.services.weekly_summary.now', lambda: fixed)
    monkeypatch.setenv('WEEKLY_SHARE_TOKEN_TTL_HOURS','1')
    share = athlete_client.post('/api/training-week/shares',json={}).json()
    assert datetime.fromisoformat(share['expires_at']) == fixed + timedelta(hours=1)
    monkeypatch.setattr('app.services.weekly_summary.now', lambda: fixed + timedelta(minutes=59))
    assert athlete_client.get(share['path']).status_code == 200
    monkeypatch.setattr('app.services.weekly_summary.now', lambda: fixed + timedelta(hours=1))
    assert athlete_client.get(share['path']).status_code == 404
    monkeypatch.setenv('WEEKLY_SHARE_TOKEN_TTL_HOURS','168')
    monkeypatch.setattr('app.services.weekly_summary.now', lambda: fixed)
    default = athlete_client.post('/api/training-week/shares',json={}).json()
    assert datetime.fromisoformat(default['expires_at']) == fixed + timedelta(days=7)
    evidence('ttl', {'configured_hours':1,'before_expiry_status':200,'at_expiry_status':404,'release_default_hours':168})


def test_whatsapp_exact_commands_use_configured_real_public_base(client, session, monkeypatch):
    from tests.test_whatsapp_foundation import link
    from app.whatsapp.worker import process_one
    from app.whatsapp.security import Vault
    from app.whatsapp.models import WhatsAppOutbox
    base = os.getenv('WEEKLY_RELEASE_PUBLIC_BASE_URL')
    if not base:
        pytest.skip('Release runner must supply actual PUBLIC_BASE_URL; no real-domain claim without it')
    parsed = urlsplit(base)
    assert parsed.scheme == 'https' and parsed.hostname and not parsed.query and not parsed.fragment
    configure(monkeypatch); link(session)
    monkeypatch.setenv('PUBLIC_BASE_URL',base)
    provider = FakeProvider(); vault = Vault()
    for command_text in ['resumen semana','compartir semana','revocar semana']:
        event = payload(command_text)
        assert webhook(client,event).status_code == 200
        assert process_one(provider,vault)
        assert webhook(client,event).json()['accepted'] == 0
    session.expire_all()
    texts = [vault.decrypt(row.payload_encrypted,row.key_version)['text'] for row in session.scalars(select(WhatsAppOutbox))]
    assert any('Semana ' in value and 'días activos' in value for value in texts)
    share_text = next(value for value in texts if value.startswith('Semana compartida:'))
    generated_url = share_text.splitlines()[0].removeprefix('Semana compartida: ')
    assert generated_url.startswith(base.rstrip('/')+'/shared/week/')
    assert any('Enlaces de esa semana revocados.' == value for value in texts)
    assert session.scalar(select(func.count()).select_from(WeeklyShare)) == 1
    assert session.scalar(select(WeeklyShare)).revoked_at is not None
    evidence('whatsapp-domain', {'configured_public_base_url':base,'generated_origin':urlsplit(generated_url).netloc,
        'all_three_commands_passed':True,'replay_deduplicated':True,'provider':'FakeProvider',
        'live_messages_sent':False})
