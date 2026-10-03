from datetime import timedelta
from io import BytesIO
from pathlib import Path
import json
import subprocess
from uuid import uuid4
import pytest
from PIL import Image
from sqlalchemy import select, func
from app.database import SessionLocal
from app.models import TrainingSession, TrainingImage, Athlete, User, TrainingAIUsage
from app.seed import DEMO_ATHLETE_ID
from app.services.training_service import TrainingService
from app.services.training_contracts import SessionPayload
from app.services.training_errors import TrainingInvalid
from app.whatsapp.capture import snapshot
from app.whatsapp.identity import now
from app.whatsapp.models import ConversationState, WhatsAppInbox, WhatsAppMedia, WhatsAppOutbox, WhatsAppUsage
from app.whatsapp.provider import DownloadedMedia
from app.whatsapp.security import Vault
from app.whatsapp.worker import process_one, cleanup
from app.whatsapp.queue import dispatch_one
from tests.whatsapp_helpers import PHONE, FakeProvider, configure, payload, webhook
from tests.test_whatsapp_foundation import link


def draft(**changes):
    return dict(title='WOD', workout='4 rondas: remo y thruster', result_text='12:00',
        adaptations=None, rpe=None, blocks=[], questions=[], **changes)


@pytest.fixture
def channel(monkeypatch, session, tmp_path):
    configure(monkeypatch)
    monkeypatch.setenv('STORAGE_PATH', str(tmp_path))
    link(session)
    calls = []
    def interpreter(text, image=None):
        calls.append((text, image))
        return draft()
    monkeypatch.setattr('app.services.training_service.interpret', interpreter)
    return FakeProvider(), calls


def step(client, channel, text='Hoy hice 4 rondas en 12 minutos', **options):
    provider, _ = channel
    assert webhook(client, payload(text, **options)).status_code == 200
    assert process_one(provider, Vault())


def state(session):
    session.expire_all()
    return session.get(ConversationState, (DEMO_ATHLETE_ID, 'whatsapp'))


def count(session):
    session.expire_all()
    return session.scalar(select(func.count()).select_from(TrainingSession))


def button(session, operation):
    return state(session).pending_action + ':' + operation


def confirm(client, channel, session, operation='save'):
    step(client, channel, '', kind='interactive', action=button(session, operation))


def own_session(session, title='WOD'):
    return TrainingService(session, DEMO_ATHLETE_ID).create(SessionPayload(
        trained_on=now().astimezone(__import__('zoneinfo').ZoneInfo('America/Santiago')).date(),
        title=title, workout='4 rondas', adaptations='Escalado: 20 kg'))


def test_text_confirm_exact_draft_double_action_and_duplicate(client, channel, session):
    initial = count(session)
    step(client, channel)
    assert count(session) == initial
    proposed = snapshot(state(session), Vault())['draft']
    action = button(session, 'save')
    step(client, channel, '', kind='interactive', action=action, identifier='wamid.confirm')
    step(client, channel, '', kind='interactive', action=action)
    assert webhook(client, payload('', kind='interactive', action=action, identifier='wamid.confirm')).json()['accepted'] == 0
    assert count(session) == initial + 1
    row = session.scalar(select(TrainingSession).order_by(TrainingSession.created_at.desc()))
    assert row.workout == proposed['workout'] and row.result_text == proposed['result_text']


def test_correction_reproposes_cancel_and_old_button(client, channel, session):
    initial = count(session)
    step(client, channel)
    old = button(session, 'save')
    confirm(client, channel, session, 'correct')
    step(client, channel, 'Fueron 5 rondas')
    assert state(session).state == 'CONFIRM' and '5 rondas' in channel[1][-1][0]
    step(client, channel, '', kind='interactive', action=old)
    assert count(session) == initial
    confirm(client, channel, session, 'cancel')
    assert count(session) == initial and state(session).state == 'IDLE'


@pytest.mark.parametrize('case', ['ambiguous', 'invalid'])
def test_text_asks_one_clarification(client, channel, session, monkeypatch, case):
    def interpreter(*args):
        if case == 'invalid':
            raise ValueError('fixture failure')
        value = draft(); value['workout'] = ''; value['questions'] = ['¿Qué ejercicios hiciste?', '¿Cuántas repeticiones?']
        return value
    monkeypatch.setattr('app.services.training_service.interpret', interpreter)
    initial = count(session)
    step(client, channel)
    assert count(session) == initial
    out = session.scalar(select(WhatsAppOutbox))
    text = Vault().decrypt(out.payload_encrypted, out.key_version)['text']
    assert 'Cuántas repeticiones' not in text


