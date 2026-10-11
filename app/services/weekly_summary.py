"""Calendar summaries and revocable live weeks shared across web and WhatsApp."""
import hashlib
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from uuid import UUID
from sqlalchemy import select, update
from ..models import TrainingSession, WeeklyShare, User
from .training_errors import TrainingNotFound, TrainingInvalid


CONSENT_VERSION = 'weekly-live-v1'
CONSENT_NOTICE = ('Quien tenga el enlace podrá consultar esta semana, incluidos entrenamientos, '
    'resultados, notas, esfuerzo y fotografías. También mostrará registros, fotografías, '
    'resultados y notas que agregues o modifiques después en esta semana. '
    'Vence en 7 días como máximo y puedes revocarlo antes.')


def consent_verified(row):
    data = row.snapshot.get('consent') if isinstance(row.snapshot, dict) else None
    try:
        return (isinstance(data, dict) and data.get('version') == CONSENT_VERSION
            and data.get('accepted') is True
            and data.get('channel') in {'web', 'whatsapp'}
            and bool(UUID(data['request_id']))
            and datetime.fromisoformat(data['accepted_at']).tzinfo is not None)
    except (KeyError, TypeError, ValueError):
        return False


def now():
    return datetime.now(timezone.utc)


def week_start(day=None):
    day = day or now().astimezone(ZoneInfo('America/Santiago')).date()
    return day - timedelta(days=day.weekday())


def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


class WeeklySummaryService:
    def __init__(self, session, athlete_id, *, commit=True):
        self.session, self.athlete_id, self.commit = session, athlete_id, commit

    def persist(self):
        if self.commit:
            self.session.commit()
        else:
            self.session.flush()

    def summary(self, day=None):
        start = week_start(day)
        end = start + timedelta(days=6)
        rows = list(self.session.scalars(select(TrainingSession).where(
            TrainingSession.athlete_id == self.athlete_id,
            TrainingSession.trained_on >= start, TrainingSession.trained_on <= end
        ).order_by(TrainingSession.trained_on, TrainingSession.created_at, TrainingSession.id)))
        efforts = [row.rpe for row in rows if row.rpe is not None]
        return {'week_start': start.isoformat(), 'week_end': end.isoformat(),
            'session_count': len(rows), 'active_days': len({row.trained_on for row in rows}),
            'average_rpe': round(sum(efforts) / len(efforts), 1) if efforts else None,
            'rpe_count': len(efforts),
            'items': [{key: getattr(row, key) for key in
                ('title', 'workout', 'result_text', 'adaptations', 'rpe')} |
                {'trained_on': row.trained_on.isoformat(),
                 'source_image_id': str(row.source_image_id) if row.source_image_id else None} for row in rows]}

    def create_share(self, day=None, *, consent=False, consent_version=None, request_id=None, channel='web', event_id=None):
        if consent is not True or consent_version != CONSENT_VERSION or channel not in {'web', 'whatsapp'}:
            raise TrainingInvalid('Confirma qué se publicará antes de compartir tu semana')
        try:
            request_id = str(UUID(str(request_id)))
        except (ValueError, TypeError):
            raise TrainingInvalid('Identificador de consentimiento inválido') from None
        # Serialize requests and administrative deactivation using the same User lock as S02.
        user = self.session.scalar(select(User).where(User.id == self.athlete_id).with_for_update()
            .execution_options(populate_existing=True))
        if user is None or not user.is_active or user.role != 'ATHLETE':
            raise TrainingNotFound('Cuenta no disponible')
        if channel == 'whatsapp':
            try:
                event_id = str(UUID(str(event_id)))
            except (ValueError, TypeError):
                raise TrainingInvalid('Evidencia de consentimiento inválida') from None
        start = week_start(day)
        existing = self.session.scalar(select(WeeklyShare).where(
            WeeklyShare.athlete_id == self.athlete_id,
            WeeklyShare.snapshot['consent']['request_id'].astext == request_id))
        if existing:
            if existing.week_start != start:
                raise TrainingInvalid('El consentimiento corresponde a otra semana')
            # The raw token is never persisted/recovered. A replay creates nothing and
            # never revives an expired/revoked grant, even if the first response was lost.
            self.persist()
            return {'id': str(existing.id), 'path': None, 'expires_at': existing.expires_at.isoformat(),
                'already_created': True}
        try:
            ttl = int(os.getenv('WEEKLY_SHARE_TOKEN_TTL_HOURS', '168'))
            if not 1 <= ttl <= 168:
                raise ValueError()
        except ValueError:
            raise TrainingInvalid('El vencimiento del enlace debe estar entre 1 y 168 horas') from None
        token = secrets.token_urlsafe(32)
        accepted_at = now()
        row = WeeklyShare(athlete_id=self.athlete_id, token_hash=token_hash(token),
            week_start=start, snapshot={'consent': {'version': CONSENT_VERSION,
                'accepted': True, 'channel': channel, 'request_id': request_id, 'accepted_at': accepted_at.isoformat(),
                **({'event_id': event_id} if channel == 'whatsapp' else {})}},
            expires_at=accepted_at + timedelta(hours=ttl))
        self.session.add(row)
        self.persist()
        return {'id': str(row.id), 'path': '/shared/week/' + token,
            'expires_at': row.expires_at.isoformat()}

    def list_shares(self, day=None):
        return [{'id': str(row.id), 'expires_at': row.expires_at.isoformat(), 'consent_required': not consent_verified(row)}
            for row in self.session.scalars(select(WeeklyShare).where(
                WeeklyShare.athlete_id == self.athlete_id, WeeklyShare.week_start == week_start(day),
                WeeklyShare.revoked_at.is_(None), WeeklyShare.expires_at > now()))]

    def revoke(self, identifier):
        row = self.session.scalar(select(WeeklyShare).where(
            WeeklyShare.id == identifier, WeeklyShare.athlete_id == self.athlete_id).with_for_update())
        if row is None:
            raise TrainingNotFound('Enlace no encontrado')
        row.revoked_at = now()
        self.persist()

    def revoke_week(self, day=None):
        self.session.execute(update(WeeklyShare).where(
            WeeklyShare.athlete_id == self.athlete_id,
            WeeklyShare.week_start == week_start(day), WeeklyShare.revoked_at.is_(None)
        ).values(revoked_at=now()))
        self.persist()


