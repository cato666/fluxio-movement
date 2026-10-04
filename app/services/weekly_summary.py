"""Calendar summaries and revocable live weeks shared across web and WhatsApp."""
import hashlib
import os
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select, update
from ..models import TrainingSession, WeeklyShare
from .training_errors import TrainingNotFound


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

    def create_share(self, day=None):
        snapshot = self.summary(day)
        token = secrets.token_urlsafe(32)
        ttl = int(os.getenv('WEEKLY_SHARE_TOKEN_TTL_HOURS', '168'))
        if not 1 <= ttl <= 168:
            raise ValueError('WEEKLY_SHARE_TOKEN_TTL_HOURS must be between 1 and 168')
        row = WeeklyShare(athlete_id=self.athlete_id, token_hash=token_hash(token),
            week_start=date.fromisoformat(snapshot['week_start']), snapshot=snapshot,
            expires_at=now() + timedelta(hours=ttl))
        self.session.add(row)
        self.persist()
        return {'id': str(row.id), 'path': '/shared/week/' + token,
            'expires_at': row.expires_at.isoformat()}

    def list_shares(self, day=None):
        return [{'id': str(row.id), 'expires_at': row.expires_at.isoformat()}
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
    row = session.scalar(select(WeeklyShare).where(WeeklyShare.token_hash == token_hash(token),
        WeeklyShare.revoked_at.is_(None), WeeklyShare.expires_at > now()))
    if row is None:
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
