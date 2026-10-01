"""Small password and session helpers for the MVP."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, stored: str | None) -> bool:
    if not stored:
        return False
    try:
        _, salt, digest = stored.split('$', 2)
        candidate = hash_password(password, base64.b64decode(salt))
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(candidate, stored)
