#!/usr/bin/env bash
set -euo pipefail

# Wait for DB to be reachable before running migrations.
if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "Waiting for database…"
  python - <<'PY'
import os, time, urllib.parse, sys
import psycopg
url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://", 1)
for i in range(60):
    try:
        with psycopg.connect(url, connect_timeout=3) as c:
            c.execute("SELECT 1")
        print("DB ready.")
        sys.exit(0)
    except Exception as exc:
        print(f"  attempt {i+1}: {exc}")
        time.sleep(2)
sys.exit("DB never became ready")
PY
fi

# Run Alembic migrations (idempotent).
if [[ "${RUN_MIGRATIONS:-true}" == "true" ]]; then
  alembic upgrade head
fi

exec "$@"
