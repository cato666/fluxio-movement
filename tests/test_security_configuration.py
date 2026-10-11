"""S04 startup and seed lifecycle; provider credentials here are synthetic only."""
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import select
from cryptography.fernet import Fernet

from app import main
from app.database import engine
from app.models import User
from app.seed import DEMO_ATHLETE_ID, seed
from app.services.auth import hash_password, verify_password
from app.security_config import SecurityConfigurationError, demo_seed_enabled, validate_security
from app.whatsapp.security import Vault


def production(monkeypatch, whatsapp=False):
    monkeypatch.delenv('POSTGRES_PASSWORD', raising=False)
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('ENABLE_DEMO_SEED', 'false')
    monkeypatch.delenv('DEMO_PASSWORD', raising=False)
    monkeypatch.setenv('SESSION_SECRET', secrets.token_urlsafe(48))
    monkeypatch.setenv('DATABASE_URL', 'postgresql+psycopg://fixture:' + secrets.token_hex(24) + '@unreachable.invalid/movement_test')
    for name in ('AI_REASONING_ENABLED', 'TRAINING_AI_ENABLED', 'TRAINING_VOICE_ENABLED'):
        monkeypatch.setenv(name, 'false')
    monkeypatch.setenv('WHATSAPP_ENABLED', str(whatsapp).lower())
    if whatsapp:
        monkeypatch.setenv('KAPSO_API_KEY', secrets.token_urlsafe(40))
        monkeypatch.setenv('KAPSO_WEBHOOK_SECRET', secrets.token_urlsafe(48))
        monkeypatch.setenv('KAPSO_PHONE_NUMBER_ID', 'synthetic-number-id')
        monkeypatch.setenv('WHATSAPP_ENCRYPTION_KEY', Fernet.generate_key().decode())
        monkeypatch.setenv('WHATSAPP_KEY_VERSION', '1')
        monkeypatch.setenv('WHATSAPP_ENCRYPTION_KEYS', '{}')
        monkeypatch.setenv('PHONE_HASH_KEY', base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())


@pytest.mark.parametrize('value', ['', 'local-development-change-me', 'replace-with-a-long-random-secret', 'a' * 64, 'short', 'demo-password-for-production-do-not-use'])
def test_production_rejects_session_secret(monkeypatch, value):
    production(monkeypatch)
    monkeypatch.setenv('SESSION_SECRET', value)
    with pytest.raises(SecurityConfigurationError, match='SESSION_SECRET'):
        validate_security()


