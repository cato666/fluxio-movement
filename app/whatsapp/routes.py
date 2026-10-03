from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_session
from ..models import User
from .identity import IdentityResolver
from .kapso import KapsoWhatsAppProvider
from .models import AthleteIdentity
from .queue import accept
from .security import ChannelError, Vault, enabled
import os

BODY_LIMIT = 256 * 1024


def vault_or_error():
    if not enabled():
        raise HTTPException(404, 'Canal no habilitado')
    try:
        return Vault()
    except ChannelError:
        raise HTTPException(503, 'Canal no configurado') from None


def router(require_athlete):
    routes = APIRouter()

    @routes.post('/webhooks/whatsapp/kapso')
    async def webhook(request: Request, session: Session = Depends(get_session)):
        vault = vault_or_error()
        if os.getenv('APP_ENV') == 'production' and request.url.scheme != 'https':
            raise HTTPException(400, 'HTTPS requerido')
        provider = KapsoWhatsAppProvider()
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > BODY_LIMIT:
                raise HTTPException(413, 'Webhook demasiado grande')
        if not provider.verify_webhook(bytes(raw), request.headers.get('X-Webhook-Signature')):
            raise HTTPException(401, 'Firma inválida')
        try:
            messages = provider.normalize(bytes(raw), request.headers.get('X-Webhook-Event', ''))
            count = accept(session, messages, vault)
            session.commit()  # Durable before ACK. No worker or AI is run in this request.
        except ChannelError:
            session.rollback()
            raise HTTPException(400, 'Webhook inválido') from None
        return {'ok': True, 'accepted': count}

    @routes.post('/api/whatsapp/link-challenges', status_code=201)
    def issue_link(user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        vault = vault_or_error()
        try:
            result = IdentityResolver(session, vault).issue(user.id)
            session.commit()
            return result
        except ChannelError:
            session.rollback()
            raise HTTPException(429, 'Espera antes de generar otro código') from None

    @routes.get('/api/whatsapp/identity')
    def identity(user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        vault_or_error()
        row = session.scalar(select(AthleteIdentity).where(AthleteIdentity.athlete_id == user.id,
            AthleteIdentity.revoked_at.is_(None)))
        return {'linked': row is not None, 'verified_at': row.verified_at if row else None}

    @routes.delete('/api/whatsapp/identity')
    def unlink(user: User = Depends(require_athlete), session: Session = Depends(get_session)):
        IdentityResolver(session, vault_or_error()).revoke(user.id)
        session.commit()
        return {'linked': False}

    return routes
