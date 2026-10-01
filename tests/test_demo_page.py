def test_demo_page_exposes_the_short_demo_flow(client):
    response = client.get('/demo')
    assert response.status_code == 200
    for text in (
        'De video a feedback humano', 'Gastón Demo', 'Carlos', 'Anais', 'Pablo',
        'Nuevo análisis', 'Mis análisis', 'Bandeja coach', 'Feedback',
    ):
        assert text in response.text


def test_landing_exposes_commercial_coach_flow(client):
    response = client.get('/')
    assert response.status_code == 200
    for text in (
        'NUEVO', 'Análisis de levantamientos con IA', 'Feedback de técnica en minutos,',
        'no en horas.', 'Soy coach', 'Soy atleta', 'De video a progreso en 4 pasos',
        'Todo lo que necesitas para revisar mejor', 'Una herramienta, dos formas de usarla',
        'Empieza gratis. Crece cuando lo necesites.', 'Lo que suelen preguntar',
        'Convierte cada video en una oportunidad de coaching', 'Entrar a la demo', '/coach/reviews',
    ):
        assert text in response.text
