"""S07: real disposable PostgreSQL admission, ASGI origins and trusted proxy semantics."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app import main
from app.database import SessionLocal
from app.models import AdminSetting, User
from app.seed import DEMO_ATHLETE_ID
from app.security_config import SecurityConfigurationError
from app.services import auth, login_security
from app.web_security import WebSecurityMiddleware, validate_web_security
from tests.whatsapp_helpers import configure, payload, webhook


@pytest.fixture(autouse=True)
def bounded_policy(monkeypatch):
    monkeypatch.setenv('LOGIN_WINDOW_SECONDS', '300')
    monkeypatch.setenv('LOGIN_ACCOUNT_LIMIT', '5')
    monkeypatch.setenv('LOGIN_PEER_LIMIT', '20')
    monkeypatch.setenv('WEB_ALLOWED_ORIGINS', 'http://testserver,https://pilot.invalid')
    monkeypatch.setattr(login_security, '_clock', lambda session: 1800000100)


def attempt(client, username='gaston', password='wrong', **kwargs):
    return client.post('/api/auth/login', json={'username': username, 'password': password}, **kwargs)


def test_login_correct_wrong_absent_and_inactive_use_same_scrypt_work(client, session, monkeypatch):
    original = auth.hash_password
    calls = []
    def spy(password, salt=None):
        calls.append(1)
        return original(password, salt)
    monkeypatch.setattr(auth, 'hash_password', spy)
    assert attempt(client, password='demo1234').status_code == 200
    wrong = attempt(client)
    absent = attempt(client, username='does-not-exist')
    user = session.get(User, DEMO_ATHLETE_ID)
    user.is_active = False
    session.commit()
    inactive = attempt(client, password='demo1234')
    assert [wrong.status_code, absent.status_code, inactive.status_code] == [401, 401, 401]
    assert wrong.json() == absent.json() == inactive.json() == {'detail': 'Credenciales inválidas'}
    assert calls == [1, 1, 1, 1]
    assert client.get('/api/auth/me').status_code == 401


def test_corrupt_credential_still_performs_scrypt(client, session, monkeypatch):
    user = session.get(User, DEMO_ATHLETE_ID)
    user.password_hash = 'malformed'
    session.commit()
    original = auth.hash_password
    calls = []
    monkeypatch.setattr(auth, 'hash_password', lambda *args: calls.append(1) or original(*args))
    assert attempt(client).status_code == 401
    assert calls == [1]


@pytest.mark.parametrize('username', ['gaston', 'does-not-exist'])
def test_uniform_rate_limit_and_window_recovery(client, monkeypatch, username):
    for _ in range(5):
        assert attempt(client, username).status_code == 401
    response = attempt(client, username)
    assert response.status_code == 429
    assert response.headers['retry-after'] == '200'
    assert not any('remaining' in header for header in response.headers)
    monkeypatch.setattr(login_security, '_clock', lambda session: 1800000300)
    assert attempt(client, username).status_code == 401


def test_success_is_counted_and_accounts_are_independent(client):
    for _ in range(5):
        assert attempt(client, password='demo1234').status_code == 200
    assert attempt(client, password='demo1234').status_code == 429
    assert attempt(client, 'carlos', 'demo1234').status_code == 200


def test_peer_limit_includes_invalid_payload_and_ignores_forged_forwarded(client, monkeypatch):
    monkeypatch.setenv('LOGIN_PEER_LIMIT', '2')
    assert client.post('/api/auth/login', content='invalid', headers={'content-type': 'application/json'}).status_code == 422
    assert attempt(client, 'unknown1', headers={'X-Forwarded-For': '203.0.113.2'}).status_code == 401
    assert attempt(client, 'unknown2', headers={'X-Forwarded-For': '203.0.113.3'}).status_code == 429


@pytest.mark.parametrize('kind', ['account', 'peer'])
def test_concurrent_admission_cannot_exceed_last_slot(kind, monkeypatch):
    monkeypatch.setenv('LOGIN_ACCOUNT_LIMIT', '1')
    monkeypatch.setenv('LOGIN_PEER_LIMIT', '1')
    def submit(_):
        try:
            login_security.admit(kind, 'synthetic-shared-identifier')
            return 200
        except HTTPException as exc:
            return exc.status_code
    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(submit, range(8)))
    assert outcomes.count(200) == 1 and outcomes.count(429) == 7
    # A new connection/worker sees the committed reservation.
    with pytest.raises(HTTPException) as exc:
        login_security.admit(kind, 'synthetic-shared-identifier')
    assert exc.value.status_code == 429


def test_bounded_storage_contains_only_hmac_and_counters_and_safe_logs(client, caplog, monkeypatch):
    monkeypatch.setenv('LOGIN_ACCOUNT_LIMIT', '1')
    secret = 'sensitive-password-marker'
    for _ in range(2):
        attempt(client, 'personal-username-marker', secret)
    with SessionLocal() as session:
        state = session.get(AdminSetting, login_security.KEY).value
        encoded = json.dumps(state)
    assert 'personal-username-marker' not in encoded and secret not in encoded
    assert all(len(key) == 64 for key in state['buckets'])
    assert 'security_rejection reason=login_rate_limit' in caplog.text
    assert secret not in caplog.text and 'personal-username-marker' not in caplog.text
    assert 'cookie' not in caplog.text.lower()


def test_storage_capacity_fails_closed_then_expires(monkeypatch):
    monkeypatch.setattr(login_security, 'MAX_BUCKETS', 1)
    login_security.admit('account', 'first')
    with pytest.raises(HTTPException):
        login_security.admit('account', 'second')
    monkeypatch.setattr(login_security, '_clock', lambda session: 1800000300)
    login_security.admit('account', 'second')


def test_database_failure_is_closed_without_exception_payload(client, monkeypatch, caplog):
    from sqlalchemy.exc import OperationalError
    def broken(*args):
        raise OperationalError('secret-sql', {'password': 'sensitive-marker'}, RuntimeError('sensitive-marker'))
    monkeypatch.setattr(login_security, 'admit', broken)
    response = attempt(client)
    assert response.status_code == 503
    assert 'sensitive-marker' not in response.text + caplog.text


@pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH', 'DELETE'])
@pytest.mark.parametrize('origin,status', [('http://testserver', 200), ('https://attacker.invalid', 403), ('null', 403), ('http://testserver/path', 403), ('http://testserver,https://attacker.invalid', 403)])
def test_all_mutating_methods_have_origin_guard(method, origin, status, monkeypatch):
    async def operation(request):
        return JSONResponse({'ok': True})
    application = Starlette(routes=[Route('/operation', operation, methods=['POST', 'PUT', 'PATCH', 'DELETE'])])
    application.add_middleware(WebSecurityMiddleware)
    with TestClient(application) as client:
        assert client.request(method, '/operation', headers={'Origin': origin}).status_code == status


def test_missing_origin_policy_and_cross_site_metadata(client, monkeypatch):
    assert attempt(client).status_code == 401  # explicit local non-browser policy
    assert attempt(client, headers={'Sec-Fetch-Site': 'same-origin'}).status_code == 403
    assert attempt(client, headers={'Origin': 'http://testserver', 'Sec-Fetch-Site': 'cross-site'}).status_code == 403
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('WEB_ALLOWED_ORIGINS', 'https://pilot.invalid')
    client.base_url = 'https://pilot.invalid'
    assert attempt(client).status_code == 403


def test_admin_and_sharing_are_covered_and_logout_clears_session(client):
    assert attempt(client, 'admin', 'demo1234', headers={'Origin': 'http://testserver'}).status_code == 200
    for method, path in [('PUT', '/api/admin/plans'), ('POST', '/api/admin/users'), ('POST', '/api/training-week/shares'), ('DELETE', '/api/training-week/shares'), ('POST', '/api/auth/logout')]:
        assert client.request(method, path, json={}, headers={'Origin': 'https://attacker.invalid'}).status_code == 403
    assert client.get('/api/auth/me').status_code == 200
    assert client.post('/api/auth/logout', headers={'Origin': 'http://testserver'}).status_code == 200
    assert client.get('/api/auth/me').status_code == 401


def test_production_origin_requires_https_scope_ignores_forged_headers(client, monkeypatch):
    assert attempt(client, password='demo1234').status_code == 200
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('WEB_ALLOWED_ORIGINS', 'https://pilot.invalid')
    assert client.post('/api/auth/logout', headers={'Origin': 'https://pilot.invalid', 'X-Forwarded-Proto': 'https', 'X-Forwarded-Host': 'pilot.invalid'}).status_code == 403
    saved_cookie = client.cookies.get('session')
    client.base_url = 'https://pilot.invalid'
    client.cookies.set('session', saved_cookie, domain='pilot.invalid', path='/')
    assert client.post('/api/auth/logout', headers={'Origin': 'https://pilot.invalid'}).status_code == 200


@pytest.mark.parametrize('trusted,peer,expected', [(['10.20.0.0/24'], '10.20.0.8', 200), (['10.20.0.0/24'], '10.21.0.8', 403), ([], '10.20.0.8', 403)])
def test_real_uvicorn_proxy_middleware_and_origin_policy(trusted, peer, expected, monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('WEB_ALLOWED_ORIGINS', 'https://pilot.invalid')
    async def operation(request):
        return JSONResponse({'scheme': request.url.scheme, 'peer': request.client.host})
    application = Starlette(routes=[Route('/operation', operation, methods=['POST'])])
    application.add_middleware(WebSecurityMiddleware)
    application = ProxyHeadersMiddleware(application, trusted_hosts=trusted)
    with TestClient(application, client=(peer, 1234)) as client:
        response = client.post('/operation', headers={'Origin': 'https://pilot.invalid', 'X-Forwarded-Proto': 'https', 'X-Forwarded-For': '203.0.113.8', 'X-Forwarded-Host': 'attacker.invalid'})
    assert response.status_code == expected
    if expected == 200:
        assert response.json() == {'scheme': 'https', 'peer': '203.0.113.8'}


@pytest.mark.parametrize('secure', [False, True])
def test_cookie_flags_and_script_proxy_configuration(secure):
    async def operation(request):
        request.session.clear()
        request.session['user_id'] = 'synthetic'
        return JSONResponse({'ok': True})
    application = Starlette(routes=[Route('/', operation)])
    application.add_middleware(SessionMiddleware, secret_key='synthetic-test-only', https_only=secure, same_site='lax')
    with TestClient(application, base_url='https://pilot.invalid') as client:
        cookie = client.get('/').headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'samesite=lax' in cookie
    assert ('; secure' in cookie) == secure
    source = Path('app/main.py').read_text()
    assert "https_only=environment() == 'production'" in source
    assert '--forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-}"' in Path('scripts/start-app.sh').read_text()


@pytest.mark.parametrize('name,value', [('WEB_ALLOWED_ORIGINS', ''), ('WEB_ALLOWED_ORIGINS', 'http://pilot.invalid'), ('WEB_ALLOWED_ORIGINS', 'https://pilot.invalid/path'), ('FORWARDED_ALLOW_IPS', '*'), ('FORWARDED_ALLOW_IPS', '0.0.0.0/0'), ('FORWARDED_ALLOW_IPS', '::/0'), ('FORWARDED_ALLOW_IPS', 'host-name'), ('LOGIN_ACCOUNT_LIMIT', '0'), ('LOGIN_PEER_LIMIT', 'no'), ('LOGIN_WINDOW_SECONDS', '999999')])
def test_production_invalid_policy_fails_closed(monkeypatch, name, value):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('WEB_ALLOWED_ORIGINS', 'https://pilot.invalid')
    monkeypatch.setenv('FORWARDED_ALLOW_IPS', '10.20.0.0/24')
    monkeypatch.setenv(name, value)
    with pytest.raises(SecurityConfigurationError, match=name):
        validate_web_security()


def test_production_requires_explicit_proxy_policy(monkeypatch):
    monkeypatch.setenv('APP_ENV', 'production')
    monkeypatch.setenv('WEB_ALLOWED_ORIGINS', 'https://pilot.invalid')
    monkeypatch.delenv('FORWARDED_ALLOW_IPS', raising=False)
    with pytest.raises(SecurityConfigurationError, match='FORWARDED_ALLOW_IPS'):
        validate_web_security()
    monkeypatch.setenv('FORWARDED_ALLOW_IPS', '')
    validate_web_security()  # direct HTTPS, no trusted proxy


def test_signed_webhook_is_exempt_but_invalid_signature_still_denied(client, monkeypatch):
    configure(monkeypatch)
    client.headers['Origin'] = 'https://attacker.invalid'
    assert webhook(client, payload()).status_code == 200
    assert webhook(client, payload(), signature='0' * 64).status_code == 401
    # Exemption is exact, never inherited by related endpoints or arbitrary methods.
    assert client.post('/webhooks/whatsapp/kapso/extra').status_code == 403
    assert client.post('/api/whatsapp/link-challenges').status_code == 403


def test_actual_production_application_emits_secure_cookie_without_database_startup(monkeypatch):
    import subprocess
    import sys
    from tests.test_security_configuration import production
    production(monkeypatch)
    code = """
