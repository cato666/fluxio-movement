"""Authenticated encryption and keyed lookup. No sensitive value is loggable."""
import base64
import hashlib
import hmac
import json
import os
import re
from cryptography.fernet import Fernet


class ChannelError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def enabled():
    return os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true'


def normalize_phone(phone):
    if not isinstance(phone, str) or not re.fullmatch(r'\+?[1-9][0-9]{7,14}', phone):
        raise ChannelError('invalid_identity')
    return '+' + phone.lstrip('+')


class Vault:
    def __init__(self):
        self.version = os.getenv('WHATSAPP_KEY_VERSION', '1')
        try:
            keys = json.loads(os.getenv('WHATSAPP_ENCRYPTION_KEYS', '{}'))
            if os.getenv('WHATSAPP_ENCRYPTION_KEY'):
                keys[self.version] = os.environ['WHATSAPP_ENCRYPTION_KEY']
            self.keys = {version: Fernet(key.encode()) for version, key in keys.items()}
            self.lookup_key = base64.urlsafe_b64decode(os.environ['PHONE_HASH_KEY'])
            if self.version not in self.keys or len(self.lookup_key) < 32:
                raise ValueError()
        except Exception:
            raise ChannelError('channel_not_configured') from None

    def encrypt(self, value):
        return self.keys[self.version].encrypt(json.dumps(value, ensure_ascii=False).encode()).decode()

    def decrypt(self, value, version):
        try:
            return json.loads(self.keys[version].decrypt(value.encode()))
        except Exception:
            raise ChannelError('protected_payload_invalid') from None

    def phone_hash(self, phone):
        return hmac.new(self.lookup_key, normalize_phone(phone).encode(), hashlib.sha256).hexdigest()


def code_hash(code):
    return hashlib.sha256(code.encode()).hexdigest()
