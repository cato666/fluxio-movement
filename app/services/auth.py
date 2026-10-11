"""Small password and session helpers for the MVP."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os

from ..security_config import environment


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str | None) -> bool:
    # Reject the legacy demo credential without rewriting any stored hash.
    try:
        algorithm, salt, digest = (stored or '').split('$', 2)
        if algorithm != 'scrypt':
            raise ValueError
        candidate = hash_password(password, base64.b64decode(salt))
    except (ValueError, TypeError):
        hash_password(password, bytes(16))
        return False
    matched = hmac.compare_digest(candidate, stored)
    return matched and not (environment() == 'production' and password == 'demo1234')