def share_record(session, token):
    if not re.fullmatch(r'[A-Za-z0-9_-]{43}', token):
        raise TrainingNotFound('Este enlace venció, fue revocado o no existe')
    row = session.scalar(select(WeeklyShare).join(User, User.id == WeeklyShare.athlete_id).where(
        User.is_active.is_(True), User.role == 'ATHLETE', WeeklyShare.token_hash == token_hash(token),
        WeeklyShare.revoked_at.is_(None), WeeklyShare.expires_at > now()))
    if row is None or not consent_verified(row):
        raise TrainingNotFound('Este enlace venció, fue revocado o no existe')
    return row


def read_share(session, token):
    row = share_record(session, token)
    return WeeklySummaryService(session, row.athlete_id).summary(row.week_start)


def summary_text(summary):
    sessions, days = summary['session_count'], summary['active_days']
    lines = [f"Semana {summary['week_start']} al {summary['week_end']}",
        f"{sessions} {'entrenamiento' if sessions == 1 else 'entrenamientos'} · {days} {'día activo' if days == 1 else 'días activos'}"]
    if summary['average_rpe'] is not None:
        lines.append(f"Esfuerzo promedio: {summary['average_rpe']}/10 ({summary['rpe_count']} registros)")
    if not summary['items']:
        lines.append('No hay entrenamientos registrados en esta semana.')
    for item in summary['items']:
        lines.append(f"{item['trained_on']}: {item['title']}" +
            (f" — {item['result_text']}" if item['result_text'] else ''))
    return '\n'.join(lines)
