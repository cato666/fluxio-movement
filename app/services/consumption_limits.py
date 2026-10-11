"""Durable reservations, independent of provider/worker transaction outcomes.
No prompts, phones, tokens, response bodies or request headers are logged.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
import logging
import os
from uuid import UUID, uuid4
from fastapi import HTTPException
from sqlalchemy import select, func, text, cast, String, or_
from sqlalchemy.orm import Session, aliased
from ..models import User, PlanInteraction
from ..database import engine

logger = logging.getLogger(__name__)
LOCK = 60320261010


def reject(status, reason):
    logger.info('consumption_rejected reason=%s', reason)
    raise HTTPException(status, 'Cupo no disponible. Puedes registrar manualmente en la bitácora.' if status != 409 else
        'Esta operación ya fue reservada; no se repetirá la llamada. Revisa el resultado o registra manualmente.')


DEFAULTS = {
    'INTERPRET_DAILY': 3, 'TRANSCRIBE_DAILY': 3, 'ANALYZE_DAILY': 1,
    'WHATSAPP_INBOUND_DAILY': 20, 'WHATSAPP_OUTBOUND_DAILY': 20,
    'WHATSAPP_RATE_PER_CONVERSATION': 5, 'VIDEO_CONCURRENT': 1,
    'GLOBAL_DAILY_USD': '3', 'GLOBAL_PILOT_USD': '30', 'ALERT_PERCENT': 80,
    'INTERPRET_RESERVE_USD': '0.05', 'TRANSCRIBE_RESERVE_USD': '0.03',
    'ANALYZE_RESERVE_USD': '0.20', 'WHATSAPP_SEND_RESERVE_USD': '0.02',
}
VIDEO_COSTS = ('VIDEO_COMPUTE_RESERVE_USD', 'VIDEO_STORAGE_RESERVE_USD', 'VIDEO_OTHER_RESERVE_USD')


def configuration(session=None, operation=None, overrides=None):
    from ..models import AdminSetting
    production = os.getenv('APP_ENV', 'development').strip().lower() == 'production'
    stored = session.get(AdminSetting, 'consumption_limits') if session is not None else None
    controlled = overrides if overrides is not None else stored.value if stored else {}
    values = {}
    try:
        for name, default in DEFAULTS.items():
            raw = controlled.get(name, os.getenv('USAGE_' + name, None if production else str(default)))
            if raw is None:
                reject(503, 'configuration_missing')
            value = Decimal(str(raw))
            if not value.is_finite() or value < 0 or value.as_tuple().exponent < -8 or value > Decimal('1000000'):
                reject(503, 'configuration_invalid')
            if 'USD' not in name and value != int(value):
                reject(503, 'configuration_invalid')
            if name.endswith('RESERVE_USD') and value <= 0:
                reject(503, 'configuration_invalid')
            if name == 'ALERT_PERCENT' and not 1 <= value < 100:
                reject(503, 'configuration_invalid')
            values[name] = value
        for name in VIDEO_COSTS:
            raw = controlled.get(name, os.getenv('USAGE_' + name, None if production else '0'))
            if raw is None or raw == '':
                if operation == 'ANALYZE':
                    reject(503, 'video_cost_missing')
                continue
            value = Decimal(str(raw))
            if not value.is_finite() or value < 0 or value.as_tuple().exponent < -8 or value > Decimal('1000000'):
                reject(503, 'configuration_invalid')
            values[name] = value
        window = session.get(AdminSetting, 'consumption_window') if session is not None else None
        development_start = window.value['start'].split('T')[0] if window else clock().date().isoformat()
        raw_start = controlled.get('PILOT_START', os.getenv('USAGE_PILOT_START', None if production else development_start))
        if raw_start is None:
            reject(503, 'pilot_start_missing')
        values['PILOT_START'] = datetime.strptime(raw_start, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        if values['PILOT_START'].time() != datetime.min.time():
            reject(503, 'pilot_start_invalid')
    except (InvalidOperation, ValueError, TypeError):
        reject(503, 'configuration_invalid')
    return values


def clock():
    return datetime.now(timezone.utc)


def budget(session, config, cost, *, existing=False):
    from ..whatsapp.models import WhatsAppUsage
    from ..models import AdminSetting
    start = config['PILOT_START']
    if not start <= clock() < start + timedelta(days=30):
        reject(429, 'pilot_window_closed')
    window = session.get(AdminSetting, 'consumption_window')
    if window and window.value['start'] != start.isoformat():
        reject(503, 'pilot_window_immutable')
    if window is None:
        session.add(AdminSetting(key='consumption_window', value={'start': start.isoformat()}))
    today = clock().replace(hour=0, minute=0, second=0, microsecond=0)
    for period, limit in ((today, 'GLOBAL_DAILY_USD'), (start, 'GLOBAL_PILOT_USD')):
        total = Decimal(0)
        for operation, reserved in session.execute(select(PlanInteraction.operation, PlanInteraction.budget_usd).where(
                or_(PlanInteraction.created_at >= period, PlanInteraction.started_at >= period,
                    PlanInteraction.reservation_state == 'RESERVED'), PlanInteraction.reservation_state != 'RELEASED')):
            # Unknown historical costs retain a conservative reservation.
            total += reserved if reserved is not None else config[operation + '_RESERVE_USD'] + (
                sum(config.get(k, Decimal(0)) for k in VIDEO_COSTS) if operation == 'ANALYZE' else 0)
        total += session.scalar(select(func.coalesce(func.sum(WhatsAppUsage.cost), 0)).where(
            WhatsAppUsage.category == 'send_reservation', or_(WhatsAppUsage.created_at >= period, WhatsAppUsage.reservation_state == 'RESERVED'),
            WhatsAppUsage.reservation_state != 'RELEASED'))
        legacy = aliased(WhatsAppUsage)
        newer = aliased(WhatsAppUsage)
        legacy_costs = session.scalars(select(legacy.cost).where(legacy.category == 'outbound',
            legacy.created_at >= period, ~select(newer.id).where(
                newer.category == 'send_reservation', newer.event_key.like(
                    'send-reservation:' + func.substr(legacy.event_key, 10, 36) + ':%')).exists()))
        total += sum(value if value is not None else config['WHATSAPP_SEND_RESERVE_USD'] for value in legacy_costs)
        if total + cost > config[limit] or (not existing and cost == 0 and total >= config[limit]):
            reject(429, 'global_budget')
        if config[limit] and (total + cost) * 100 >= config[limit] * config['ALERT_PERCENT']:
            logger.warning('consumption_budget_alert period=%s threshold=%s', 'daily' if period == today else 'pilot', config['ALERT_PERCENT'])


def reserve(session, user_id, operation, *, request_key=None, channel='web'):
    from ..administration import usage
    if operation not in ('ANALYZE', 'INTERPRET', 'TRANSCRIBE') or channel not in ('web', 'whatsapp'):
        reject(422, 'operation_invalid')
    key = request_key or str(uuid4())
    try:
        key = str(UUID(str(key)))
    except ValueError:
        reject(422, 'request_key_invalid')
    # NO KEY UPDATE blocks account changes but permits FK insertion by the durable
    # reservation transaction. Caller retains this lock throughout external work.
    user = session.scalar(select(User).where(User.id == user_id).with_for_update(key_share=True)
                          .execution_options(populate_existing=True))
    if user is None or not user.is_active:
        reject(403, 'account_inactive')
    with Session(bind=engine) as durable:
        durable.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': LOCK})
        config = configuration(durable, operation)
        if durable.scalar(select(PlanInteraction.id).where(PlanInteraction.user_id == user_id,
                PlanInteraction.operation == operation, PlanInteraction.request_key == key)):
            reject(409, 'reservation_replay')
        status = usage(durable, user)
        if operation not in status['enabled_operations']:
            reject(403, 'operation_disabled')
        if not status['remaining']:
            reject(429, 'monthly_quota')
        today = clock().replace(hour=0, minute=0, second=0, microsecond=0)
        count = durable.scalar(select(func.count()).select_from(PlanInteraction).where(
            PlanInteraction.user_id == user_id, PlanInteraction.operation == operation,
            or_(PlanInteraction.created_at >= today, PlanInteraction.started_at >= today,
                PlanInteraction.reservation_state == 'RESERVED'), PlanInteraction.reservation_state != 'RELEASED'))
        if count >= config[operation + '_DAILY']:
            reject(429, 'athlete_daily_limit')
        recent = durable.scalar(select(func.count()).select_from(PlanInteraction).where(
            PlanInteraction.user_id == user_id, PlanInteraction.created_at >= clock() - timedelta(minutes=1),
            PlanInteraction.reservation_state != 'RELEASED'))
        if recent >= config['WHATSAPP_RATE_PER_CONVERSATION']:
            reject(429, 'athlete_rate_limit')
        cost = config[operation + '_RESERVE_USD']
        if operation == 'ANALYZE':
            running = durable.scalar(select(func.count()).select_from(PlanInteraction).where(
                PlanInteraction.operation == 'ANALYZE', PlanInteraction.reservation_state == 'RESERVED'))
            from ..models import Analysis
            unmatched = durable.scalar(select(func.count()).select_from(Analysis).where(
                Analysis.status.in_(('PENDING', 'PROCESSING')), ~select(PlanInteraction.id).where(
                    PlanInteraction.resource_id == Analysis.id).exists()))
            if running + unmatched >= config['VIDEO_CONCURRENT']:
                reject(429, 'video_concurrency')
            cost += sum(config[k] for k in VIDEO_COSTS)
        budget(durable, config, cost)
        row = PlanInteraction(user_id=user_id, operation=operation, request_key=key,
                                    channel=channel, budget_usd=cost, reservation_state='RESERVED')
        durable.add(row)
        durable.commit()
        identifier = row.id
    logger.info('consumption_reserved operation=%s channel=%s', operation, channel)
    return identifier


def admit_message(session, inbox, athlete_id):
    from ..whatsapp.models import WhatsAppInbox, WhatsAppUsage
    with Session(bind=engine) as durable:
        durable.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': LOCK})
        config = configuration(durable)
        key = 'admission:' + str(inbox.id)
        if durable.scalar(select(WhatsAppUsage.id).where(WhatsAppUsage.event_key == key)):
            return True  # Same admission may replay local work; AI reservations prevent repeated calls.
        start = clock() - timedelta(minutes=1)
        peer_count = durable.scalar(select(func.count()).select_from(WhatsAppUsage).join(
            WhatsAppInbox, WhatsAppUsage.event_key == 'admission:' + cast(WhatsAppInbox.id, String)).where(
            WhatsAppInbox.peer_hash == inbox.peer_hash, WhatsAppUsage.category == 'admission', WhatsAppUsage.created_at >= start))
        daily = durable.scalar(select(func.count()).select_from(WhatsAppUsage).where(
            WhatsAppUsage.athlete_id == athlete_id, WhatsAppUsage.category == 'admission',
            WhatsAppUsage.created_at >= clock().replace(hour=0, minute=0, second=0, microsecond=0))) if athlete_id else 0
        recent = durable.scalar(select(func.count()).select_from(WhatsAppUsage).where(
            WhatsAppUsage.athlete_id == athlete_id, WhatsAppUsage.category == 'admission', WhatsAppUsage.created_at >= start)) if athlete_id else 0
        if peer_count >= config['WHATSAPP_RATE_PER_CONVERSATION'] or recent >= config['WHATSAPP_RATE_PER_CONVERSATION']:
            reject(429, 'conversation_limit')
        if daily >= config['WHATSAPP_INBOUND_DAILY']:
            reject(429, 'inbound_daily_limit')
        durable.add(WhatsAppUsage(event_key=key, category='admission', athlete_id=athlete_id, units=1))
        durable.commit()
    return True


def reserve_send(session, row):
    from ..whatsapp.models import WhatsAppUsage
    with Session(bind=engine) as durable:
        durable.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': LOCK})
        config = configuration(durable)
        key = f'send-reservation:{row.id}:{row.attempts}'
        if durable.scalar(select(WhatsAppUsage.id).where(WhatsAppUsage.event_key == key)):
            reject(409, 'send_replay')
        count = durable.scalar(select(func.count()).select_from(WhatsAppUsage).where(
            WhatsAppUsage.category == 'send_reservation', WhatsAppUsage.athlete_id == row.athlete_id, WhatsAppUsage.created_at >= clock().replace(hour=0, minute=0, second=0, microsecond=0)))
        if count >= config['WHATSAPP_OUTBOUND_DAILY']:
            reject(429, 'send_daily_limit')
        cost = config['WHATSAPP_SEND_RESERVE_USD']
        budget(durable, config, cost)
        durable.add(WhatsAppUsage(event_key=key, category='send_reservation', athlete_id=row.athlete_id, units=1, cost=cost, reservation_state='RESERVED'))
        durable.commit()
    logger.info('consumption_reserved operation=SEND channel=whatsapp')


def transition(identifier, state, *, not_called=False):
    """Provider outcomes never imply a refund of unknown costs."""
    if state not in ('CONFIRMED', 'UNCERTAIN', 'RELEASED', 'STARTED'):
        raise ValueError('Invalid reservation transition')
    with Session(bind=engine) as durable:
        durable.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': LOCK})
        row = durable.get(PlanInteraction, identifier)
        if row is None or row.reservation_state != 'RESERVED':
            reject(409, 'reservation_not_open')
        if state == 'RELEASED' and (not not_called or row.started_at is not None):
            reject(409, 'release_not_proven')
        if state == 'STARTED':
            if row.started_at:
                reject(409, 'provider_replay')
            # Revalidate after queueing or a UTC day change; pending obligations
            # count against the new day's budget before any provider starts.
            budget(durable, configuration(durable, row.operation), Decimal(0), existing=True)
            row.started_at = clock()
        else:
            row.reservation_state = state
        durable.commit()
    logger.info('consumption_transition state=%s', state)


def settle_send(row, state):
    from ..whatsapp.models import WhatsAppUsage
    with Session(bind=engine) as durable:
        record = durable.scalar(select(WhatsAppUsage).where(
            WhatsAppUsage.event_key == f'send-reservation:{row.id}:{row.attempts}').with_for_update())
        if record:
            record.reservation_state = state
            durable.commit()
    logger.info('consumption_transition operation=SEND state=%s', state)


def bind_video(identifier, job):
    with Session(bind=engine) as durable:
        row = durable.get(PlanInteraction, identifier)
        if row and row.reservation_state == 'RESERVED' and row.resource_id is None:
            row.resource_id = job
            durable.commit()


def video_reservation(session, job, user_id):
    from ..whatsapp.identity import active_account
    if active_account(session, user_id) is None:
        reject(403, 'account_inactive')
    existing = session.scalar(select(PlanInteraction).where(PlanInteraction.resource_id == job))
    if existing:
        return existing.id
    identifier = reserve(session, user_id, 'ANALYZE')
    bind_video(identifier, job)
    return identifier


def check_budget():
    """Nonbillable media download still stops at a fully reserved budget."""
    with Session(bind=engine) as durable:
        durable.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': LOCK})
        budget(durable, configuration(durable), Decimal(0))


def abandon_media(session, inbox_id):
    with Session(bind=engine) as durable:
        for (event, operation), identifier in session.info.get('media_reservations', {}).items():
            if event != inbox_id:
                continue
            row = durable.get(PlanInteraction, identifier)
            if row and row.reservation_state == 'RESERVED':
                transition(identifier, 'UNCERTAIN')
