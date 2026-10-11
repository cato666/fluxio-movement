from datetime import timedelta
from decimal import Decimal, InvalidOperation
import os
from uuid import uuid4
from sqlalchemy import select, exists, func
from sqlalchemy.orm import aliased
from sqlalchemy.dialects.postgresql import insert
from .identity import IdentityResolver, active_account, now
from .models import WhatsAppInbox, WhatsAppOutbox, WhatsAppUsage
from .security import ChannelError


def usage(session, event_key, category, athlete_id=None, units=1, cost=None):
    statement = insert(WhatsAppUsage).values(id=uuid4(), athlete_id=athlete_id,
        event_key=event_key, category=category, units=units, cost=cost, currency='USD')
    session.execute(statement.on_conflict_do_update(index_elements=['event_key'],
        set_={'athlete_id':func.coalesce(WhatsAppUsage.athlete_id, statement.excluded.athlete_id)}))


def accept(session, messages, vault):
    accepted = 0
    for message in messages:
        if message.happened_at < now() - timedelta(days=7) or message.happened_at > now() + timedelta(minutes=5):
            raise ChannelError('message_timestamp_out_of_window')
        key = message.provider_message_id if message.event == 'received' else f'{message.event}:{message.provider_message_id}'
        identifier = uuid4()
        result = session.execute(insert(WhatsAppInbox).values(id=identifier, provider='kapso',
            provider_message_id=key, message_type=message.message_type, event=message.event,
            peer_hash=vault.phone_hash(message.phone) if message.phone else None,
            payload_encrypted=vault.encrypt(message.minimized()), key_version=vault.version,
            happened_at=message.happened_at, expires_at=now() + timedelta(hours=24))
            .on_conflict_do_nothing(index_elements=['provider', 'provider_message_id']).returning(WhatsAppInbox.id))
        if result.scalar_one_or_none():
            accepted += 1
            if message.event == 'received':
                usage(session, f'inbound:{identifier}', 'inbound')
    return accepted


def reply(session, vault, inbox, phone, text, *, athlete_id=None, actions=None, action='reply'):
    # Interactive bodies are bounded to 1024; long proposals remain complete.
    if len(text) > (1024 if actions else 4096):
        for index, start in enumerate(range(0, len(text), 1000)):
            last = start + 1000 >= len(text)
            reply(session, vault, inbox, phone, text[start:start+1000], athlete_id=athlete_id,
                  actions=actions if last else None, action=f'{action}~{index:03d}')
        return
    key = f'{inbox.id}:{action}'
    session.execute(insert(WhatsAppOutbox).values(id=uuid4(), athlete_id=athlete_id,
        dedupe_key=key, action=action, payload_encrypted=vault.encrypt({'phone': phone, 'text': text, 'actions': actions}),
        key_version=vault.version, created_at=now(), expires_at=now() + timedelta(hours=23))
        .on_conflict_do_nothing(index_elements=['dedupe_key']))


def dispatch_one(session, provider, vault):
    # A stale in-flight send has an unknown outcome and is never replayed blindly.
    for stale in session.scalars(select(WhatsAppOutbox).where(WhatsAppOutbox.state == 'SENDING',
        WhatsAppOutbox.lease_until < now()).with_for_update(skip_locked=True)):
        from ..services.consumption_limits import settle_send
        settle_send(stale, 'UNCERTAIN')
        stale.state, stale.error_code = 'UNCERTAIN', 'send_interrupted'
    predecessor = aliased(WhatsAppOutbox)
    blocked = exists(select(predecessor.id).where(
        predecessor.dedupe_key.like(func.substr(WhatsAppOutbox.dedupe_key, 1, 36) + ':%'),
        predecessor.created_at < WhatsAppOutbox.created_at,
        predecessor.state.not_in(('SENT','DELIVERED','READ'))))
    row = session.scalar(select(WhatsAppOutbox).where(WhatsAppOutbox.state.in_(('PENDING', 'RETRY')),
        WhatsAppOutbox.next_attempt_at <= now(), ~blocked).order_by(WhatsAppOutbox.created_at, WhatsAppOutbox.id)
        .with_for_update(skip_locked=True).limit(1))
    if row is None:
        session.commit()
        return False
    if row.expires_at <= now():
        row.state, row.payload_encrypted = 'EXPIRED', None
        session.commit()
        return True
    row.state, row.lease_until = 'SENDING', now() + timedelta(minutes=2)
    row.attempts += 1
    session.commit()
    # Recheck after the durable SENDING commit, holding the user lock until send
    # finishes. Deactivation may have committed between claiming and this check.
    if row.athlete_id and active_account(session, row.athlete_id) is None:
        IdentityResolver(session, vault).revoke(row.athlete_id)
        row.state, row.payload_encrypted = 'CANCELLED', None
        row.error_code, row.lease_until = 'account_inactive', None
        session.commit()
        return True
    session.refresh(row)
    if row.state != 'SENDING' or row.payload_encrypted is None:
        session.commit()
        return True
    payload = vault.decrypt(row.payload_encrypted, row.key_version)
    if row.athlete_id and IdentityResolver(session, vault).resolve(payload['phone']) != row.athlete_id:
        row.state, row.payload_encrypted = 'CANCELLED', None
        row.error_code, row.lease_until = 'identity_revoked', None
        session.commit()
        return True
    from .provider import ProviderError
    from ..services.consumption_limits import reserve_send
    from fastapi import HTTPException
    try:
        reserve_send(session, row)
    except HTTPException:
        row.state, row.error_code, row.lease_until = 'FAILED', 'consumption_rejected', None
        session.commit()
        return True
    try:
        identifier = provider.send(payload['phone'], payload['text'], payload.get('actions'))
    except ProviderError as error:
        row.state = 'UNCERTAIN' if error.uncertain else 'RETRY' if error.safe_retry and row.attempts < 5 else 'FAILED'
        row.error_code = error.code
        row.next_attempt_at = now() + timedelta(seconds=min(300, 10 * 2 ** row.attempts))
    except Exception:
        row.state, row.error_code = 'UNCERTAIN', 'send_result_unknown'
    else:
        row.state, row.provider_message_id, row.error_code = 'SENT', identifier, None
        rate = os.getenv('WHATSAPP_OUTBOUND_UNIT_COST_USD')
        try:
            cost = Decimal(rate) if rate else None
            if cost is not None and (not cost.is_finite() or cost < 0):
                cost = None
        except InvalidOperation:
            cost = None
        usage(session, f'outbound:{row.id}', 'outbound', row.athlete_id,
              cost=cost)
    from ..services.consumption_limits import settle_send
    settle_send(row, 'CONFIRMED' if row.state == 'SENT' else 'UNCERTAIN')
    row.lease_until = None
    session.commit()
    return True
