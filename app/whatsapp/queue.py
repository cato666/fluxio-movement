from datetime import timedelta
from decimal import Decimal
import os
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .identity import now
from .models import WhatsAppInbox, WhatsAppOutbox, WhatsAppUsage
from .security import ChannelError


def usage(session, event_key, category, athlete_id=None, units=1, cost=None):
    session.execute(insert(WhatsAppUsage).values(id=uuid4(), athlete_id=athlete_id,
        event_key=event_key, category=category, units=units, cost=cost, currency='USD')
        .on_conflict_do_nothing(index_elements=['event_key']))


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
    return accepted


def reply(session, vault, inbox, phone, text, *, athlete_id=None, actions=None, action='reply'):
    key = f'{inbox.id}:{action}'
    session.execute(insert(WhatsAppOutbox).values(id=uuid4(), athlete_id=athlete_id,
        dedupe_key=key, action=action, payload_encrypted=vault.encrypt({'phone': phone, 'text': text, 'actions': actions}),
        key_version=vault.version, expires_at=now() + timedelta(hours=23))
        .on_conflict_do_nothing(index_elements=['dedupe_key']))


def dispatch_one(session, provider, vault):
    # A stale in-flight send has an unknown outcome and is never replayed blindly.
    for stale in session.scalars(select(WhatsAppOutbox).where(WhatsAppOutbox.state == 'SENDING',
        WhatsAppOutbox.lease_until < now()).with_for_update(skip_locked=True)):
        stale.state, stale.error_code = 'UNCERTAIN', 'send_interrupted'
    row = session.scalar(select(WhatsAppOutbox).where(WhatsAppOutbox.state.in_(('PENDING', 'RETRY')),
        WhatsAppOutbox.next_attempt_at <= now()).order_by(WhatsAppOutbox.created_at)
        .with_for_update(skip_locked=True).limit(1))
    if row is None:
        session.commit()
        return False
    if row.expires_at <= now():
        row.state, row.payload_encrypted = 'EXPIRED', None
        session.commit()
        return True
    payload = vault.decrypt(row.payload_encrypted, row.key_version)
    row.state, row.lease_until = 'SENDING', now() + timedelta(minutes=2)
    row.attempts += 1
    session.commit()
    from .provider import ProviderError
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
        usage(session, f'outbound:{row.id}', 'outbound', row.athlete_id,
              cost=Decimal(rate) if rate else None)
    row.lease_until = None
    session.commit()
    return True
