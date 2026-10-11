import json
from pathlib import Path
from alembic import command
from alembic.config import Config
from app.main import app
from app.models import TrainingSession
from app.seed import DEMO_ATHLETE_ID
from app.services.training_contracts import SessionPayload
from app.services.training_service import TrainingService


def test_all_baseline_http_operations_and_schemas_are_preserved():
    baseline=json.loads((Path(__file__).parent/'fixtures/whatsapp-baseline-openapi.json').read_text())
    current=app.openapi()
    for path, contract in baseline['paths'].items():
        for operation, expected in contract.items():
            actual = dict(current['paths'][path][operation])
            if operation == 'post' and path in ('/api/training-sessions/interpret', '/api/training-sessions/transcribe', '/api/analyze', '/api/analyses', '/api/analyses/{analysis_id}/reanalyze'):
                parameters = actual.get('parameters', [])
                added = [p for p in parameters if p['name'] == 'idempotency-key']
                assert len(added) == 1 and added[0]['in'] == 'header' and not added[0]['required']
                kept = [p for p in parameters if p['name'] != 'idempotency-key']
                if kept: actual['parameters'] = kept
                else: actual.pop('parameters', None)
            assert actual == expected, (path, operation)
    for name, schema in baseline['components']['schemas'].items():
        if name == 'SharePayload':
            actual = current['components']['schemas'][name]
            assert actual['properties']['day'] == schema['properties']['day']
            assert set(actual['properties']) == {'day', 'consent', 'consent_version', 'request_id'}
            assert actual['properties']['consent']['default'] is False
            assert actual['additionalProperties'] is False
        else:
            assert current['components']['schemas'][name]==schema, name


def test_migration_roundtrip_preserves_existing_bitacora(session):
    row=TrainingService(session,DEMO_ATHLETE_ID).create(SessionPayload(
        trained_on='2026-10-01',title='Baseline workout',workout='4 rondas: remo',adaptations='20 kg'))
    session.close()
    config=Config('alembic.ini')
    command.downgrade(config,'0018_training_ai_usage')
    command.upgrade(config,'head')
    actual=session.get(TrainingSession,row['id'])
    assert actual.workout==row['workout'] and actual.adaptations==row['adaptations']
    assert actual.athlete_id==DEMO_ATHLETE_ID and actual.athlete_notes==[]
    command.check(config)
