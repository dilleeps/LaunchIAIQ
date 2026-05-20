from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine
from .jobs.scheduler import build_scheduler
from .migrations_phase2 import apply_phase2_migrations
from .routers import (
    approvals,
    assets,
    assistant,
    auth,
    comments,
    competitive_intel,
    dependencies,
    forecasts,
    fx,
    gates,
    integrations,
    irp,
    kpis,
    launches,
    lookups,
    market_intel,
    milestones,
    permissions,
    portfolio,
    prd_import,
    prds,
    raci,
    risks,
    scenarios,
    users,
    variance,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    apply_phase2_migrations(engine)
    sched = build_scheduler()
    sched.start()
    try:
        yield
    finally:
        sched.shutdown(wait=False)


app = FastAPI(title="LaunchAIQ API", version="0.2.0", lifespan=lifespan)

@app.middleware("http")
async def strip_api_prefix(request: Request, call_next):
    """Frontend (Vite dev convention) calls /api/*. ALB routes /api/* to this
    container without rewriting; FastAPI routes don't include the prefix. Strip
    it here so /api/auth/login and /auth/login both work."""
    path = request.scope.get("path", "")
    if path.startswith("/api/"):
        new_path = path[4:] or "/"
        request.scope["path"] = new_path
        request.scope["raw_path"] = new_path.encode("utf-8")
    return await call_next(request)


origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
def healthz():
    return {"ok": True}


app.include_router(auth.router)
app.include_router(lookups.router)
app.include_router(assets.router)
app.include_router(launches.router)
app.include_router(portfolio.router)
app.include_router(milestones.router)
app.include_router(prds.router)
app.include_router(prd_import.router)
app.include_router(risks.router)
app.include_router(raci.router)
app.include_router(kpis.router)
app.include_router(forecasts.router)
app.include_router(dependencies.router)
app.include_router(market_intel.router)
app.include_router(integrations.router)
app.include_router(scenarios.router)
app.include_router(irp.router)
app.include_router(fx.router)
app.include_router(variance.router)
app.include_router(gates.router)
app.include_router(approvals.router)
app.include_router(comments.router)
app.include_router(competitive_intel.router)
app.include_router(permissions.router)
app.include_router(assistant.router)
app.include_router(users.router)
