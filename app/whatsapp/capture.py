"""Bounded workout/note state machine. Only TrainingService changes Bitácora."""
from datetime import date, datetime, timedelta
import re
import secrets
import os
from urllib.parse import urlsplit
from uuid import UUID
from zoneinfo import ZoneInfo
from sqlalchemy import select
from ..models import TrainingSession
from ..services.training_contracts import InterpretPayload, SessionPayload, WorkoutDraft
from ..services.training_errors import TrainingError, TrainingInvalid
from ..services.training_service import TrainingService
from .identity import now
from .media import receive
from .models import AthleteIdentity, ConversationState, WhatsAppInbox, WhatsAppMedia
from .provider import ProviderError
from .queue import reply, usage


def sanitize(text):
    text = re.sub(r'\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b', '[dato omitido]', text)
    text = re.sub(r'\+?\b\d{9,15}\b', '[dato omitido]', text)
    return re.sub(r'\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b', '[dato omitido]', text)


MONTHS = {name: index for index, name in enumerate(
    ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
     'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'), 1)}


def stated_date(text, today):
    """Use explicit Spanish calendar dates, never infer a date from WOD durations."""
    lowered = text.casefold()
    match = re.search(r'\b(\d{1,2}) de (' + '|'.join(MONTHS) + r')(?: de(?:l)? (\d{4}))?\b', lowered)
    if match:
        try:
            return date(int(match[3]) if match[3] else today.year, MONTHS[match[2]], int(match[1]))
        except ValueError:
            raise TrainingInvalid('Fecha inválida') from None
    if re.search(r'\bayer\b', lowered):
        return today - timedelta(days=1)
    if re.search(r'\bhoy\b', lowered):
        return today
    return None


def snapshot(state, vault):
    return vault.decrypt(state.payload_minimized, state.key_version) if state.payload_minimized else {}


def transition(state, name, payload, vault):
    state.state = name
    state.version += 1
    state.pending_action = secrets.token_urlsafe(18)
    state.payload_minimized = vault.encrypt(payload)
    state.key_version = vault.version
    state.expires_at = now() + timedelta(hours=24)


def actions(state):
    return [{'id':f'{state.pending_action}:{operation}', 'title':title} for operation, title in
            [('save','Guardar'),('correct','Corregir'),('cancel','Cancelar')]]


def clear(state):
    state.state, state.pending_action, state.payload_minimized = 'IDLE', None, None
    state.version += 1


def respond(session, inbox, message, athlete_id, vault, text, buttons=None):
    reply(session, vault, inbox, message.phone, text, athlete_id=athlete_id, actions=buttons)


def propose(session, inbox, message, athlete_id, state, data, vault):
    transition(state, 'CONFIRM', data, vault)
    if data['kind'] == 'note':
        text = f"Agregar a «{data['title']}» ({data['date']}):\n{data['note']}\n¿Guardar esta nota?"
    else:
        draft = data['draft']
        text = f"Detecté:\nFecha: {date.fromisoformat(data['date']).strftime('%d/%m/%Y')}\n{draft['title']}\n{draft['workout']}"
        if draft.get('result_text'):
            text += '\nResultado: ' + draft['result_text']
        if draft.get('adaptations'):
            text += '\nAdaptaciones: ' + draft['adaptations']
        if draft.get('rpe') is not None:
            text += '\nRPE: ' + str(draft['rpe'])
        if data.get('questions'):
            text += '\nPor confirmar (opcional):'
            text += ''.join('\n• ' + question for question in data['questions'])
            text += '\nPuedes guardar este borrador o usar Corregir para aclarar estos detalles.'
        text += '\n¿Quieres guardarlo?'
    respond(session, inbox, message, athlete_id, vault, text, actions(state))


