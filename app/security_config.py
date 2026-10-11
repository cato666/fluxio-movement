"""Startup policy shared by web, seed and worker; errors never include values."""
import base64
import json
import os
from urllib.parse import unquote, urlsplit


class SecurityConfigurationError(RuntimeError):
    pass


def reject(name):
    raise SecurityConfigurationError(f"Invalid security configuration: {name}") from None


def environment():
    value = os.getenv('APP_ENV', 'development').strip().lower()
    if value not in {'development', 'test', 'production'}:
        reject('APP_ENV')
    return value


def flag(name, default=False):
    value = os.getenv(name, str(default)).strip().lower()
    if value not in {'true', 'false'}:
        reject(name)
    return value == 'true'


def unsafe(value):
    lowered = value.lower()
    return (not value.strip() or lowered in {'movement', 'password', 'demo1234', 'fixture-key'}
            or any(word in lowered for word in ('change', 'replace', 'your-', 'your_',
                                               'development', 'your-secret', 'your-api-key', 'changeme', 'placeholder',
                                               'example', 'insecure', 'demo', 'default', 'password', 'fixture', 'sk-test')))


def secret(name):
    value = os.getenv(name, '')
    if unsafe(value) or len(value) < 32 or len(set(value)) < 8:
        reject(name)
    return value


def session_secret():
    if environment() == 'production':
        return secret('SESSION_SECRET')
    return os.getenv('SESSION_SECRET') or 'local-development-change-me'


def demo_seed_enabled():
    enabled = flag('ENABLE_DEMO_SEED')
    if enabled and os.getenv('APP_ENV', '').strip().lower() != 'development':
        reject('ENABLE_DEMO_SEED')
    if enabled and not os.getenv('DEMO_PASSWORD', '').strip():
        reject('DEMO_PASSWORD')
    return enabled


def decoded_key(name, value):
    try:
        raw = base64.b64decode(value.encode('ascii'), altchars=b'-_', validate=True)
    except Exception:
        reject(name)
    if len(raw) < 32 or len(set(raw)) < 8:
        reject(name)
    return raw


def validate_security():
    env = environment()
    demo_seed_enabled()
    if env != 'production':
        return
    session_secret()
    if os.getenv('DEMO_PASSWORD', ''):
        reject('DEMO_PASSWORD')
    try:
        url = urlsplit(os.getenv('DATABASE_URL', ''))
        valid_database = url.scheme in {'postgresql', 'postgresql+psycopg'} and url.hostname and url.username and url.password and url.path.strip('/')
        valid_database = valid_database and (url.port is None or 0 < url.port < 65536)
    except Exception:
        reject('DATABASE_URL')
    if not valid_database or unsafe(unquote(url.password)) or len(unquote(url.password)) < 16:
        reject('DATABASE_URL')
    database_password = os.getenv('POSTGRES_PASSWORD')
    if database_password is not None and (unsafe(database_password) or len(database_password) < 16):
        reject('POSTGRES_PASSWORD')
    # API keys are provider-issued opaque credentials, not locally generated secrets.
    ai_enabled = [flag(name, True) for name in ('AI_REASONING_ENABLED', 'TRAINING_AI_ENABLED', 'TRAINING_VOICE_ENABLED')]
    if any(ai_enabled):
        if unsafe(os.getenv('OPENAI_API_KEY', '')):
            reject('OPENAI_API_KEY')
    if not flag('WHATSAPP_ENABLED'):
        return
    if os.getenv('WHATSAPP_PROVIDER', 'kapso') != 'kapso':
        reject('WHATSAPP_PROVIDER')
    if unsafe(os.getenv('KAPSO_API_KEY', '')):
        reject('KAPSO_API_KEY')
    if not os.getenv('KAPSO_PHONE_NUMBER_ID', '').strip():
        reject('KAPSO_PHONE_NUMBER_ID')
    secret('KAPSO_WEBHOOK_SECRET')
    lookup = decoded_key('PHONE_HASH_KEY', os.getenv('PHONE_HASH_KEY', ''))
    try:
        keys = json.loads(os.getenv('WHATSAPP_ENCRYPTION_KEYS', '{}'))
        if not isinstance(keys, dict):
            reject('WHATSAPP_ENCRYPTION_KEYS')
        version = os.getenv('WHATSAPP_KEY_VERSION', '1')
        single = os.getenv('WHATSAPP_ENCRYPTION_KEY', '')
        if single:
            keys[version] = single
        if version not in keys:
            reject('WHATSAPP_ENCRYPTION_KEYS')
        from cryptography.fernet import Fernet
        for key in keys.values():
            raw = decoded_key('WHATSAPP_ENCRYPTION_KEYS', key)
            Fernet(key.encode('ascii'))
            if raw == lookup:
                reject('PHONE_HASH_KEY')
    except SecurityConfigurationError:
        raise
    except Exception:
        reject('WHATSAPP_ENCRYPTION_KEYS')


if __name__ == '__main__':
    try:
        validate_security()
    except SecurityConfigurationError as exc:
        raise SystemExit(str(exc)) from None
