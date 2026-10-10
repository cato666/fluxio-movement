from app.models import User, PlanInteraction
from app.seed import DEMO_ATHLETE_ID
from sqlalchemy import select, func


def admin(client):
    assert client.post('/api/auth/login', json={'username': 'admin', 'password': 'demo1234'}).status_code == 200
    return client


def test_permissions(athlete_client):
    assert athlete_client.get('/api/admin/users').status_code == 403
    assert athlete_client.get('/api/account/plan').json()['plan'] == 'FREE'


def test_create_update_audit(client):
    admin(client)
    payload = dict(name='Nueva atleta', username='nueva', email='nueva@example.com', role='ATHLETE', password='password123', plan='PAID')
    response = client.post('/api/admin/users', json=payload)
    assert response.status_code == 201, response.text
    identifier = response.json()['id']
    payload.update(is_active=False, password=None)
    assert client.put(f'/api/admin/users/{identifier}', json=payload).status_code == 200
    items = client.get('/api/admin/audit').json()['items']
    assert len(items) == 2
    assert 'password123' not in str(items)
    client.post('/api/auth/logout')
    assert client.post('/api/auth/login', json={'username': 'nueva', 'password': 'password123'}).status_code == 401


def test_last_admin(client):
    admin(client)
    user = next(row for row in client.get('/api/admin/users').json()['items'] if row['role'] == 'SYSTEM_ADMIN')
    payload = {key: user[key] for key in ('name', 'username', 'email', 'role', 'plan')}
    payload['is_active'] = False
    assert client.put('/api/admin/users/' + user['id'], json=payload).status_code == 409


def test_quota_and_feature_gate(client, session):
    admin(client)
    policies = {'FREE': {'monthly_limit': 1, 'enabled_operations': ['INTERPRET']}, 'PAID': {'monthly_limit': 200, 'enabled_operations': ['ANALYZE', 'INTERPRET', 'TRANSCRIBE']}}
    assert client.put('/api/admin/plans', json=policies).status_code == 200
    client.post('/api/auth/login', json={'username': 'gaston', 'password': 'demo1234'})
    assert client.post('/api/analyze', files={'file': ('clip.mp4', b'fake', 'video/mp4')}).status_code == 403
    from app.administration import consume
    consume(session, DEMO_ATHLETE_ID, 'INTERPRET')
    assert client.get('/api/account/plan').json()['remaining'] == 0
    response = client.post('/api/training-sessions/interpret', json={'text': '3 rounds: 10 squats'})
    assert response.status_code == 429, response.text
    assert session.scalar(select(func.count()).select_from(PlanInteraction)) == 1


def test_deactivation_revokes_existing_session(athlete_client, session):
    user = session.get(User, DEMO_ATHLETE_ID)
    user.is_active = False
    session.commit()
    assert athlete_client.get('/api/auth/me').status_code == 401


def test_previous_month_does_not_consume_quota(athlete_client, session):
    from datetime import datetime, timezone, timedelta
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    session.add(PlanInteraction(user_id=DEMO_ATHLETE_ID, operation='ANALYZE', created_at=month_start - timedelta(seconds=1)))
    session.commit()
    assert athlete_client.get('/api/account/plan').json()['used'] == 0


def test_plan_change_preserves_consumption(client, session):
    from app.administration import consume
    consume(session, DEMO_ATHLETE_ID, 'ANALYZE')
    admin(client)
    user = next(row for row in client.get('/api/admin/users').json()['items'] if row['id'] == str(DEMO_ATHLETE_ID))
    payload = {key: user[key] for key in ('name', 'username', 'email', 'role', 'is_active')}
    payload['plan'] = 'PAID'
    assert client.put('/api/admin/users/' + user['id'], json=payload).status_code == 200
    client.post('/api/auth/login', json={'username': 'gaston', 'password': 'demo1234'})
    usage = client.get('/api/account/plan').json()
    assert usage['used'] == 1 and usage['remaining'] == 199


def test_parallel_requests_cannot_exceed_quota(session):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from fastapi import HTTPException
    from app.database import SessionLocal
    from app.models import AdminSetting
    from app.administration import consume
    session.add(AdminSetting(key='plans', value={
        'FREE': {'monthly_limit': 1, 'enabled_operations': ['ANALYZE']},
        'PAID': {'monthly_limit': 200, 'enabled_operations': ['ANALYZE']}}))
    session.commit()
    barrier = Barrier(2)
    def reserve(_):
        with SessionLocal() as worker:
            barrier.wait(timeout=10)
            try:
                consume(worker, DEMO_ATHLETE_ID, 'ANALYZE')
                return 200
            except HTTPException as error:
                return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(reserve, range(2))) == [200, 429]
    assert session.scalar(select(func.count()).select_from(PlanInteraction)) == 1
