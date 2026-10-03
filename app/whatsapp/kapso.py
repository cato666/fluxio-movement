"""Only Kapso knows provider payloads, credentials, URLs and error details."""
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener
from .provider import DownloadedMedia, InboundWhatsAppMessage, ProviderError
from .security import normalize_phone


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ProviderError('provider_redirect_rejected')


class KapsoWhatsAppProvider:
    name = 'kapso'
    base = 'https://api.kapso.ai/meta/whatsapp/v24.0'

    def __init__(self, *, opener=None):
        if os.getenv('WHATSAPP_PROVIDER', 'kapso') != 'kapso':
            raise ProviderError('unsupported_provider')
        self.key = os.getenv('KAPSO_API_KEY', '')
        self.secret = os.getenv('KAPSO_WEBHOOK_SECRET', '')
        self.number_id = os.getenv('KAPSO_PHONE_NUMBER_ID', '')
        self.opener = opener or build_opener(NoRedirect()).open

    def verify_webhook(self, raw, signature):
        if not self.secret or not isinstance(signature, str) or not re.fullmatch('[0-9a-f]{64}', signature):
            return False
        expected = hmac.new(self.secret.encode(), raw, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def normalize(self, raw, event):
        try:
            data = json.loads(raw)
            batched = data.get('batch') is True
            if batched and data.get('type') != event:
                raise ValueError()
            items = data['data'] if batched else [data]
            if not isinstance(items, list) or len(items) > 100:
                raise ValueError()
            result = []
            status = event.removeprefix('whatsapp.message.')
            if status not in {'received', 'sent', 'delivered', 'read', 'failed'}:
                return []
            for item in items:
                if not self.number_id or item.get('phone_number_id') != self.number_id:
                    raise ValueError()
                message = item['message']
                kapso = message.get('kapso') or {}
                if kapso.get('passive'):
                    continue
                if kapso.get('direction') != ('inbound' if status == 'received' else 'outbound'):
                    raise ValueError()
                # Real Kapso received events can report delivery of the inbound
                # message as delivered. Direction still comes from signed bytes;
                # outbound receipts retain strict status matching.
                allowed_statuses = {'received', 'delivered'} if status == 'received' else {status}
                if kapso.get('status') not in allowed_statuses:
                    raise ValueError()
                identifier = message['id']
                if not isinstance(identifier, str) or not 1 <= len(identifier) <= 200:
                    raise ValueError()
                timestamp = datetime.fromtimestamp(int(message['timestamp']), timezone.utc).isoformat()
                kind = message.get('type', 'unsupported')
                body = (message.get('text') or {}).get('body', '')
                media = message.get(kind) or {}
                interactive = message.get('interactive') or {}
                action = (interactive.get('button_reply') or interactive.get('list_reply') or {}).get('id')
                if kind == 'button':
                    action = (message.get('button') or {}).get('payload')
                phone = message.get('from') if status == 'received' else None
                if phone is not None:
                    phone = normalize_phone(phone)
                if not isinstance(body, str) or len(body) > 12000 or (action and len(action) > 100):
                    raise ValueError()
                reference = media.get('id') if kind in {'image', 'audio', 'video'} else None
                if reference and (not isinstance(reference, str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,160}', reference)):
                    raise ValueError()
                if not body and kind in {'image', 'video'}:
                    body = media.get('caption', '')
                if not isinstance(body, str) or len(body) > 12000:
                    raise ValueError()
                result.append(InboundWhatsAppMessage(identifier, phone, kind, timestamp,
                    body, reference, media.get('mime_type'), action, status))
            return result
        except Exception:
            raise ProviderError('invalid_webhook_payload') from None

    def _read(self, url, *, body=None, authenticated=True, limit=1024 * 1024):
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname != 'api.kapso.ai' or parsed.port not in (None, 443) or parsed.username:
            raise ProviderError('provider_url_rejected')
        if authenticated and not self.key:
            raise ProviderError('provider_not_configured')
        headers = {'Content-Type': 'application/json'}
        if authenticated:
            headers['X-API-Key'] = self.key
        try:
            with self.opener(Request(url, data=body, headers=headers), timeout=30) as response:
                content = response.read(limit + 1)
                if len(content) > limit:
                    raise ProviderError('provider_response_too_large', uncertain=body is not None)
                return content, response.headers.get('Content-Type', '').split(';')[0]
        except ProviderError:
            raise
        except HTTPError as error:
            raise ProviderError('provider_http_error', safe_retry=error.code == 429,
                                uncertain=body is not None and error.code >= 500) from None
        except URLError as error:
            raise ProviderError('provider_transport_error', safe_retry=isinstance(error.reason, socket.gaierror),
                                uncertain=body is not None and not isinstance(error.reason, socket.gaierror)) from None
        except Exception:
            raise ProviderError('provider_transport_error', uncertain=body is not None) from None

    def send(self, phone, text, actions=None):
        if not self.number_id:
            raise ProviderError('provider_not_configured')
        payload = {'messaging_product': 'whatsapp', 'recipient_type': 'individual', 'to': normalize_phone(phone)[1:]}
        if actions:
            if len(actions) > 3:
                raise ProviderError('invalid_outbound_actions')
            payload.update(type='interactive', interactive={'type': 'button', 'body': {'text': text},
                'action': {'buttons': [{'type': 'reply', 'reply': {'id': a['id'], 'title': a['title']}} for a in actions]}})
        else:
            payload.update(type='text', text={'body': text, 'preview_url': False})
        raw, _ = self._read(f'{self.base}/{quote(self.number_id, safe="")}/messages', body=json.dumps(payload).encode())
        try:
            identifier = json.loads(raw)['messages'][0]['id']
            if not isinstance(identifier, str) or not 1 <= len(identifier) <= 240:
                raise ValueError()
            return identifier
        except Exception:
            raise ProviderError('provider_send_result_uncertain', uncertain=True) from None

    def download_media(self, reference, max_bytes):
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,160}', reference):
            raise ProviderError('invalid_media_reference')
        if not self.number_id:
            raise ProviderError('provider_not_configured')
        raw, _ = self._read(f'{self.base}/{quote(reference, safe="")}?phone_number_id={quote(self.number_id, safe="")}')
        try:
            info = json.loads(raw)
            url = info['download_url']
            if urlsplit(url).path != '/meta/whatsapp/media_download':
                raise ValueError()
            if int(info.get('file_size', 0)) > max_bytes:
                raise ProviderError('media_too_large')
        except ProviderError:
            raise
        except Exception:
            raise ProviderError('invalid_media_metadata') from None
        raw, mime = self._read(url, authenticated=False, limit=max_bytes)
        return DownloadedMedia(raw, mime or info.get('mime_type', 'application/octet-stream'))