@pytest.mark.parametrize('module', ['app.main', 'app.whatsapp.worker'])
def test_both_entrypoints_fail_before_database_and_do_not_print_values(monkeypatch, module):
    production(monkeypatch)
    marker = 'sensitive-value-short'
    monkeypatch.setenv('SESSION_SECRET', marker)
    result = subprocess.run([sys.executable, '-c', f'import {module}'], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'SESSION_SECRET' in result.stderr
    assert marker not in result.stdout + result.stderr
    assert os.environ['DATABASE_URL'] not in result.stdout + result.stderr
    assert 'OperationalError' not in result.stderr


@pytest.mark.parametrize('name', ['DATABASE_URL', 'OPENAI_API_KEY', 'KAPSO_API_KEY', 'KAPSO_WEBHOOK_SECRET', 'PHONE_HASH_KEY', 'WHATSAPP_ENCRYPTION_KEY'])
def test_production_missing_required_credentials(monkeypatch, name):
    production(monkeypatch, whatsapp=True)
    monkeypatch.setenv('TRAINING_AI_ENABLED', 'true')
    monkeypatch.setenv('OPENAI_API_KEY', secrets.token_urlsafe(40))
    monkeypatch.delenv(name, raising=False)
    with pytest.raises(SecurityConfigurationError):
        validate_security()


@pytest.mark.parametrize('name,value', [('APP_ENV', 'prod'), ('ENABLE_DEMO_SEED', 'true'), ('DEMO_PASSWORD', 'unused-but-forbidden'), ('WHATSAPP_ENABLED', 'yes'), ('DATABASE_URL', 'postgresql+psycopg://movement:movement@db/movement')])
def test_production_rejects_unsafe_configuration(monkeypatch, name, value):
    production(monkeypatch)
    monkeypatch.setenv(name, value)
    with pytest.raises(SecurityConfigurationError):
        validate_security()


def test_disabled_providers_do_not_require_keys(monkeypatch):
    production(monkeypatch)
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    validate_security()


@pytest.mark.parametrize('case', ['weak_lookup', 'weak_encryption', 'shared_key', 'invalid_ring', 'missing_current', 'weak_old_key'])
def test_production_rejects_unsafe_whatsapp_keys(monkeypatch, case):
    production(monkeypatch, whatsapp=True)
    zero = base64.urlsafe_b64encode(bytes(32)).decode()
    if case == 'weak_lookup':
        monkeypatch.setenv('PHONE_HASH_KEY', zero)
    elif case == 'weak_encryption':
        monkeypatch.setenv('WHATSAPP_ENCRYPTION_KEY', zero)
    elif case == 'shared_key':
        monkeypatch.setenv('PHONE_HASH_KEY', os.environ['WHATSAPP_ENCRYPTION_KEY'])
    elif case == 'invalid_ring':
        monkeypatch.setenv('WHATSAPP_ENCRYPTION_KEYS', '[1]')
    elif case == 'missing_current':
        monkeypatch.delenv('WHATSAPP_ENCRYPTION_KEY')
    else:
        monkeypatch.setenv('WHATSAPP_ENCRYPTION_KEYS', json.dumps({'old': zero}))
    with pytest.raises(SecurityConfigurationError):
        validate_security()


def test_web_and_worker_accept_same_configuration_and_historical_keys(monkeypatch):
    production(monkeypatch, whatsapp=True)
    old = Fernet.generate_key()
    monkeypatch.setenv('WHATSAPP_ENCRYPTION_KEYS', json.dumps({'old': old.decode()}))
    validate_security()
    web, worker = Vault(), Vault()
    encrypted = web.encrypt({'fixture': 'protected'})
    assert worker.decrypt(encrypted, web.version) == {'fixture': 'protected'}
    historic = Fernet(old).encrypt(json.dumps({'fixture': 'history'}).encode()).decode()
    assert worker.decrypt(historic, 'old') == {'fixture': 'history'}
    assert web.phone_hash('+56912345678') == worker.phone_hash('+56912345678')


def test_development_seed_requires_explicit_flag_and_password(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'development')
    monkeypatch.delenv('ENABLE_DEMO_SEED', raising=False)
    assert not demo_seed_enabled()
    monkeypatch.setenv('ENABLE_DEMO_SEED', 'true')
    monkeypatch.delenv('DEMO_PASSWORD', raising=False)
    with pytest.raises(SecurityConfigurationError, match='DEMO_PASSWORD'):
        demo_seed_enabled()
    monkeypatch.setenv('DEMO_PASSWORD', 'synthetic-development-password')
    assert demo_seed_enabled()


@pytest.mark.parametrize('mode', ['production', 'test'])
def test_seed_denied_outside_development(session, monkeypatch, mode):
    monkeypatch.setenv('APP_ENV', mode)
    monkeypatch.setenv('ENABLE_DEMO_SEED', 'true')
    with pytest.raises(SecurityConfigurationError):
        seed(session)


def test_seed_preserves_changed_demo_password_and_real_user(session, monkeypatch):
    user = session.get(User, DEMO_ATHLETE_ID)
    changed = hash_password('changed-credential-fixture')
    user.password_hash = changed
    user.is_active = False
    real = User(id=uuid4(), demo_key='synthetic-real-user', name='Fixture', role='ATHLETE', password_hash=hash_password('real-fixture-password'))
    session.add(real)
    session.commit()
    real_hash = real.password_hash
    monkeypatch.setenv('DEMO_PASSWORD', 'different-seed-password')
    for _ in range(2):
        seed(session)
        session.commit()
        session.expire_all()
        assert session.get(User, DEMO_ATHLETE_ID).password_hash == changed
        assert not session.get(User, DEMO_ATHLETE_ID).is_active
        assert session.get(User, real.id).password_hash == real_hash
    assert verify_password('real-fixture-password', real_hash)


def test_production_seed_does_not_create_missing_demo(session, monkeypatch):
    from app.models import Coach
    coach = session.scalar(select(Coach).join(User).where(User.demo_key == 'pablo'))
    user = session.get(User, coach.user_id)
    session.delete(coach)
    session.delete(user)
    session.commit()
    before = list(session.scalars(select(User.id)))
    production(monkeypatch)
    assert seed(session) is False
    session.commit()
    assert list(session.scalars(select(User.id))) == before


def test_start_script_rejects_security_before_running_database_commands(monkeypatch, tmp_path):
    production(monkeypatch)
    monkeypatch.setenv('SESSION_SECRET', '')
    result = subprocess.run(['sh', 'scripts/start-app.sh'], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Invalid security configuration: SESSION_SECRET' in result.stderr
    assert 'alembic' not in result.stdout + result.stderr


def test_startup_restarts_keep_credentials_and_production_creates_no_demos(session, monkeypatch, tmp_path):
    # Only the disposable DB from conftest is permitted; use real startup/seed/migrations,
    # replace just uvicorn with a no-op so startup can return twice.
    assert engine.url.database == 'movement_test'
    database_url = engine.url.render_as_string(hide_password=False)
    (tmp_path / 'uvicorn').write_text('#!/bin/sh\nexit 0\n')
    (tmp_path / 'uvicorn').chmod(0o700)
    monkeypatch.setenv('PATH', str(tmp_path) + os.pathsep + os.environ['PATH'])
    before = {u.id: u.password_hash for u in session.scalars(select(User))}
    for _ in range(2):
        result = subprocess.run(['sh', 'scripts/start-app.sh'], capture_output=True, text=True)
        assert result.returncode == 0, 'Development startup failed (details suppressed)'
        session.expire_all()
        assert {u.id: u.password_hash for u in session.scalars(select(User))} == before
    # This fixture database uses a deliberately weak local password. Change only its
    # disposable test role password, then restore it before leaving the test.
    password = secrets.token_hex(24)
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.exec_driver_sql("ALTER ROLE movement PASSWORD '" + password + "'")
    try:
        production(monkeypatch)
        monkeypatch.setenv('DATABASE_URL', database_url.replace(':movement@', ':' + password + '@'))
        for _ in range(2):
            result = subprocess.run(['sh', 'scripts/start-app.sh'], capture_output=True, text=True)
            assert result.returncode == 0, 'Production startup failed (details suppressed)'
            session.expire_all()
            assert {u.id: u.password_hash for u in session.scalars(select(User))} == before
    finally:
        with engine.begin() as conn:
            conn.exec_driver_sql("ALTER ROLE movement PASSWORD 'movement'")


def test_sql_parameters_are_hidden_and_app_logs_suppress_exception_body(client, session, monkeypatch, caplog):
    assert engine.hide_parameters
    from io import BytesIO
    from fastapi import UploadFile, HTTPException
    from sqlalchemy.exc import OperationalError
    sentinel = 'synthetic-sensitive-token-do-not-log'
    def broken(*args, **kwargs):
        raise OperationalError('query', {'password': sentinel}, RuntimeError(sentinel))
    monkeypatch.setattr(session, 'commit', broken)
    with pytest.raises(HTTPException) as exc:
        main._run_analysis(UploadFile(filename='fixture.mp4', file=BytesIO(b'fixture')), 'Sentadilla', 'Técnica', None, session)
    assert exc.value.status_code == 503
    assert 'Cannot create analysis' in caplog.text
    assert sentinel not in caplog.text
    source = Path('app/main.py').read_text()
    assert 'logger.exception(' not in source
    assert 'exc_info=True' not in source
    assert 'result.stderr[-300:]' not in source
    assert '--no-access-log' in Path('scripts/start-app.sh').read_text()


def test_production_rejects_legacy_demo_login_but_preserves_changed_account(client, session, monkeypatch):
    production(monkeypatch)
    assert client.post('/api/auth/login', json={'username': 'gaston', 'password': 'demo1234'}).status_code == 401
    user = session.get(User, DEMO_ATHLETE_ID)
    password = secrets.token_urlsafe(40)
    user.password_hash = hash_password(password)
    session.commit()
    before = user.password_hash
    assert client.post('/api/auth/login', json={'username': 'gaston', 'password': password}).status_code == 200
    assert session.get(User, DEMO_ATHLETE_ID).password_hash == before


@pytest.mark.parametrize('module', ['app.main', 'app.whatsapp.worker'])
def test_production_entrypoints_accept_valid_configuration_without_provider_calls(monkeypatch, module):
    production(monkeypatch, whatsapp=True)
    result = subprocess.run([sys.executable, '-c', f'import {module}'], capture_output=True, text=True)
    assert result.returncode == 0, 'Valid configuration rejected (details suppressed)'
    for name in ('SESSION_SECRET', 'KAPSO_API_KEY', 'KAPSO_WEBHOOK_SECRET', 'PHONE_HASH_KEY', 'WHATSAPP_ENCRYPTION_KEY'):
        assert os.environ[name] not in result.stdout + result.stderr


def test_worker_revalidates_before_any_processing(monkeypatch):
    from app.whatsapp import worker
    production(monkeypatch)
    monkeypatch.setenv('SESSION_SECRET', '')
    monkeypatch.setattr(worker, 'process_one', lambda *_: pytest.fail('Worker processed invalid configuration'))
    with pytest.raises(SecurityConfigurationError, match='SESSION_SECRET'):
        worker.run_once(provider=object(), vault=object())


def test_seed_requires_explicit_development_environment(monkeypatch):
    monkeypatch.delenv('APP_ENV', raising=False)
    monkeypatch.setenv('ENABLE_DEMO_SEED', 'true')
    with pytest.raises(SecurityConfigurationError, match='ENABLE_DEMO_SEED'):
        demo_seed_enabled()
