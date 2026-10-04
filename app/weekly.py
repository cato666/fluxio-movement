"""Authenticated weekly controls and a public live week reader."""
from datetime import date
from html import escape
import re
from uuid import UUID
from fastapi import APIRouter, Depends, Response
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from .database import get_session
from .models import User
from .services.weekly_summary import WeeklySummaryService, read_share, share_record
from .training import http_errors

PRIVATE_HEADERS = {'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow',
    'Referrer-Policy': 'no-referrer'}


class SharePayload(BaseModel):
    day: date | None = None


def router(require_athlete):
    routes = APIRouter()

    @routes.get('/api/training-week')
    def summary(response: Response, day: date | None = None,
                user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        response.headers.update(PRIVATE_HEADERS)
        return WeeklySummaryService(session, user.id).summary(day)

    @routes.get('/api/training-week/shares')
    def shares(response: Response, day: date | None = None,
               user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        response.headers.update(PRIVATE_HEADERS)
        return {'items': WeeklySummaryService(session, user.id).list_shares(day)}

    @routes.post('/api/training-week/shares', status_code=201)
    def create(payload: SharePayload, response: Response,
               user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        response.headers.update(PRIVATE_HEADERS)
        return WeeklySummaryService(session, user.id).create_share(payload.day)

    @routes.delete('/api/training-week/shares/{identifier}')
    def revoke(identifier: UUID, response: Response,
               user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        response.headers.update(PRIVATE_HEADERS)
        with http_errors():
            WeeklySummaryService(session, user.id).revoke(identifier)
        return {'ok': True}

    @routes.delete('/api/training-week/shares')
    def revoke_week(response: Response, day: date | None = None,
                    user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        response.headers.update(PRIVATE_HEADERS)
        WeeklySummaryService(session, user.id).revoke_week(day)
        return {'ok': True}

    @routes.get('/shared/week/{token}', response_class=HTMLResponse)
    def shared(token: str, session: Session = Depends(get_session)):
        from .services.training_errors import TrainingNotFound
        headers = PRIVATE_HEADERS | {'Content-Security-Policy':
            "default-src 'none'; style-src 'self'; font-src 'self'; img-src 'self'; base-uri 'none'; frame-ancestors 'none'"}
        try:
            data = read_share(session, token)
        except TrainingNotFound as error:
            return HTMLResponse(page(f'<h1>Enlace no disponible</h1><p>{escape(str(error))}</p>'),
                status_code=404, headers=headers)
        return HTMLResponse(page(recap(data, token)), headers=headers)

    @routes.get('/shared/week/{token}/images/{identifier}')
    def shared_image(token: str, identifier: UUID, session: Session = Depends(get_session)):
        from .services.training_service import TrainingService
        from .services.training_errors import TrainingNotFound
        try:
            row = share_record(session, token)
            data = WeeklySummaryService(session, row.athlete_id).summary(row.week_start)
            if not any(item.get('source_image_id') == str(identifier) for item in data['items']):
                raise TrainingNotFound('Foto no disponible en esta semana')
            path = TrainingService(session, row.athlete_id).image_path(identifier)
        except TrainingNotFound as error:
            return JSONResponse({'detail': str(error)}, status_code=404, headers=PRIVATE_HEADERS)
        return FileResponse(path, media_type='image/jpeg', headers=PRIVATE_HEADERS |
            {'X-Content-Type-Options': 'nosniff'})

    return routes


def readable_date(value):
    months = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
              'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')
    day = date.fromisoformat(value)
    return f'{day.day} de {months[day.month - 1]} de {day.year}'


def recap(data, token):
    """Present only the authorized week's current fields."""
    sessions, days = data['session_count'], data['active_days']
    items = sorted(data['items'], key=lambda item: item['trained_on'], reverse=True)
    featured = next((item for item in items if item.get('source_image_id')), None)
    parts = ['<div class="recap-brand">Fluxio <span>Movement</span></div><div class="recap-opening"><header class="recap-hero"><h1>Tu semana en movimiento</h1>',
        f'<p class="recap-dates">{readable_date(data["week_start"])} — {readable_date(data["week_end"])}</p>',
        '<dl class="recap-metrics">',
        f'<div><dt>{"Entrenamiento" if sessions == 1 else "Entrenamientos"}</dt><dd>{sessions}</dd></div>',
        f'<div><dt>{"Día activo" if days == 1 else "Días activos"}</dt><dd>{days}</dd></div>']
    if data['average_rpe'] is not None:
        parts.append(f'<div><dt>Esfuerzo promedio</dt><dd>{data["average_rpe"]}<span>/10</span></dd></div>')
    parts.append('</dl>')
    if data['average_rpe'] is not None:
        parts.append(f'<p class="recap-sample">{data["rpe_count"]} registros con esfuerzo</p>')
    parts.append('</header>')
    if featured:
        parts.append(f'<figure class="recap-feature"><a href="/shared/week/{token}/images/{featured["source_image_id"]}" aria-label="Ver foto del entrenamiento completa"><img class="weekly-photo" src="/shared/week/{token}/images/{featured["source_image_id"]}" alt="Foto del entrenamiento" fetchpriority="high"></a><figcaption><span>La sesión más reciente con foto · {readable_date(featured["trained_on"])}</span><strong>{escape(featured["title"])}</strong></figcaption></figure>')
    parts.append('</div>')
    if items:
        highlights = [('Última sesión', items[0]['title'], items[0]['result_text'] or 'Resultado sin registrar')]
        efforts = [item for item in items if item['rpe'] is not None]
        if efforts:
            hardest = max(efforts, key=lambda item: item['rpe'])
            highlights.append(('Mayor esfuerzo registrado', hardest['title'], f'{hardest["rpe"]}/10 · esfuerzo percibido'))
        noted = next((item for item in items if item['adaptations']), None)
        if noted:
            highlights.append(('Una nota de tu semana', noted['title'], noted['adaptations']))
        parts.append('<section class="recap-highlights"><h2>Tu semana, en pocas palabras</h2><div class="recap-highlight-grid">')
        for label, title, value in highlights:
            parts.append(f'<article><p class="recap-highlight-label">{label}</p><h3>{escape(title)}</h3><p>{escape(value)}</p></article>')
        parts.append('</div></section>')
    parts.append('<section class="recap-timeline" aria-label="Entrenamientos de la semana"><h2 class="recap-timeline-title">Tu semana día a día</h2>')
    if not items:
        parts.append('<p class="recap-empty">No hay entrenamientos registrados en esta semana.</p>')
    for item in items:
        day = date.fromisoformat(item['trained_on'])
        parts.append(f'<article class="recap-entry"><time class="recap-date" datetime="{item["trained_on"]}"><strong>{("Lun","Mar","Mié","Jue","Vie","Sáb","Dom")[day.weekday()]}</strong>{day.day}/{day.month}</time><header><h2>{escape(item["title"])}</h2></header>')
        if item.get('source_image_id'):
            parts.append(f'<a class="recap-photo-link" href="/shared/week/{token}/images/{item["source_image_id"]}" aria-label="Ver foto del entrenamiento completa"><img class="weekly-photo" src="/shared/week/{token}/images/{item["source_image_id"]}" alt="Foto del entrenamiento" loading="lazy" decoding="async"></a>')
        for label, key in [('Resultado', 'result_text'), ('Notas y adaptaciones', 'adaptations')]:
            if item[key]:
                parts.append(f'<section class="recap-{key}"><h3>{label}</h3><p class="weekly-copy">{escape(item[key])}</p></section>')
        if item['rpe'] is not None:
            parts.append(f'<p class="recap-effort">Esfuerzo: {item["rpe"]}/10</p>')
        if item['workout']:
            parts.append(f'<details class="recap-workout"><summary>Ver entrenamiento</summary><p class="weekly-copy">{escape(item["workout"])}</p></details>')
        parts.append('</article>')
    parts.append('</section>')
    # Count explicit exercise names already present in the authorized workout;
    # never infer technique, personal records or performance from them.
    movements = [('Sentadilla',r'\bsentadillas?\b'),('Thruster',r'\bthrusters?\b'),('Clean',r'\bcleans?\b'),('Remo',r'\bremo\b'),('Burpee',r'\bburpees?\b'),('Pull-up',r'\bpull[ -]?ups?\b'),('Air squat',r'\bair squats?\b'),('Deadlift',r'\bdeadlifts?\b')]
    frequencies = sorted([(name,sum(bool(re.search(pattern,item['workout'],re.I)) for item in items)) for name,pattern in movements],key=lambda pair:pair[1],reverse=True)
    repeated = [(name,count) for name,count in frequencies if count > 1][:3]
    if repeated:
        parts.append('<section class="recap-repeated"><h2>Movimientos que se repitieron</h2><div>')
        for name,count in repeated:
            parts.append(f'<article><strong>{name}</strong><span>En {count} entrenamientos</span></article>')
        parts.append('</div></section>')
    parts.append('<footer class="recap-footer"><strong>Compartido desde Fluxio Movement</strong><p>Esta semana se actualiza al agregar, editar o eliminar entrenamientos. Recarga el enlace para ver los cambios.</p></footer>')
    return ''.join(parts)


def page(body):
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><meta name="theme-color" content="#f7f7f5"><meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer"><title>Semana compartida · Fluxio</title><link rel="stylesheet" href="/static/styles.css"><link rel="stylesheet" href="/static/visual-v2.css?v=2"><link rel="stylesheet" href="/static/weekly.css?v=3"></head><body class="weekly-public"><main class="weekly-shared">' + body + '</main></body></html>'
