#!/bin/sh
set -eu

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
python -m app.seed
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
