#!/usr/bin/env bash
# LaunchAIQ — SessionStart hook for Claude Code on the web.
# Boots Postgres, sets up the Python venv + Alembic schema + seed, installs npm deps.
# Idempotent: safe to re-run.

set -euo pipefail

# Only run in the cloud environment; locally users manage their own deps.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
API_DIR="$PROJECT_DIR/apps/api"
WEB_DIR="$PROJECT_DIR/apps/web"

log() { printf '[setup] %s\n' "$*"; }

# 1. Postgres — start the system cluster if installed, else skip (CI will provide one).
if command -v pg_ctlcluster >/dev/null 2>&1; then
  log "starting Postgres cluster 16/main"
  pg_ctlcluster 16 main start >/dev/null 2>&1 || true
  for _ in $(seq 1 30); do
    pg_isready -q && break
    sleep 1
  done
fi

# 2. DB role + database (idempotent).
if command -v psql >/dev/null 2>&1 && pg_isready -q 2>/dev/null; then
  log "ensuring launchiq role + database"
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='launchiq'" 2>/dev/null | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER launchiq WITH PASSWORD 'launchiq' SUPERUSER;" >/dev/null
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='launchiq'" 2>/dev/null | grep -q 1 || \
    sudo -u postgres createdb -O launchiq launchiq
fi

# 3. Backend venv + deps.
if [ -d "$API_DIR" ]; then
  log "preparing Python venv + dependencies"
  cd "$API_DIR"
  if [ ! -d .venv ]; then
    python3 -m venv .venv
  fi
  ./.venv/bin/pip install -q --disable-pip-version-check --upgrade pip
  ./.venv/bin/pip install -q --disable-pip-version-check -e .
  # passlib + bcrypt 4.1+ has a known incompat that breaks hash on long inputs.
  ./.venv/bin/pip install -q --disable-pip-version-check 'bcrypt<4.1'

  # Migrations + seed (only if DB reachable).
  if pg_isready -q 2>/dev/null; then
    log "running Alembic migrations"
    ./.venv/bin/alembic upgrade head >/dev/null
    log "seeding demo data"
    ./.venv/bin/python -m app.seed >/dev/null
  fi
fi

# 4. Frontend deps.
if [ -d "$WEB_DIR" ] && [ -f "$WEB_DIR/package.json" ]; then
  log "installing npm dependencies"
  cd "$WEB_DIR"
  # Prefer npm install over npm ci so the container cache speeds up subsequent runs.
  npm install --no-audit --no-fund --silent
fi

# 5. Persist useful env for the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  {
    echo 'export DATABASE_URL="postgresql+psycopg://launchiq:launchiq@localhost:5432/launchiq"'
    echo 'export CORS_ORIGINS="http://localhost:5173"'
    echo "export PATH=\"$API_DIR/.venv/bin:\$PATH\""
  } >> "$CLAUDE_ENV_FILE"
fi

log "ready. API: cd apps/api && .venv/bin/uvicorn app.main:app --reload  ·  WEB: cd apps/web && npm run dev"
