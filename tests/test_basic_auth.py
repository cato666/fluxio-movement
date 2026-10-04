def test_demo_login_sets_session_and_returns_role(client):
    response = client.post('/api/auth/login', json={'username': 'gaston', 'password': 'demo1234'})
    assert response.status_code == 200
    assert response.json()['role'] == 'ATHLETE'
    assert client.get('/api/auth/me').json()['name'] == 'Gastón Demo'


def test_athlete_login_defaults_to_training(client):
    response = client.post('/api/auth/login', json={'username': 'gaston', 'password': 'demo1234'})
    assert response.status_code == 200
    assert response.json()['next'] == '/training'


def test_login_rejects_invalid_password(client):
    assert client.post('/api/auth/login', json={'username': 'carlos', 'password': 'incorrecta'}).status_code == 401


def test_logout_clears_session(client):
    client.post('/api/auth/login', json={'username': 'carlos', 'password': 'demo1234'})
    assert client.post('/api/auth/logout').json() == {'ok': True}
    assert client.get('/api/auth/me').status_code == 401


def test_protected_routes_redirect_or_reject_without_session(client):
    assert client.get('/analyses', follow_redirects=False).status_code == 303
    assert client.get('/api/analyses').status_code == 401
    assert client.get('/uploads/not-owned.mp4').status_code == 401


def test_public_shell_hides_authenticated_navigation_by_default(client):
    html = client.get('/').text
    assert 'class="functional-nav" aria-label="Navegación de la aplicación" hidden' in html
    assert 'class="functional-actions" hidden' in html


def test_role_boundaries_and_coach_identity_are_enforced(client):
    client.post('/api/auth/login', json={'username': 'gaston', 'password': 'demo1234'})
    athlete_redirect = client.get('/coach/reviews', follow_redirects=False)
    assert athlete_redirect.status_code == 303 and athlete_redirect.headers['location'] == '/analyses'
    assert client.get('/api/coach/reviews').status_code == 403
    client.post('/api/auth/logout')
    logged = client.post('/api/auth/login', json={'username': 'carlos', 'password': 'demo1234'}).json()
    redirect = client.get('/analyses', follow_redirects=False)
    assert redirect.status_code == 303 and redirect.headers['location'] == '/coach/reviews'
    assert client.get('/api/coach/reviews?coach_id=00000000-0000-4000-8000-000000000003').status_code == 403
    assert client.get(f"/api/coach/reviews?coach_id={logged['id']}").status_code == 200


def test_system_admin_can_access_usage_but_not_athlete_api(client):
    response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'demo1234'})
    assert response.json()['next'] == '/internal/usage'
    assert client.get('/api/internal/ai-usage').status_code == 200
    assert client.get('/api/analyses').status_code == 403


def test_coach_can_upload_for_an_athlete_and_gets_assigned_review(client, session, monkeypatch):
    from app import main
    from app.models import Analysis, CoachReview
    client.post('/api/auth/login', json={'username': 'carlos', 'password': 'demo1234'})
    monkeypatch.setattr(main, '_process_analysis', lambda *_: None)
    athlete = client.get('/api/coach/athletes').json()['items'][0]
    response = client.post('/api/coach/analyses', data={
        'athlete_id': athlete['id'], 'exercise': 'Sentadilla', 'objective': 'Revisar profundidad', 'view': 'side',
    }, files={'file': ('alumno.mp4', b'video', 'video/mp4')})
    assert response.status_code == 202, response.text
    payload = response.json()
    analysis = session.get(Analysis, payload['id'])
    review = session.get(CoachReview, payload['review_id'])
    assert analysis.athlete_id == __import__('uuid').UUID(athlete['id'])
    assert review.coach_id == __import__('uuid').UUID('00000000-0000-4000-8000-000000000002')


def test_coach_registers_athlete_who_can_log_in(client):
    client.post('/api/auth/login', json={'username': 'carlos', 'password': 'demo1234'})
    created = client.post('/api/coach/athletes', json={
        'name': 'María Pérez', 'username': 'maria.perez', 'password': 'movimiento123',
    })
    assert created.status_code == 201, created.text
    assert created.json()['name'] == 'María Pérez'
    assert client.post('/api/coach/athletes', json={
        'name': 'Otra María', 'username': 'maria.perez', 'password': 'movimiento123',
    }).status_code == 409
    client.post('/api/auth/logout')
    assert client.post('/api/auth/login', json={'username': 'maria.perez', 'password': 'movimiento123'}).json()['role'] == 'ATHLETE'


def test_athlete_can_only_list_and_read_own_analyses(client, session):
    from uuid import UUID

    from app.models import Analysis
    from app.seed import DEMO_ATHLETE_ID

    client.post('/api/auth/login', json={'username': 'carlos', 'password': 'demo1234'})
    registered = client.post('/api/coach/athletes', json={
        'name': 'Max Aislamiento', 'username': 'max.isolation', 'password': 'movimiento123',
    })
    assert registered.status_code == 201, registered.text
    max_id = UUID(registered.json()['id'])
    session.add_all([
        Analysis(id='gaston-private', athlete_id=DEMO_ATHLETE_ID, status='PROCESSING', exercise='Sentadilla', view='side', objective='Técnica', original_filename='gaston.mp4', video_path='uploads/gaston.mp4'),
        Analysis(id='max-private', athlete_id=max_id, status='PROCESSING', exercise='Press', view='front', objective='Técnica', original_filename='max.mp4', video_path='uploads/max.mp4'),
    ])
    session.commit()

    client.post('/api/auth/logout')
    assert client.post('/api/auth/login', json={'username': 'max.isolation', 'password': 'movimiento123'}).status_code == 200
    listed = client.get('/api/analyses')
    assert listed.status_code == 200
    assert [item['id'] for item in listed.json()['items']] == ['max-private']
    assert client.get('/api/analyses/max-private').status_code == 200
    assert client.get('/api/analyses/gaston-private').status_code == 404
