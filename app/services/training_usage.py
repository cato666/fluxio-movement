"""Request-scoped provider accounting. Never stores prompts, photos or audio."""
from contextlib import contextmanager
from contextvars import ContextVar
from math import isfinite
from time import perf_counter
from sqlalchemy import select, func, case, or_
from ..models import TrainingAIUsage, User

_current = ContextVar('training_usage', default=None)


def report_usage(model, usage=None, duration_seconds=None):
    recorder = _current.get()
    if recorder is None:
        return
    session, athlete_id, operation = recorder['context']
    row = recorder.get('row')
    if row is None:
        row = TrainingAIUsage(athlete_id=athlete_id, operation=operation, model=model[:120], status='RUNNING')
        session.add(row)
        session.commit()  # Keep a durable attempt even if the worker stops mid-call.
        recorder['row'] = row
        recorder['started'] = perf_counter()
    row.model = model[:120]
    if isinstance(usage, dict):
        for key in ('input_tokens', 'output_tokens'):
            value = usage.get(key)
            if type(value) is int and value >= 0:
                setattr(row, key, value)
        details = usage.get('output_tokens_details') or {}
        value = details.get('reasoning_tokens') if isinstance(details, dict) else None
        if type(value) is int and value >= 0:
            row.reasoning_tokens = value
    if isinstance(duration_seconds, (int, float)) and isfinite(duration_seconds) and duration_seconds >= 0:
        row.duration_seconds = duration_seconds


@contextmanager
def track_usage(session, athlete_id, operation):
    recorder = {'context': (session, athlete_id, operation)}
    token = _current.set(recorder)
    error = None
    try:
        yield
    except Exception as exc:
        error = type(exc).__name__  # No provider response or private source content.
        raise
    finally:
        _current.reset(token)
        row = recorder.get('row')
        if row is not None:
            row.status = 'FAILED' if error else 'COMPLETED'
            row.error = error
            row.latency_ms = round((perf_counter() - recorder['started']) * 1000)
            session.commit()


def extend_usage(data, session):
    """Add training accounting to the incumbent movement-analysis payload."""
    usage = TrainingAIUsage
    summed = lambda column: func.coalesce(func.sum(column), 0)
    missing = case((or_(usage.input_tokens.is_(None), usage.output_tokens.is_(None)), 1), else_=0)
    summary = session.execute(select(func.count(usage.id), summed(case((usage.status == 'COMPLETED', 1), else_=0)),
                                     summed(usage.input_tokens), summed(usage.output_tokens), summed(usage.reasoning_tokens), summed(missing))).one()
    audio_calls, audio_seconds = session.execute(select(func.count(usage.id), summed(usage.duration_seconds)).where(usage.operation == 'TRANSCRIBE')).one()
    data['totals']['transcription_runs'] = audio_calls
    data['totals']['audio_seconds'] = audio_seconds
    data['totals']['training_runs'] = summary[0]
    data['totals']['completed_runs'] += summary[1]
    data['totals']['input_tokens'] += summary[2]
    data['totals']['output_tokens'] += summary[3]
    data['totals']['reasoning_tokens'] += summary[4]
    data['totals']['unreported_training_runs'] = summary[5]
    models = {item['model']: item for item in data['by_model']}
    for model, count, incoming, outgoing in session.execute(select(usage.model, func.count(usage.id), summed(usage.input_tokens), summed(usage.output_tokens)).group_by(usage.model)):
        item = models.setdefault(model, dict(model=model,runs=0,input_tokens=0,output_tokens=0,total_tokens=0))
        item['runs'] += count; item['input_tokens'] += incoming; item['output_tokens'] += outgoing; item['total_tokens'] += incoming + outgoing
    athletes = []
    for identifier, name, count, incoming, outgoing, seconds, unreported in session.execute(
            select(usage.athlete_id, User.name, func.count(usage.id), summed(usage.input_tokens), summed(usage.output_tokens), summed(usage.duration_seconds), summed(missing))
            .join(User, User.id == usage.athlete_id).group_by(usage.athlete_id, User.name)):
        athletes.append(dict(athlete_id=str(identifier),athlete_name=name,runs=count,input_tokens=incoming,output_tokens=outgoing,total_tokens=incoming+outgoing,audio_seconds=seconds,unreported_runs=unreported))
    recent = []
    rows = session.execute(select(usage, User.name).join(User, User.id == usage.athlete_id).order_by(usage.created_at.desc()).limit(25)).all()
    for row, name in rows:
        incoming, outgoing = row.input_tokens or 0, row.output_tokens or 0
        known = row.input_tokens is not None and row.output_tokens is not None
        recent.append(dict(analysis_id=None,exercise='Interpretación de WOD' if row.operation == 'INTERPRET' else 'Dictado de entrenamiento',
                           operation=row.operation,athlete_name=name,status=row.status,model=row.model,
                           input_tokens=row.input_tokens,output_tokens=row.output_tokens,reasoning_tokens=row.reasoning_tokens,
                           total_tokens=incoming+outgoing if known else None,duration_seconds=row.duration_seconds,
                           latency_ms=row.latency_ms,created_at=row.created_at))
    data['totals']['total_tokens'] = data['totals']['input_tokens'] + data['totals']['output_tokens']
    data['by_model'] = sorted(models.values(), key=lambda item:item['total_tokens'], reverse=True)
    data['training_by_athlete'] = sorted(athletes, key=lambda item:item['total_tokens'], reverse=True)
    data['recent_runs'] = sorted(data['recent_runs'] + recent, key=lambda item:item['created_at'], reverse=True)[:25]
    return data
