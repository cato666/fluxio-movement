"""Origin policy for cookie-authenticated mutations, including login CSRF."""
import ipaddress
import logging
import os
from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from .security_config import environment, reject, SecurityConfigurationError

logger = logging.getLogger(__name__)
SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}
SIGNED_WEBHOOK = '/webhooks/whatsapp/kapso'


def canonical_origin(value):
    try:
        if not value or any(ord(char) <= 32 or ord(char) >= 127 for char in value) or any(char in value for char in '?#'):
            raise ValueError
        parsed = urlsplit(value)
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.path or parsed.query or parsed.fragment:
            raise ValueError
        port = parsed.port
        if port == 0:
            raise ValueError
        host = parsed.hostname.lower()
        if ':' in host:
            host = '[' + host + ']'
        return parsed.scheme.lower() + '://' + host + ((':' + str(port)) if port and port != (443 if parsed.scheme == 'https' else 80) else '')
    except (ValueError, AttributeError):
        raise ValueError('Invalid origin') from None


def origins():
    configured = os.getenv('WEB_ALLOWED_ORIGINS', '')
    if not configured:
        if environment() == 'production':
            reject('WEB_ALLOWED_ORIGINS')
        configured = 'http://localhost:8000,http://127.0.0.1:8000'
    try:
        values = {canonical_origin(item.strip()) for item in configured.split(',')}
    except ValueError:
        reject('WEB_ALLOWED_ORIGINS')
    if environment() == 'production' and any(not item.startswith('https://') for item in values):
        reject('WEB_ALLOWED_ORIGINS')
    return values


def validate_web_security():
    origins()
    for name, default in [('LOGIN_WINDOW_SECONDS', 300), ('LOGIN_ACCOUNT_LIMIT', 5), ('LOGIN_PEER_LIMIT', 20)]:
        try:
            value = int(os.getenv(name, str(default)))
            if not 1 <= value <= (3600 if name == 'LOGIN_WINDOW_SECONDS' else 1000):
                raise ValueError
        except ValueError:
            reject(name)
    if environment() == 'production' and 'FORWARDED_ALLOW_IPS' not in os.environ:
        reject('FORWARDED_ALLOW_IPS')
    for item in os.getenv('FORWARDED_ALLOW_IPS', '').split(','):
        if item.strip():
            try:
                network = ipaddress.ip_network(item.strip(), strict=False)
                if network.prefixlen == 0:
                    raise ValueError
            except ValueError:
                reject('FORWARDED_ALLOW_IPS')


class WebSecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        # Only this exact endpoint uses provider signature instead of session cookies.
        if request.method not in SAFE_METHODS and path != SIGNED_WEBHOOK:
            origin = request.headers.get('origin')
            try:
                allowed = origins()
                if origin is None:
                    # Local non-browser automation only. Production always requires Origin.
                    accepted = environment() != 'production' and not any(name.startswith('sec-fetch-') for name in request.headers)
                else:
                    accepted = canonical_origin(origin) in allowed
                if environment() == 'production' and request.url.scheme != 'https':
                    accepted = False
                if len(request.headers.getlist('origin')) > 1:
                    accepted = False
                if request.headers.get('sec-fetch-site') == 'cross-site':
                    accepted = False
            except ValueError:
                accepted = False
            except SecurityConfigurationError:
                return JSONResponse({'detail': 'Configuración de seguridad no disponible'}, status_code=503, headers={'Cache-Control': 'no-store'})
            if not accepted:
                logger.warning('security_rejection reason=origin_policy')
                return JSONResponse({'detail': 'Origen de solicitud no autorizado'}, status_code=403, headers={'Cache-Control': 'no-store'})
        if path == '/api/auth/login' and request.method == 'POST':
            from .services.login_security import admit
            try:
                # Uvicorn rewrites client only for explicitly trusted proxy addresses.
                await run_in_threadpool(admit, 'peer', request.client.host if request.client else 'unknown')
            except HTTPException as exc:
                return JSONResponse({'detail': exc.detail}, status_code=exc.status_code, headers={**(exc.headers or {}), 'Cache-Control': 'no-store'})
            except (SQLAlchemyError, SecurityConfigurationError):
                return JSONResponse({'detail': 'Autenticación no disponible'}, status_code=503, headers={'Cache-Control': 'no-store'})
        response = await call_next(request)
        if path.startswith('/api/auth/'):
            response.headers['Cache-Control'] = 'no-store'
        return response