from fastapi import Request
from fastapi.testclient import TestClient
from app import main
@main.app.get('/api/auth/login')
def fixture(request: Request):
    request.session['user_id'] = 'synthetic-only'
    return {'ok': True}
# No lifespan/DB startup; synthetic route exists only in this child process.
client = TestClient(main.app, base_url='https://pilot.invalid')
cookie = client.get('/api/auth/login').headers['set-cookie'].lower()
assert 'httponly' in cookie and 'samesite=lax' in cookie and '; secure' in cookie
print('production-cookie-flags=PASS')
"""
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert result.returncode == 0, 'Production cookie validation failed (details suppressed)'
    assert result.stdout.strip() == 'production-cookie-flags=PASS'


def test_cli_invalid_origin_fails_cleanly_before_database_without_values(monkeypatch):
    import subprocess
    import sys
    from tests.test_security_configuration import production
    production(monkeypatch)
    monkeypatch.setenv('WEB_ALLOWED_ORIGINS', 'https://sensitive-origin-marker.invalid/path')
    result = subprocess.run([sys.executable, '-m', 'app.security_config'], capture_output=True, text=True)
    assert result.returncode != 0
    assert 'WEB_ALLOWED_ORIGINS' in result.stderr
    assert 'sensitive-origin-marker' not in result.stderr + result.stdout
    assert 'Traceback' not in result.stderr


def test_duplicate_origin_headers_rejected(client):
    assert attempt(client, headers=[('Origin', 'http://testserver'), ('Origin', 'https://attacker.invalid')]).status_code == 403


def test_concurrent_http_attempts_share_final_account_slot(client, monkeypatch):
    for _ in range(4):
        assert attempt(client).status_code == 401
    verified = []
    original = main.verify_password
    monkeypatch.setattr(main, 'verify_password', lambda *args: verified.append(1) or original(*args))
    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(lambda _: attempt(client).status_code, range(8)))
    assert statuses.count(401) == 1 and statuses.count(429) == 7
    assert verified == [1]


def test_expired_and_tampered_session_cannot_mutate(client):
    import base64
    from itsdangerous import TimestampSigner
    from unittest.mock import patch
    assert attempt(client, password='demo1234').status_code == 200
    cookie = client.cookies.get('session')
    client.cookies.clear()
    client.cookies.set('session', cookie + 'tampered')
    assert client.post('/api/auth/logout', headers={'Origin': 'http://testserver'}).status_code == 401
    payload = base64.b64encode(json.dumps({'user_id': str(DEMO_ATHLETE_ID)}).encode())
    with patch.object(TimestampSigner, 'get_timestamp', return_value=1):
        expired = TimestampSigner(main.SESSION_SECRET).sign(payload).decode()
    client.cookies.clear()
    client.cookies.set('session', expired)
    assert client.post('/api/auth/logout', headers={'Origin': 'http://testserver'}).status_code == 401


def test_session_login_discards_previous_session_fields(client):
    import base64
    from itsdangerous import TimestampSigner
    payload = base64.b64encode(json.dumps({'user_id': str(DEMO_ATHLETE_ID), 'unexpected_field': 'fixture'}).encode())
    cookie = TimestampSigner(main.SESSION_SECRET).sign(payload).decode()
    client.cookies.set('session', cookie, domain='testserver.local', path='/')
    response = attempt(client, 'carlos', 'demo1234')
    decoded = TimestampSigner(main.SESSION_SECRET).unsign(response.cookies['session'])
    assert set(json.loads(base64.b64decode(decoded))) == {'user_id'}


def test_authentication_responses_are_not_cacheable(client):
    assert attempt(client).headers['cache-control'] == 'no-store'
    assert attempt(client, password='demo1234').headers['cache-control'] == 'no-store'
    assert client.get('/api/auth/me').headers['cache-control'] == 'no-store'
    assert client.post('/api/auth/logout').headers['cache-control'] == 'no-store'
    assert attempt(client, headers={'Origin': 'https://attacker.invalid'}).headers['cache-control'] == 'no-store'


def test_production_allowed_origin_preserves_admin_and_explicit_share_flow(client, session, monkeypatch):
    from sqlalchemy import select
    from tests.share_helpers import consent_payload
    from tests.test_security_configuration import production
    password = 'synthetic-non-demo-credential'
    for user in session.scalars(select(User).where(User.demo_key.in_(['admin', 'gaston']))):
        user.password_hash = auth.hash_password(password)
    session.commit()
    production(monkeypatch)
    client.base_url = 'https://pilot.invalid'
    client.headers['Origin'] = 'https://pilot.invalid'
    assert attempt(client, 'admin', password).status_code == 200
    assert client.put('/api/admin/organization', json={'name': 'Disposable pilot fixture', 'contact_email': ''}).status_code == 200
    assert client.get('/api/admin/settings').json()['organization']['name'] == 'Disposable pilot fixture'
    assert client.post('/api/auth/logout').status_code == 200
    assert attempt(client, 'gaston', password).status_code == 200
    assert client.post('/api/training-sessions', json={'trained_on': '2026-10-11', 'title': 'Fixture', 'workout': 'Manual'}).status_code == 201
    assert client.post('/api/training-week/shares', json={'day': '2026-10-11'}).status_code == 422
    consent = consent_payload('2026-10-11')
    share = client.post('/api/training-week/shares', json=consent)
    assert share.status_code == 201
    data = share.json()
    replay = client.post('/api/training-week/shares', json=consent)
    assert replay.status_code == 201 and replay.json()['already_created'] is True
    assert client.get(data['path']).status_code == 200
    assert client.delete('/api/training-week/shares/' + data['id']).status_code == 200
    assert client.get(data['path']).status_code == 404


def test_clock_regression_does_not_reset_current_admission_window(monkeypatch):
    monkeypatch.setenv('LOGIN_ACCOUNT_LIMIT', '1')
    login_security.admit('account', 'same-login')
    monkeypatch.setattr(login_security, '_clock', lambda session: 1799999800)
    with pytest.raises(HTTPException) as exc:
        login_security.admit('account', 'same-login')
    assert exc.value.status_code == 429
    monkeypatch.setattr(login_security, '_clock', lambda session: 1800000300)
    login_security.admit('account', 'same-login')
