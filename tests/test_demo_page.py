def test_demo_page_exposes_the_short_demo_flow(client):
    response = client.get('/demo')
    assert response.status_code == 200
    for text in (
        'De video a feedback humano', 'Gastón Demo', 'Carlos', 'Andrea', 'Pablo',
        'Nuevo análisis', 'Mis análisis', 'Bandeja coach', 'Feedback',
    ):
        assert text in response.text


def test_landing_exposes_commercial_coach_flow(client):
    response = client.get('/')
    assert response.status_code == 200
    for text in (
        'TU MIRADA EXPERTA, POTENCIADA POR IA', 'Revisa más atletas.', 'En menos tiempo.',
        'Video + IA + tu criterio profesional para entregar feedback más claro, más rápido y más útil.',
        'Ver demo coach', 'Probar gratis', 'Cómo funciona', 'Beneficios para coaches',
        'Convierte cada video en una oportunidad de coaching', 'Entrar al MVP', '/coach/reviews',
    ):
        assert text in response.text
