"""Authenticated weekly controls and a minimal public snapshot reader."""
from datetime import date
from html import escape
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
        sessions, days = data['session_count'], data['active_days']
        parts = [f"<h1>Semana de entrenamiento</h1><p>{data['week_start']} — {data['week_end']}</p>",
            f"<p>{sessions} {'entrenamiento' if sessions == 1 else 'entrenamientos'} · {days} {'día activo' if days == 1 else 'días activos'}</p>"]
        if data['average_rpe'] is not None:
            parts.append(f"<p>Esfuerzo promedio: {data['average_rpe']}/10 ({data['rpe_count']} registros)</p>")
        parts.append('<p>Copia de la semana al crear el enlace. Los cambios posteriores no se incluyen.</p>')
        if not data['items']:
            parts.append('<p>No hay entrenamientos registrados en esta semana.</p>')
        for item in data['items']:
            parts.append(f"<article class='training-entry-content'><h2>{escape(item['title'])}</h2><p>{item['trained_on']}</p>")
            if item.get('source_image_id'):
                parts.append(f'<img class="weekly-photo" src="/shared/week/{token}/images/{item["source_image_id"]}" alt="Foto del entrenamiento" loading="lazy">')
            for label, key in [('Entrenamiento', 'workout'), ('Resultado', 'result_text'), ('Notas y adaptaciones', 'adaptations')]:
                if item[key]:
                    parts.append(f"<h3>{label}</h3><p class='weekly-copy'>{escape(item[key])}</p>")
            if item['rpe'] is not None:
                parts.append(f"<p>Esfuerzo: {item['rpe']}/10</p>")
            parts.append('</article>')
        return HTMLResponse(page(''.join(parts)), headers=headers)

    @routes.get('/shared/week/{token}/images/{identifier}')
    def shared_image(token: str, identifier: UUID, session: Session = Depends(get_session)):
        from .services.training_service import TrainingService
        from .services.training_errors import TrainingNotFound
        try:
            row = share_record(session, token)
            if not any(item.get('source_image_id') == str(identifier) for item in row.snapshot['items']):
                raise TrainingNotFound('Foto no disponible en esta semana')
            path = TrainingService(session, row.athlete_id).image_path(identifier)
        except TrainingNotFound as error:
            return JSONResponse({'detail': str(error)}, status_code=404, headers=PRIVATE_HEADERS)
        return FileResponse(path, media_type='image/jpeg', headers=PRIVATE_HEADERS |
            {'X-Content-Type-Options': 'nosniff'})

    return routes


def page(body):
    return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="referrer" content="no-referrer"><title>Semana compartida · Fluxio</title><link rel="stylesheet" href="/static/styles.css"></head><body class="weekly-public"><main class="weekly-shared">' + body + '</main></body></html>'
