from datetime import datetime, timezone
import hashlib
import hmac
import json
from uuid import uuid4
from cryptography.fernet import Fernet
from app.whatsapp.provider import DownloadedMedia

PHONE = '+56911112222'


def configure(monkeypatch):
    monkeypatch.setenv('WHATSAPP_ENABLED', 'true')
    monkeypatch.setenv('WHATSAPP_ENCRYPTION_KEY', Fernet.generate_key().decode())
    monkeypatch.setenv('PHONE_HASH_KEY', Fernet.generate_key().decode())
    monkeypatch.setenv('KAPSO_API_KEY', 'fixture-key')
    monkeypatch.setenv('KAPSO_WEBHOOK_SECRET', 'fixture-secret')
    monkeypatch.setenv('KAPSO_PHONE_NUMBER_ID', 'fixture-number')


def payload(text='ayuda', *, identifier=None, kind='text', phone=PHONE, event='received', action=None):
    message = {'id': identifier or 'wamid.' + uuid4().hex, 'timestamp': str(int(datetime.now(timezone.utc).timestamp())),
        'type': kind, 'kapso': {'direction': 'inbound' if event == 'received' else 'outbound', 'status': event}}
    if phone:
        message['from' if event == 'received' else 'to'] = phone.lstrip('+')
    if kind == 'text':
        message['text'] = {'body': text}
    elif kind in {'audio', 'image', 'video'}:
        message[kind] = {'id': 'media-fixture', 'mime_type': {'image':'image/png', 'audio':'audio/ogg', 'video':'video/mp4'}[kind]}
        if text:
            message[kind]['caption'] = text
    elif kind == 'interactive':
        message['interactive'] = {'type': 'button_reply', 'button_reply': {'id': action, 'title': 'Guardar'}}
    return {'phone_number_id':'fixture-number', 'message':message, 'conversation':{'contact_name':'PRIVATE NAME'}}


def webhook(client, body, event='received', *, signature=None):
    raw = json.dumps(body, separators=(',', ':')).encode()
    signature = signature or hmac.new(b'fixture-secret', raw, hashlib.sha256).hexdigest()
    return client.post('/webhooks/whatsapp/kapso', content=raw, headers={
        'Content-Type':'application/json', 'X-Webhook-Signature':signature,
        'X-Webhook-Event':'whatsapp.message.' + event})


class FakeProvider:
    def __init__(self):
        self.sent = []
        self.media = DownloadedMedia(b'invalid', 'application/octet-stream')

    def send(self, phone, text, actions=None):
        self.sent.append((phone, text, actions))
        return 'sent.' + str(len(self.sent))

    def download_media(self, reference, max_bytes):
        from app.whatsapp.provider import ProviderError
        if len(self.media.data) > max_bytes:
            raise ProviderError('media_too_large')
        return self.media
