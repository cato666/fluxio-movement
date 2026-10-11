"""Minimal admin-only delivery signals and individually audited credit recovery."""
import logging
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StrictBool, ConfigDict
from sqlalchemy import select, text, func
from sqlalchemy.orm import Session
from ..database import get_session
from ..models import AdminSetting, AdminAudit, User
from .identity import now, active_account, IdentityResolver
from .models import WhatsAppOutbox
from .security import Vault, ChannelError

LOCK = 80820261011
CREDIT_KEY = 'whatsapp_credit_block'
logger = logging.getLogger(__name__)


def lock(session):
    session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': LOCK})


def credit_status(session):
    row = session.get(AdminSetting, CREDIT_KEY, populate_existing=True)
    return row.value if row else {'blocked': False}


def block_credit(session):
    value = {'blocked': True, 'block_id': str(uuid4()), 'blocked_at': now().isoformat()}
    row = session.get(AdminSetting, CREDIT_KEY)
    if row:
        row.value = value
    else:
        session.add(AdminSetting(key=CREDIT_KEY, value=value))
    logger.error('whatsapp_credit_blocked reason=insufficient_credits')


def authorize(session, actor):
    current = session.scalar(select(User).where(User.id == actor.id).with_for_update(key_share=True).execution_options(populate_existing=True))
    if current is None or not current.is_active or current.role != 'SYSTEM_ADMIN':
        raise HTTPException(403, 'Operación no autorizada')
    return current


class ClearancePayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    evidence_reference: UUID
    balance_verified: StrictBool


class RecoveryPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: UUID
    clearance_id: UUID
    evidence_reference: UUID
    rejection_verified: StrictBool


def replay(session, actor, action, target, request_id, evidence_reference):
    record = session.scalar(select(AdminAudit).where(AdminAudit.action == action,
        AdminAudit.changes['request_id'].astext == str(request_id)))
    if record and (record.actor_id != actor.id or record.target != str(target) or record.changes.get('evidence_reference') != str(evidence_reference)):
        raise HTTPException(409, 'Identificador de autorización ya utilizado')
    return record


def clear_credit(session, actor, payload):
    lock(session)
    actor = authorize(session, actor)
    if payload.balance_verified is not True:
        raise HTTPException(422, 'Verifica el saldo antes de autorizar')
    previous = replay(session, actor, 'WHATSAPP_CREDIT_CLEAR', CREDIT_KEY, payload.request_id, payload.evidence_reference)
    if previous:
        identifier = previous.id
        session.commit()
        return {'clearance_id': identifier, 'already_authorized': True}
    value = credit_status(session)
    if not value.get('blocked'):
        raise HTTPException(409, 'No existe un bloqueo de crédito que autorizar')
    identifier = uuid4()
    session.add(AdminAudit(id=identifier, actor_id=actor.id, action='WHATSAPP_CREDIT_CLEAR', target=CREDIT_KEY,
        changes={'request_id': str(payload.request_id), 'evidence_reference': str(payload.evidence_reference),
                 'block_id': value['block_id'], 'balance_verified': True}))
    session.get(AdminSetting, CREDIT_KEY).value = {**value, 'blocked': False, 'clearance_id': str(identifier)}
    session.commit()
    logger.info('whatsapp_credit_clearance authorized=true')
    return {'clearance_id': identifier, 'already_authorized': False}


