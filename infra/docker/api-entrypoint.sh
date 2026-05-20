#!/usr/bin/env bash
set -euo pipefail

# 1. Wait for DB to be reachable.
if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "[entrypoint] waiting for database…"
  python - <<'PY'
import os, time, sys
import psycopg
url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
for i in range(60):
    try:
        with psycopg.connect(url, connect_timeout=3) as c:
            c.execute("SELECT 1")
        print("[entrypoint] DB ready.")
        sys.exit(0)
    except Exception as exc:
        print(f"  attempt {i+1}: {exc}")
        time.sleep(2)
sys.exit("DB never became ready")
PY
fi

# 2. Alembic migrations (idempotent).
if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
  echo "[entrypoint] alembic upgrade head"
  alembic upgrade head
fi

# 3. Phase-2 raw-SQL migrations (idempotent CREATE TABLE IF NOT EXISTS).
if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
  echo "[entrypoint] applying Phase-2 migrations"
  python -c "from app.database import engine; from app.migrations_phase2 import apply_phase2_migrations; apply_phase2_migrations(engine)"
fi

# 4. Seed demo data (idempotent — _get_or_create guards every row).
#    Default ON for first deploy; set SEED_ON_BOOT=false to disable later.
if [[ "${SEED_ON_BOOT:-true}" == "true" ]]; then
  echo "[entrypoint] seeding demo data"
  python -m app.seed
fi

exec "$@"
