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
            assert current['paths'][path][operation] == expected, (path, operation)
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