def recover(session, actor, identifier, payload):
    lock(session)
    actor = authorize(session, actor)
    if payload.rejection_verified is not True:
        raise HTTPException(422, 'Verifica el rechazo sin envío antes de autorizar')
    previous = replay(session, actor, 'WHATSAPP_RECOVERY', identifier, payload.request_id, payload.evidence_reference)
    if previous:
        if previous.changes.get('clearance_id') != str(payload.clearance_id):
            raise HTTPException(409, 'Identificador de autorización ya utilizado')
        session.commit()
        return {'id': identifier, 'already_authorized': True}
    credit = credit_status(session)
    if credit.get('blocked') or credit.get('clearance_id') != str(payload.clearance_id):
        raise HTTPException(409, 'Requiere verificación vigente del saldo')
    candidate = session.get(WhatsAppOutbox, identifier)
    if candidate is None:
        raise HTTPException(404, 'Mensaje no disponible')
    # User before outbox: same order as administrative deactivation and dispatch.
    if not candidate.athlete_id or active_account(session, candidate.athlete_id) is None:
        raise HTTPException(409, 'Destinatario no disponible')
    row = session.scalar(select(WhatsAppOutbox).where(WhatsAppOutbox.id == identifier).with_for_update().execution_options(populate_existing=True))
    if row is None:
        raise HTTPException(404, 'Mensaje no disponible')
    if row.state != 'FAILED' or row.error_code != 'insufficient_credits' or row.provider_message_id or row.expires_at <= now() or not row.payload_encrypted:
        raise HTTPException(409, 'No existe evidencia suficiente para un reenvío seguro')
    try:
        vault = Vault()
        protected = vault.decrypt(row.payload_encrypted, row.key_version)
        if not isinstance(protected, dict) or not isinstance(protected.get('phone'), str) or not isinstance(protected.get('text'), str):
            raise ChannelError('protected_payload_invalid')
        if IdentityResolver(session, vault).resolve(protected['phone']) != row.athlete_id:
            raise ChannelError('identity_revoked')
    except (ChannelError, KeyError):
        raise HTTPException(409, 'Destinatario no disponible') from None
    session.add(AdminAudit(actor_id=actor.id, action='WHATSAPP_RECOVERY', target=str(row.id), changes={
        'request_id': str(payload.request_id), 'evidence_reference': str(payload.evidence_reference),
        'clearance_id': str(payload.clearance_id), 'from_state': row.state, 'attempts': row.attempts,
        'rejection_verified': True}))
    # Same outbox/dedupe/payload/expiry; no inbox replay or new conversation.
    row.state, row.error_code, row.lease_until = 'RETRY', 'manual_recovery_authorized', None
    row.next_attempt_at = now()
    session.commit()
    logger.info('whatsapp_recovery authorized=true')
    return {'id': identifier, 'already_authorized': False}


def summary(session):
    credit = credit_status(session)
    counts = dict(session.execute(select(WhatsAppOutbox.state, func.count()).group_by(WhatsAppOutbox.state)).all())
    return {'credit_blocked': bool(credit.get('blocked')), 'blocked_at': credit.get('blocked_at'),
            'clearance_id': credit.get('clearance_id'), 'states': counts}


def router(require_admin):
    routes = APIRouter()
    @routes.get('/api/admin/whatsapp/operations')
    def status(_actor=Depends(require_admin), session: Session = Depends(get_session)):
        rows = session.scalars(select(WhatsAppOutbox).where(WhatsAppOutbox.state.in_(('FAILED','UNCERTAIN','PENDING','RETRY','SENDING')))
            .order_by(WhatsAppOutbox.created_at, WhatsAppOutbox.dedupe_key).limit(100)).all()
        return summary(session) | {'outbox': [{'id': row.id, 'state': row.state, 'error_code': row.error_code,
            'attempts': row.attempts, 'expires_at': row.expires_at, 'payload_available': row.payload_encrypted is not None,
            'next_attempt_at': row.next_attempt_at} for row in rows]}
    @routes.post('/api/admin/whatsapp/credit-clearances')
    def clearance(payload: ClearancePayload, actor=Depends(require_admin), session: Session = Depends(get_session)):
        return clear_credit(session, actor, payload)
    @routes.post('/api/admin/whatsapp/outbox/{identifier}/recover')
    def recovery(identifier: UUID, payload: RecoveryPayload, actor=Depends(require_admin), session: Session = Depends(get_session)):
        return recover(session, actor, identifier, payload)
    return routes
