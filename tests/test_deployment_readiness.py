from app import main


def test_deployment_health_does_not_expose_database_details(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'ok': True}


def test_upload_over_configured_limit_is_rejected_before_persistence(client, monkeypatch, session):
    monkeypatch.setattr(main, 'MAX_UPLOAD_BYTES', 1)
    response = client.post(
        '/api/analyses',
        data={'exercise': 'Press', 'objective': 'Probar límite'},
        files={'file': ('video.mp4', b'too-large', 'video/mp4')},
    )
    assert response.status_code == 413