def test_unknown_text_no_ai_and_identity_not_sent(client, channel, session, caplog):
    step(client, channel, 'Buenos días')
    assert not channel[1]
    step(client, channel, 'Hice 4 rondas. Mi teléfono ' + PHONE + ' atleta@example.com')
    sent = channel[1][-1][0]
    assert PHONE not in sent and 'atleta@example.com' not in sent and 'PRIVATE NAME' not in sent
    assert PHONE not in caplog.text and 'fixture-key' not in caplog.text


def test_expired_and_out_of_order_actions(client, channel, session):
    initial = count(session)
    step(client, channel)
    action = button(session, 'save')
    row = state(session); row.expires_at = now() - timedelta(seconds=1); session.commit()
    step(client, channel, '', kind='interactive', action=action)
    assert count(session) == initial
    step(client, channel)
    action = button(session, 'save')
    row = session.scalar(select(WhatsAppInbox).where(WhatsAppInbox.state == 'DONE').order_by(WhatsAppInbox.created_at.desc()))
    row.happened_at = now() + timedelta(seconds=2); session.commit()
    step(client, channel, '', kind='interactive', action=action)
    assert count(session) == initial and state(session).state == 'CONFIRM'


def test_restart_recovers_inbox_draft_and_outbox(client, channel, session):
    initial = count(session)
    assert webhook(client, payload('Hice 4 rondas en 12 minutos')).json()['accepted'] == 1
    row = session.scalar(select(WhatsAppInbox)); row.state = 'PROCESSING'
    row.lease_until = now() - timedelta(seconds=1); session.commit()
    assert process_one(channel[0], Vault())
    # Fresh sessions and fresh provider simulate loss of all process memory.
    with SessionLocal() as fresh:
        assert snapshot(state(fresh), Vault())['draft']
        action = button(fresh, 'save')
    restarted = FakeProvider()
    assert webhook(client, payload('', kind='interactive', action=action)).status_code == 200
    assert process_one(restarted, Vault())
    assert count(session) == initial + 1
    with SessionLocal() as fresh:
        assert dispatch_one(fresh, restarted, Vault())
    assert restarted.sent


def test_save_rollback_preserves_proposal_without_partial_session(client, channel, session):
    initial = count(session)
    step(client, channel)
    row = state(session); data = snapshot(row, Vault()); data['media_id'] = str(uuid4())
    row.payload_minimized = Vault().encrypt(data); session.commit()
    confirm(client, channel, session)
    assert count(session) == initial and state(session).state == 'CONFIRM'


def test_photo_private_valid_and_cleanup(client, channel, session, tmp_path):
    out = BytesIO(); Image.new('RGB', (30, 30), 'white').save(out, 'PNG')
    channel[0].media = DownloadedMedia(out.getvalue(), 'image/png')
    initial = count(session)
    step(client, channel, '', kind='image')
    assert channel[1][-1][1].startswith(b'\xff\xd8') and count(session) == initial
    media = session.scalar(select(WhatsAppMedia)); target = tmp_path / media.path
    assert target.exists() and client.get('/uploads/' + target.name).status_code == 401
    assert client.post('/api/auth/login', json={'username':'gaston','password':'demo1234'}).status_code == 200
    assert client.get('/uploads/' + target.name).status_code == 403
    confirm(client, channel, session)
    session.expire_all(); assert media.training_session_id and media.expires_at is None
    saved = session.get(TrainingSession, media.training_session_id)
    TrainingService(session, DEMO_ATHLETE_ID).delete(saved.id)
    session.expire_all(); assert media.training_session_id is None
    cleanup(session)
    media.expires_at = now() - timedelta(seconds=1); session.commit(); cleanup(session)
    assert not target.exists() and session.scalar(select(TrainingImage)) is None


@pytest.mark.parametrize('media', [DownloadedMedia(b'invalid', 'image/png'),
    DownloadedMedia(b'x' * (8*1024*1024+1), 'image/png'), DownloadedMedia(b'invalid', 'text/html')])
def test_bad_photo_no_persistence(client, channel, session, media):
    channel[0].media = media
    initial = count(session)
    step(client, channel, '', kind='image')
    assert count(session) == initial and session.scalar(select(WhatsAppMedia)) is None


def make_audio(tmp_path, duration=0.2, codec='libopus'):
    target = tmp_path / 'voice.ogg'
    subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440',
        '-t', str(duration), '-c:a', codec, '-y', str(target)], check=True, timeout=25)
    return target.read_bytes()


