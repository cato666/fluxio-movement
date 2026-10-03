"""Run separately: python -m app.whatsapp.worker [--once]. No request tasks."""
from datetime import timedelta
import argparse
import logging
import time
from sqlalchemy import or_, select, text
from sqlalchemy.orm import Session
from ..database import SessionLocal, engine
from ..models import TrainingImage, TrainingSession
from .identity import now
from .kapso import KapsoWhatsAppProvider
from .models import ConversationState, WhatsAppInbox, WhatsAppOutbox, WhatsAppMedia
from .media import private_root
from .provider import InboundWhatsAppMessage
from .queue import dispatch_one
from .security import Vault, enabled
from . import runtime

logger = logging.getLogger(__name__)


def process_one(provider, vault):
    eligible = or_(WhatsAppInbox.state == 'PENDING',
        (WhatsAppInbox.state == 'PROCESSING') & (WhatsAppInbox.lease_until < now()))
    with engine.connect() as connection:
        candidates = connection.execute(select(WhatsAppInbox.id, WhatsAppInbox.peer_hash).where(
            eligible, WhatsAppInbox.next_attempt_at <= now()).order_by(WhatsAppInbox.happened_at,
            WhatsAppInbox.created_at).limit(20)).all()
        connection.commit()
        for identifier, peer_hash in candidates:
            lock_id = int((peer_hash or identifier.hex)[:15], 16)
            locked = connection.scalar(text('SELECT pg_try_advisory_lock(:key)'), {'key': lock_id})
            connection.commit()
            if not locked:
                continue
            try:
                with Session(bind=connection, expire_on_commit=False) as session:
                    row = session.scalar(select(WhatsAppInbox).where(WhatsAppInbox.id == identifier, eligible)
                                         .with_for_update(skip_locked=True))
                    if row is None:
                        continue
                    if row.expires_at <= now() or row.payload_encrypted is None:
                        row.state, row.payload_encrypted = 'EXPIRED', None
                        session.commit()
                        return True
                    row.state, row.lease_until = 'PROCESSING', now() + timedelta(minutes=5)
                    row.attempts += 1
                    session.commit()
                    try:
                        message = InboundWhatsAppMessage(**vault.decrypt(row.payload_encrypted, row.key_version))
                        runtime.handle(session, row, message, vault, provider)
                        row.state, row.processed_at, row.lease_until = 'DONE', now(), None
                        row.payload_encrypted = None
                        session.commit()
                    except Exception:
                        session.rollback()
                        row = session.get(WhatsAppInbox, identifier)
                        row.state = 'PENDING' if row.attempts < 3 else 'FAILED'
                        row.error_code = 'processing_failed'
                        row.lease_until = None
                        row.next_attempt_at = now() + timedelta(seconds=30)
                        session.commit()
                        logger.warning('WhatsApp processing failed; private details suppressed')
                    return True
            finally:
                connection.rollback()
                connection.execute(text('SELECT pg_advisory_unlock(:key)'), {'key': lock_id})
                connection.commit()
    return False


def cleanup(session):
    for row in session.scalars(select(WhatsAppMedia).where(WhatsAppMedia.training_session_id.is_(None),
            WhatsAppMedia.expires_at.is_(None)).with_for_update(skip_locked=True)):
        row.expires_at = now() + timedelta(hours=24)
    for row in session.scalars(select(ConversationState).where(ConversationState.expires_at <= now(),
            ConversationState.state != 'IDLE').with_for_update(skip_locked=True)):
        row.state, row.pending_action, row.payload_minimized = 'IDLE', None, None
        row.version += 1
    for model, field in ((WhatsAppInbox, 'payload_encrypted'), (WhatsAppOutbox, 'payload_encrypted')):
        for row in session.scalars(select(model).where(model.expires_at <= now(), getattr(model, field).is_not(None))
                                  .with_for_update(skip_locked=True)):
            setattr(row, field, None)
            if row.state in {'PENDING', 'RETRY', 'PROCESSING'}:
                row.state = 'EXPIRED'
    for row in session.scalars(select(WhatsAppMedia).where(WhatsAppMedia.expires_at <= now(),
            WhatsAppMedia.training_session_id.is_(None)).with_for_update(skip_locked=True)):
        root = private_root().resolve()
        target = (root / row.path).resolve()
        if not target.is_relative_to(root) or not row.path.startswith(('training-images/', 'original/whatsapp/')):
            continue
        if row.media_type == 'image':
            image = session.scalar(select(TrainingImage).where(TrainingImage.path == target.name,
                TrainingImage.athlete_id == row.athlete_id).with_for_update())
            if image and session.scalar(select(TrainingSession.id).where(TrainingSession.source_image_id == image.id).limit(1)):
                row.expires_at = None
                continue
            if image:
                session.delete(image)
        target.unlink(missing_ok=True)
        session.delete(row)
    session.commit()


def run_once(provider=None, vault=None):
    provider, vault = provider or KapsoWhatsAppProvider(), vault or Vault()
    incoming = process_one(provider, vault)
    with SessionLocal() as session:
        outgoing = dispatch_one(session, provider, vault)
        cleanup(session)
    return incoming or outgoing


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if not enabled():
        raise SystemExit('WhatsApp disabled')
    while True:
        worked = run_once()
        if args.once:
            break
        if not worked:
            time.sleep(1)
