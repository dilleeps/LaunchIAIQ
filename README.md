# LaunchIAIQ

A pharma-native drug-launch cockpit. React + FastAPI + Postgres. Multi-tenant, full RBAC, free-source market intelligence baked in.

> Closes the gap between generic project tools (Smartsheet/Monday) and six-figure analytics suites (IQVIA / ZS / Veeva) — purpose-built data model for Asset × Country launches, typed cross-launch dependencies, versioned PRDs, auto-RAG rollup, and pharma-specific HTA / RACI / KPI structure.

See [`COMPETITORS.md`](./COMPETITORS.md) for the competitive landscape and [`ROADMAP.md`](./ROADMAP.md) for what ships in each phase.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite + TypeScript + Tailwind, TanStack Query, Zustand, Recharts |
| Backend  | Python 3.11 + FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2 |
| Database | PostgreSQL 16 (JSONB, recursive CTEs for dependency walks) |
| Auth     | JWT (Phase 1) → Keycloak SAML/OIDC (Phase 2) |
| Jobs     | APScheduler nightly market-intel pulls |
| Intel    | openFDA (live), ClinicalTrials.gov, DailyMed — all free APIs |

## Quickstart

### 1. Postgres

```bash
# Either:
docker compose up -d postgres
# Or natively:
pg_ctlcluster 16 main start
sudo -u postgres psql -c "CREATE USER launchiq WITH PASSWORD 'launchiq' SUPERUSER;"
sudo -u postgres psql -c "CREATE DATABASE launchiq OWNER launchiq;"
```

### 2. Backend

```bash
cd apps/api
python3 -m venv .venv
.venv/bin/pip install -e .
.venv/bin/pip install 'bcrypt<4.1'    # passlib/bcrypt compat
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed          # demo org + 5 launches + openFDA connector
.venv/bin/uvicorn app.main:app --reload
```

API live at <http://localhost:8000>. OpenAPI docs at <http://localhost:8000/docs>.

### 3. Frontend

```bash
cd apps/web
npm install
npm run dev
```

Web app at <http://localhost:5173>. Sign in with **`admin@demo.example` / `demo123`** (or `viewer@demo.example` for the read-only role).

### 4. Trigger a live market-intel sync

From the Settings page click *Sync now* on the openFDA connector — pulls 50 real drug labels + recalls from `api.fda.gov`. Records appear under any launch's *Market Pulse* tab.

## Tests

```bash
cd apps/api && .venv/bin/python -m pytest tests/
```

7 smoke tests cover: auth, RBAC scope, portfolio overview, matrix, recursive dependency walk, PRD versioning.

## Project layout

```
apps/
  api/                       FastAPI + SQLAlchemy
    app/
      routers/               One per resource
      integrations/          BaseConnector + openFDA + stubs
      jobs/scheduler.py      Nightly intel pulls
      rag.py                 Auto-RAG rollup
      models.py              Full schema
      seed.py                Demo data
    alembic/
  web/                       React + Vite
    src/
      pages/                 Overview, Matrix, LaunchDetail, Milestones, Admin
      layouts/AppShell.tsx
infra/                       Reserved for Phase 2 deploy manifests
docker-compose.yml
COMPETITORS.md
ROADMAP.md
```