def mock_transcription(monkeypatch, text='Hice 4 rondas en 12 minutos'):
    from contextlib import contextmanager
    monkeypatch.setenv('OPENAI_API_KEY', 'fixture-openai')
    @contextmanager
    def response(*args, **kwargs):
        yield BytesIO(json.dumps({'text':text}).encode())
    monkeypatch.setattr('app.services.training_transcription.urlopen', response)


def test_ogg_opus_real_decode_transcribe_interpret_confirm(client, channel, session, monkeypatch, tmp_path):
    mock_transcription(monkeypatch)
    channel[0].media = DownloadedMedia(make_audio(tmp_path), 'audio/ogg')
    initial = count(session)
    step(client, channel, '', kind='audio')
    assert state(session).state == 'CONFIRM' and '4 rondas' in channel[1][-1][0]
    assert count(session) == initial
    assert session.scalar(select(TrainingAIUsage)).operation == 'TRANSCRIBE'
    confirm(client, channel, session)
    assert count(session) == initial+1


@pytest.mark.parametrize('case', ['long', 'vorbis', 'provider_error', 'too_large', 'fake_ogg'])
def test_audio_rejections(client, channel, session, monkeypatch, tmp_path, case):
    mock_transcription(monkeypatch, text='')
    data = (make_audio(tmp_path, duration=181) if case == 'long' else
        make_audio(tmp_path, codec='libvorbis') if case == 'vorbis' else
        b'x'*(8*1024*1024+1) if case == 'too_large' else
        b'OggSbroken' if case == 'fake_ogg' else make_audio(tmp_path))
    channel[0].media = DownloadedMedia(data, 'audio/ogg')
    initial = count(session)
    step(client, channel, '', kind='audio')
    assert count(session) == initial and not channel[1]


def test_video_private_storage_context_then_text_no_biomechanics(client, channel, session, tmp_path):
    target = tmp_path/'video.mp4'
    subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=black:s=160x120:d=0.2',
        '-c:v','libx264','-y',str(target)], check=True, timeout=20)
    channel[0].media = DownloadedMedia(target.read_bytes(), 'video/mp4')
    initial = count(session)
    step(client, channel, '', kind='video')
    assert not channel[1] and state(session).state == 'CONTEXT'
    media = session.scalar(select(WhatsAppMedia)); assert (tmp_path/media.path).exists()
    assert client.get('/uploads/whatsapp/'+Path(media.path).name).status_code == 401
    assert client.post('/api/auth/login', json={'username':'gaston','password':'demo1234'}).status_code == 200
    assert client.get('/uploads/whatsapp/'+Path(media.path).name).status_code == 403
    step(client, channel)
    assert state(session).state == 'CONFIRM' and count(session) == initial
    confirm(client, channel, session)
    session.expire_all(); assert media.training_session_id


def test_note_preserves_content_typed_source_and_exactly_once(client, channel, session):
    saved = own_session(session)
    step(client, channel, 'Agrega que la última ronda me costó mucho')
    row = session.get(TrainingSession, saved['id']); session.refresh(row)
    assert row.adaptations == 'Escalado: 20 kg' and not row.athlete_notes
    action = button(session, 'save')
    # A concurrent web edit must be preserved when the note is confirmed.
    row.adaptations += '\nCambio web'; session.commit()
    step(client, channel, '', kind='interactive', action=action)
    step(client, channel, '', kind='interactive', action=action)
    session.refresh(row)
    assert 'Cambio web' in row.adaptations and len(row.athlete_notes) == 1
    assert row.athlete_notes[0]['type'] == 'athlete_note' and row.athlete_notes[0]['source'] == 'whatsapp'


def test_note_ambiguous_selection_and_foreign_athlete_protected(client, channel, session):
    first = own_session(session, 'Primero'); own_session(session, 'Segundo')
    step(client, channel, 'Agrega que estuvo difícil')
    assert state(session).state == 'SELECT_NOTE'
    confirm(client, channel, session, 'choose1')
    assert snapshot(state(session), Vault())['session_id'] == str(first['id'])
    other = User(id=uuid4(), name='Other', role='ATHLETE'); session.add(other); session.flush()
    session.add(Athlete(user_id=other.id)); session.commit()
    foreign = TrainingService(session, other.id).create(SessionPayload(trained_on=now().date(), title='Ajeno', workout='Remo'))
    row = state(session); data = snapshot(row, Vault()); data['session_id'] = str(foreign['id'])
    row.payload_minimized = Vault().encrypt(data); session.commit()
    confirm(client, channel, session)
    row = session.get(TrainingSession, foreign['id']); session.refresh(row)
    assert not row.athlete_notes