def interpret(session, inbox, message, athlete_id, state, data, vault):
    # Release conversation row locks before provider accounting commits its attempts.
    # Identity remains serialized by the worker's advisory lock across those commits.
    source = sanitize(data['source'])[:12000]
    service = TrainingService(session, athlete_id)
    raw = service.interpret(InterpretPayload(text=source, image_id=data.get('image_id')))
    draft = WorkoutDraft.model_validate(raw).model_dump()
    if not draft['workout'].strip():
        transition(state, 'CLARIFY', data, vault)
        question = draft['questions'][0] if draft['questions'] else '¿Qué ejercicios, series o rondas hiciste?'
        respond(session, inbox, message, athlete_id, vault, question[:500])
        return
    proposed = SessionPayload(trained_on=data['date'], title=draft['title'].strip() or 'Entrenamiento',
        source_text=source, workout=draft['workout'], result_text=draft['result_text'],
        adaptations=draft['adaptations'], rpe=draft['rpe'], blocks=draft['blocks'], source_image_id=data.get('image_id'))
    data['questions'] = draft['questions']
    data['draft'] = proposed.model_dump(mode='json')
    propose(session, inbox, message, athlete_id, state, data, vault)


def handle_capture(session, inbox, message, athlete_id, vault, provider):
    # Also serialize against web unlink; an old phone must never confirm a new draft.
    identity = session.scalar(select(AthleteIdentity).where(AthleteIdentity.athlete_id == athlete_id,
        AthleteIdentity.phone_hash == vault.phone_hash(message.phone), AthleteIdentity.revoked_at.is_(None)))
    if identity is None:
        return
    state = session.get(ConversationState, (athlete_id, 'whatsapp'))
    if state is None:
        state = ConversationState(athlete_id=athlete_id, channel='whatsapp', state='IDLE',
            key_version=vault.version, expires_at=now() + timedelta(hours=24), version=0)
        session.add(state); session.flush()
    if state.expires_at <= now():
        clear(state)
    newer = session.scalar(select(WhatsAppInbox.id).where(WhatsAppInbox.athlete_id == athlete_id,
        WhatsAppInbox.state == 'DONE', WhatsAppInbox.happened_at > message.happened_at).limit(1))
    if newer:
        respond(session, inbox, message, athlete_id, vault, 'Llegó un mensaje anterior. Usa la propuesta más reciente.')
        return
    text = message.text.strip()
    lowered = text.casefold()
    operation = None
    if message.action_id:
        token, _, operation = message.action_id.partition(':')
        if not state.pending_action or token != state.pending_action:
            respond(session, inbox, message, athlete_id, vault, 'Esta acción ya no está vigente. Usa la propuesta más reciente.')
            return
    elif lowered in {'guardar','corregir','cancelar'}:
        operation = {'guardar':'save','corregir':'correct','cancelar':'cancel'}[lowered]
    if operation == 'cancel':
        clear(state)
        respond(session, inbox, message, athlete_id, vault, 'Cancelado. No guardé cambios en tu bitácora.')
        return
    data = snapshot(state, vault)
    if operation == 'save':
        if state.state != 'CONFIRM':
            respond(session, inbox, message, athlete_id, vault, 'No hay una propuesta vigente para guardar.')
            return
        # Short atomic transaction: identity, exact draft, action, inbox and outbox.
        expected_version, expected_token = state.version, state.pending_action
        identity = session.scalar(select(AthleteIdentity).where(AthleteIdentity.id == identity.id,
            AthleteIdentity.revoked_at.is_(None)).with_for_update())
        state = session.scalar(select(ConversationState).where(ConversationState.athlete_id == athlete_id,
            ConversationState.channel == 'whatsapp').with_for_update().execution_options(populate_existing=True))
        if (identity is None or state.state != 'CONFIRM' or state.expires_at <= now()
                or state.version != expected_version or state.pending_action != expected_token):
            respond(session, inbox, message, athlete_id, vault, 'La vinculación o propuesta ya no está vigente.')
            return
        # Refresh data from the row locked above, never from the button payload.
        data = snapshot(state, vault)
        service = TrainingService(session, athlete_id, commit=False)
        try:
            with session.begin_nested():
                if data['kind'] == 'note':
                    saved = service.add_athlete_note(UUID(data['session_id']), data['note'])
                else:
                    saved = service.create(SessionPayload.model_validate(data['draft']))
                    if data.get('media_id'):
                        media = session.scalar(select(WhatsAppMedia).where(WhatsAppMedia.id == UUID(data['media_id']),
                            WhatsAppMedia.athlete_id == athlete_id).with_for_update())
                        if media is None:
                            raise TrainingInvalid('Media no disponible')
                        media.training_session_id, media.expires_at = saved['id'], None
        except TrainingError as error:
            respond(session, inbox, message, athlete_id, vault, str(error))
            return
        clear(state)
        respond(session, inbox, message, athlete_id, vault, 'Nota guardada en tu bitácora.' if data['kind'] == 'note' else 'Entrenamiento guardado en tu bitácora.')
        return
    if operation == 'correct':
        if state.state != 'CONFIRM':
            respond(session, inbox, message, athlete_id, vault, 'No hay una propuesta vigente para corregir.')
            return
        transition(state, 'CORRECT', data, vault)
        respond(session, inbox, message, athlete_id, vault, '¿Qué dato quieres corregir? Indica el cambio concreto.')
        return
    if operation and operation.startswith('choose') and state.state == 'SELECT_NOTE':
        try:
            index = int(operation.removeprefix('choose'))
            if not 0 <= index < len(data['choices']):
                raise IndexError()
            choice = data['choices'][index]
        except (ValueError, IndexError):
            respond(session, inbox, message, athlete_id, vault, 'Elige uno de los entrenamientos propuestos.')
            return
        propose(session, inbox, message, athlete_id, state,
            {'kind':'note', 'note':data['note'], **choice}, vault)
        return
    if operation:
        respond(session, inbox, message, athlete_id, vault, 'Acción no disponible.')
        return
    if state.state == 'CONFIRM':
        respond(session, inbox, message, athlete_id, vault, 'Guarda, corrige o cancela la propuesta pendiente.', actions(state))
        return
    if lowered in {'ayuda','help','hola','menu','menú'}:
        respond(session, inbox, message, athlete_id, vault, 'Puedes registrar un entrenamiento por texto, foto o audio, agregar una nota y abrir tu bitácora en Fluxio. Escribe «resumen semana», «resumen semana pasada», «compartir semana» o «revocar semana».')
        return
    if lowered == 'resumen semanal':
        lowered = 'resumen semana'
    if re.fullmatch(r'(?:resumen(?: de)?|ver|cómo va(?: mi)?|como va(?: mi)?|compartir|revocar)(?: la| mi)? semana(?: pasada| anterior)?', lowered):
        from ..services.weekly_summary import WeeklySummaryService, week_start, summary_text
        weekly = WeeklySummaryService(session, athlete_id, commit=False)
        day = week_start()
        if lowered.endswith(('pasada', 'anterior')):
            day -= timedelta(days=7)
        if lowered.startswith('compartir'):
            base = os.getenv('PUBLIC_BASE_URL', '').rstrip('/')
            parsed = urlsplit(base)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
                respond(session, inbox, message, athlete_id, vault, 'No se pudo crear el enlace por WhatsApp. Puedes compartir tu semana desde la Bitácora web.')
                return
            share = weekly.create_share(day)
            expires = datetime.fromisoformat(share['expires_at']).astimezone(ZoneInfo('America/Santiago')).strftime('%d/%m/%Y %H:%M')
            respond(session, inbox, message, athlete_id, vault,
                'Semana compartida: ' + base + share['path'] + '\nVence: ' + expires + ' (Santiago)' +
                '\nQuien tenga el enlace puede ver entrenamientos, resultados, notas, esfuerzo y fotos. Se actualiza con los cambios de esta semana, incluidas las nuevas fotos. Escribe «revocar semana»' +
                (' pasada' if day < week_start() else '') + ' para desactivar sus enlaces.')
        elif lowered.startswith('revocar'):
            weekly.revoke_week(day)
            respond(session, inbox, message, athlete_id, vault, 'Enlaces de esa semana revocados.')
        else:
            respond(session, inbox, message, athlete_id, vault, summary_text(weekly.summary(day)))
        return
    if state.state == 'SELECT_NOTE':
        respond(session, inbox, message, athlete_id, vault, 'Selecciona un entrenamiento o escribe cancelar.')
        return
    if state.state == 'CORRECT' and data.get('kind') == 'note':
        if not text:
            respond(session, inbox, message, athlete_id, vault, 'Escribe el texto completo de la nota corregida.')
            return
        data['note'] = text[:4000]
        propose(session, inbox, message, athlete_id, state, data, vault)
        return
    if state.state == 'IDLE' and re.match(r'^(agrega|añade|nota\b)', lowered):
        note = re.sub(r'^(?:agrega|añade|nota)\s*(?:que\s*)?', '', text, flags=re.I).strip()
        if not note or len(note) > 4000:
            respond(session, inbox, message, athlete_id, vault, '¿Qué nota quieres agregar? Escribe hasta 4000 caracteres.')
            return
        sessions = TrainingService(session, athlete_id).list_sessions()
        today = now().astimezone(ZoneInfo('America/Santiago')).date()
        recent = [s for s in sessions if today - timedelta(days=7) <= s['trained_on'] <= today]
        if not recent:
            respond(session, inbox, message, athlete_id, vault, 'No encontré un entrenamiento reciente. Registra uno en Fluxio primero.')
            return
        candidates = [s for s in recent if s['trained_on'] == recent[0]['trained_on']]
        if len(candidates) > 3:
            respond(session, inbox, message, athlete_id, vault, 'Hay más de tres entrenamientos recientes. Agrega esta nota desde tu bitácora en Fluxio para elegir el correcto.')
            return
        choices = [{'session_id':str(s['id']), 'title':s['title'], 'date':s['trained_on'].isoformat()} for s in candidates]
        if len(choices) == 1:
            propose(session, inbox, message, athlete_id, state, {'kind':'note','note':note,**choices[0]}, vault)
        else:
            transition(state, 'SELECT_NOTE', {'kind':'note','note':note,'choices':choices}, vault)
            buttons = [{'id':f'{state.pending_action}:choose{i}', 'title':f'Entrenamiento {i+1}'} for i in range(len(choices))]
            description = '\n'.join(f"{i+1}. {c['title']} ({c['date']})" for i,c in enumerate(choices))
            respond(session, inbox, message, athlete_id, vault, '¿A cuál entrenamiento agrego la nota?\n'+description, buttons)
        return
    if state.state == 'IDLE':
        if message.message_type not in {'image','audio','video'} and not re.search(r'\b(hice|entren|wod|amrap|emom|rondas|series|reps|minutos|sentadilla|thruster|remo)\w*', lowered):
            respond(session, inbox, message, athlete_id, vault, 'Escribe qué entrenamiento hiciste, envía una foto o audio, o escribe ayuda.')
            return
        day = now().astimezone(ZoneInfo('America/Santiago')).date()
        if re.search(r'\bayer\b', lowered):
            day -= timedelta(days=1)
        data = {'kind':'workout', 'source':'', 'date':day.isoformat()}
    try:
        if message.message_type in {'image','audio','video'}:
            media, image_id, transcript = receive(session, inbox, message, athlete_id, provider)
            usage(session, f'media:{inbox.id}', 'media', athlete_id)
            if media:
                data['media_id'] = str(media.id)
            if image_id:
                data['image_id'] = str(image_id)
            if transcript:
                text = transcript
            if message.message_type == 'video':
                data['source'] = sanitize(text)
                transition(state, 'CONTEXT', data, vault)
                respond(session, inbox, message, athlete_id, vault, 'Recibí tu video. Cuéntame brevemente qué entrenamiento hiciste o envíame una nota de voz.')
                return
        if text and data.get('kind') == 'workout':
            explicit_day = stated_date(text, now().astimezone(ZoneInfo('America/Santiago')).date())
            if explicit_day:
                data['date'] = explicit_day.isoformat()
        if text:
            data['source'] = (data.get('source','') + '\nAclaración o corrección: ' + sanitize(text)).strip()[:12000]
        if not data.get('source') and not data.get('image_id'):
            transition(state, 'CLARIFY', data, vault)
            respond(session, inbox, message, athlete_id, vault, '¿Qué entrenamiento hiciste? Indica ejercicios y series o rondas.')
            return
        interpret(session, inbox, message, athlete_id, state, data, vault)
    except (TrainingError, ProviderError, ValueError):
        # Roll back only the pending proposal; durable media/usage attempts remain.
        session.rollback()
        state = session.get(ConversationState, (athlete_id, 'whatsapp'))
        if state:
            transition(state, 'CLARIFY', data, vault)
        respond(session, inbox, message, athlete_id, vault, 'No pude interpretar ese contenido. Envía una descripción concreta o escribe cancelar.')
