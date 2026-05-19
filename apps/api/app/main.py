from contextlib import asynccontextmanager

from fastapi import FastAPI
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


app = FastAPI(title="LaunchIAIQ API", version="0.2.0", lifespan=lifespan)

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
app.include_router(permissions.router)
app.include_router(assistant.router)
app.include_router(users.router)