def test_media_cancel_expiry_cleanup(client, channel, session, tmp_path):
    out=BytesIO(); Image.new('RGB',(20,20)).save(out,'PNG')
    channel[0].media=DownloadedMedia(out.getvalue(),'image/png')
    step(client, channel, '', kind='image')
    row=session.scalar(select(WhatsAppMedia)); target=tmp_path/row.path
    confirm(client, channel, session, 'cancel')
    row.expires_at=now()-timedelta(seconds=1); session.commit(); cleanup(session)
    assert not target.exists() and session.scalar(select(WhatsAppMedia)) is None


def test_other_phone_cannot_confirm_and_revoked_phone_loses_draft(client, channel, session):
    from app.whatsapp.identity import IdentityResolver
    initial = count(session)
    step(client, channel)
    action = button(session, 'save')
    other = User(id=uuid4(), name='Other', role='ATHLETE'); session.add(other); session.flush()
    session.add(Athlete(user_id=other.id)); session.commit()
    link(session, other.id, '+56922223333')
    step(client, channel, '', kind='interactive', action=action, phone='+56922223333')
    assert count(session) == initial and state(session).state == 'CONFIRM'
    IdentityResolver(session, Vault()).revoke(DEMO_ATHLETE_ID); session.commit()
    step(client, channel, '', kind='interactive', action=action)
    assert count(session) == initial and state(session).state == 'IDLE'


def test_full_webhook_shared_interpretation_outbox_and_web_bitacora(athlete_client, channel, session, monkeypatch):
    from app.services import workout_interpretation
    monkeypatch.setenv('OPENAI_API_KEY', 'fixture-openai')
    requests = []
    def request(body, key):
        requests.append(body)
        return {'model':'fixture-model', 'usage':{'input_tokens':10,'output_tokens':20},
            'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(draft())}]}]}
    monkeypatch.setattr(workout_interpretation, '_request', request)
    monkeypatch.setattr('app.services.training_service.interpret', workout_interpretation.interpret)
    response = athlete_client.get('/api/training-sessions'); assert response.status_code == 200
    before = response.json()['items']
    step(athlete_client, channel)
    assert requests and requests[0]['store'] is False
    with SessionLocal() as fresh:
        assert dispatch_one(fresh, channel[0], Vault())
    assert channel[0].sent[-1][2][0]['title'] == 'Guardar'
    confirm(athlete_client, channel, session)
    after = athlete_client.get('/api/training-sessions').json()['items']
    assert len(after) == len(before)+1 and after[0]['workout'] == draft()['workout']
    usage = session.scalar(select(TrainingAIUsage))
    assert usage.input_tokens == 10 and usage.output_tokens == 20


def test_parallel_workers_serialize_confirmation(client, channel, session):
    from concurrent.futures import ThreadPoolExecutor
    initial=count(session); step(client, channel)
    action=button(session,'save')
    for _ in range(2):
        assert webhook(client, payload('',kind='interactive',action=action)).status_code == 200
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(process_one, FakeProvider(), Vault()) for _ in range(2)]
        for future in futures:
            future.result(timeout=15)
    while process_one(FakeProvider(),Vault()):
        pass
    assert count(session)==initial+1


def test_long_proposal_delivery_order_limit_and_uncertain_hold(client, channel, session, monkeypatch):
    from app.whatsapp.provider import ProviderError
    value=draft(); value['workout']='Remo\n' * 500
    monkeypatch.setattr('app.services.training_service.interpret', lambda *_: value)
    step(client,channel)
    rows=session.scalars(select(WhatsAppOutbox).order_by(WhatsAppOutbox.created_at)).all()
    assert len(rows)==3
    texts=[Vault().decrypt(row.payload_encrypted,row.key_version)['text'] for row in rows]
    assert value['workout'] in ''.join(texts) and all(len(text)<=1024 for text in texts)
    class Uncertain(FakeProvider):
        def send(self,*args,**kwargs):
            raise ProviderError('fixture',uncertain=True)
    assert dispatch_one(session,Uncertain(),Vault())
    assert not dispatch_one(session,channel[0],Vault()) and not channel[0].sent


def test_worker_failure_rolls_back_then_replays_without_lost_or_duplicate_save(client, channel, session, monkeypatch):
    from app.whatsapp import runtime
    initial=count(session); step(client,channel)
    action=button(session,'save')
    assert webhook(client,payload('',kind='interactive',action=action)).status_code == 200
    original=runtime.handle
    def fail_after_handle(*args):
        original(*args)
        raise RuntimeError('fixture private failure')
    monkeypatch.setattr(runtime,'handle',fail_after_handle)
    assert process_one(channel[0],Vault())
    assert count(session)==initial and state(session).state=='CONFIRM'
    row=session.scalar(select(WhatsAppInbox).where(WhatsAppInbox.state=='PENDING'))
    row.next_attempt_at=now(); session.commit()
    monkeypatch.setattr(runtime,'handle',original)
    assert process_one(FakeProvider(),Vault())
    assert count(session)==initial+1


