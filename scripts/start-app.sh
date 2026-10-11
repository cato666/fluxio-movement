#!/bin/sh
set -eu

# Validate before any database access or migration.
python -m app.security_config

python - <<'PY'
import time
from sqlalchemy import text
from app.database import engine

for attempt in range(60):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        break
    except Exception:
        if attempt == 59:
            raise SystemExit("PostgreSQL no estuvo disponible durante el arranque")
        time.sleep(1)
PY

alembic upgrade head
if [ "${ENABLE_DEMO_SEED:-false}" = "true" ]; then
    python -m app.seed
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log --proxy-headers --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-}"
