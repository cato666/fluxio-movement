"""Phase 2 foundation. Only normalized messages reach the conversation runtime."""
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from .identity import IdentityResolver, now
from .models import ConversationState, WhatsAppOutbox, WhatsAppPeer
from .queue import reply, usage

HELP = 'Puedes registrar un entrenamiento, agregar una nota y consultar tu bitácora en Fluxio. La consulta semanal por WhatsApp estará disponible en una fase posterior.'


def handle(session, inbox, message, vault, provider):
    if message.event != 'received':
        row = session.scalar(select(WhatsAppOutbox).where(
            WhatsAppOutbox.provider_message_id == message.provider_message_id).with_for_update())
        if row:
            ranks = {'SENT': 1, 'DELIVERED': 2, 'READ': 3}
            state = message.event.upper()
            if state == 'FAILED' or ranks.get(state, 0) > ranks.get(row.state, 0):
                row.state = state
        return
    if message.phone is None:
        inbox.error_code = 'unresolved_identity'
        return
    resolver = IdentityResolver(session, vault)
    athlete_id = resolver.resolve(message.phone)
    if message.text.upper().startswith('VINCULAR '):
        code = message.text.split(' ', 1)[1].strip()
        athlete_id = resolver.verify(code, message.phone)
        reply(session, vault, inbox, message.phone,
            'WhatsApp vinculado a Fluxio. Escribe ayuda.' if athlete_id else 'No se pudo vincular. Genera un código nuevo desde tu cuenta en Fluxio.',
            athlete_id=athlete_id)
    elif athlete_id is None:
        reply(session, vault, inbox, message.phone, 'Inicia sesión en Fluxio y genera un código de vinculación para usar WhatsApp.')
    else:
        reply(session, vault, inbox, message.phone, HELP, athlete_id=athlete_id)
    inbox.athlete_id = athlete_id
    usage(session, f'inbound:{inbox.id}', 'inbound', athlete_id)
    if athlete_id:
        session.execute(insert(ConversationState).values(athlete_id=athlete_id, channel='whatsapp', state='IDLE',
            key_version=vault.version, expires_at=now() + timedelta(hours=24)).on_conflict_do_nothing())
