"""Bounded, database-backed login admission; no credentials or raw identifiers stored."""
import hashlib
import hmac
import logging
import math
import os

from fastapi import HTTPException
from sqlalchemy import text
from ..database import SessionLocal
from ..models import AdminSetting
from ..security_config import session_secret, reject

logger = logging.getLogger(__name__)
KEY = 'login_admission'
LOCK = 70720261011
MAX_BUCKETS = 4096


def policy():
    values = []
    for name, default in [('LOGIN_WINDOW_SECONDS', 300), ('LOGIN_ACCOUNT_LIMIT', 5), ('LOGIN_PEER_LIMIT', 20)]:
        try:
            value = int(os.getenv(name, str(default)))
            if not 1 <= value <= (3600 if name == 'LOGIN_WINDOW_SECONDS' else 1000):
                raise ValueError
        except ValueError:
            reject(name)
        values.append(value)
    return tuple(values)


def _clock(session):
    # One database clock for every worker, read only after acquiring admission lock.
    return float(session.scalar(text('SELECT EXTRACT(EPOCH FROM clock_timestamp())')))


def admit(kind, identifier):
    window, account_limit, peer_limit = policy()
    allowed = False
    # Independent commit: invalid credentials and endpoint rollback cannot refund attempts.
    with SessionLocal.begin() as session:
        session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': LOCK})
        now = _clock(session)
        epoch = math.floor(now / window)
        row = session.get(AdminSetting, KEY)
        state = row.value if row else {}
        if state.get('window') == window:
            epoch = max(epoch, state.get('epoch', epoch))
        digest = hmac.new(session_secret().encode(), (str(epoch) + ':' + kind + ':' + identifier).encode(), hashlib.sha256).hexdigest()
        buckets = dict(state.get('buckets', {})) if state.get('epoch') == epoch and state.get('window') == window else {}
        count = buckets.get(digest, 0)
        limit = account_limit if kind == 'account' else peer_limit
        if count < limit and (digest in buckets or len(buckets) < MAX_BUCKETS):
            buckets[digest] = count + 1
            allowed = True
        value = {'epoch': epoch, 'window': window, 'buckets': buckets}
        if row is None:
            session.add(AdminSetting(key=KEY, value=value))
        else:
            row.value = value
    if not allowed:
        logger.warning('security_rejection reason=login_rate_limit')
        # Window-based, never account existence or remaining-account-budget dependent.
        raise HTTPException(429, 'Demasiados intentos. Intenta más tarde.', headers={'Retry-After': str(max(1, math.ceil((epoch + 1) * window - now)))})