def test_channel_costs_count_accepted_inbound_and_download_bytes(client, channel, session, monkeypatch):
    out=BytesIO(); Image.new('RGB',(20,20)).save(out,'PNG')
    raw=out.getvalue(); channel[0].media=DownloadedMedia(raw,'image/png')
    body=payload('',kind='image'); assert webhook(client,body).status_code==200
    assert webhook(client,body).json()['accepted']==0
    assert process_one(channel[0],Vault())
    session.expire_all()
    inbound=session.scalars(select(WhatsAppUsage).where(WhatsAppUsage.category=='inbound')).all()
    assert len(inbound)==1 and inbound[0].athlete_id==DEMO_ATHLETE_ID
    downloaded=session.scalar(select(WhatsAppUsage).where(WhatsAppUsage.category=='media_bytes'))
    assert downloaded.units==len(raw) and downloaded.cost is None
    monkeypatch.setenv('WHATSAPP_OUTBOUND_UNIT_COST_USD','not-a-rate')
    assert dispatch_one(session,channel[0],Vault())
    assert session.scalar(select(WhatsAppUsage).where(WhatsAppUsage.category=='outbound')).cost is None


def test_optional_questions_propose_without_auto_save_and_correction_keeps_source(client, channel, session, monkeypatch):
    calls = []
    def interpreter(text, image=None):
        calls.append(text)
        value = draft()
        value['questions'] = ['¿Los 8 minutos son un límite total?', '¿Qué abdominales hiciste?']
        return value
    monkeypatch.setattr('app.services.training_service.interpret', interpreter)
    initial = count(session)
    step(client, channel, 'Hoy hice 6 rondas del WOD')
    assert state(session).state == 'CONFIRM' and count(session) == initial
    out = session.scalar(select(WhatsAppOutbox).order_by(WhatsAppOutbox.created_at.desc()))
    reply = Vault().decrypt(out.payload_encrypted, out.key_version)
    assert 'Por confirmar (opcional)' in reply['text']
    assert 'Corregir' in reply['text']
    confirm(client, channel, session, 'correct')
    step(client, channel, 'Solo peso corporal')
    assert state(session).state == 'CONFIRM'
    assert '6 rondas' in calls[-1] and 'peso corporal' in calls[-1]
    assert count(session) == initial
    confirm(client, channel, session)
    assert count(session) == initial + 1


def test_audio_explicit_date_used_in_proposal_and_saved(client, channel, session, monkeypatch, tmp_path):
    mock_transcription(monkeypatch, text='El 2 de octubre de 2026 hice 4 rondas en 12 minutos')
    channel[0].media = DownloadedMedia(make_audio(tmp_path), 'audio/ogg')
    step(client, channel, '', kind='audio')
    proposed = snapshot(state(session), Vault())['draft']
    assert proposed['trained_on'] == '2026-10-02'
    out = session.scalar(select(WhatsAppOutbox).order_by(WhatsAppOutbox.created_at.desc()))
    assert '02/10/2026' in Vault().decrypt(out.payload_encrypted, out.key_version)['text']
    confirm(client, channel, session)
    row = session.scalar(select(TrainingSession).order_by(TrainingSession.created_at.desc()))
    assert row.trained_on.isoformat() == '2026-10-02'


def test_date_correction_preserved_in_next_proposal(client, channel, session):
    step(client, channel)
    confirm(client, channel, session, 'correct')
    step(client, channel, 'Fue el 2 de octubre de 2026')
    assert snapshot(state(session), Vault())['draft']['trained_on'] == '2026-10-02'


@pytest.mark.parametrize('text,expected', [
    ('Fue el 2 de octubre', '2026-10-02'),
    ('Ayer hice 4 rondas', '2026-10-02'),
    ('Hoy hice 4 rondas', '2026-10-03'),
    ('AMRAP 12 minutos, 2 rondas', None),
])
def test_stated_date(text, expected):
    from datetime import date
    from app.whatsapp.capture import stated_date
    result = stated_date(text, date(2026, 10, 3))
    assert (result.isoformat() if result else None) == expected


def test_invalid_explicit_date_not_silently_replaced():
    from datetime import date
    from app.whatsapp.capture import stated_date
    with pytest.raises(TrainingInvalid):
        stated_date('Fue el 31 de febrero', date(2026, 10, 3))
