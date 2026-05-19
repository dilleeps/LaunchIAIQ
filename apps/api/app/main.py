from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .jobs.scheduler import build_scheduler
from .routers import (
    assets,
    auth,
    dependencies,
    forecasts,
    integrations,
    kpis,
    launches,
    lookups,
    market_intel,
    milestones,
    portfolio,
    prds,
    raci,
    risks,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    sched = build_scheduler()
    sched.start()
    try:
        yield
    finally:
        sched.shutdown(wait=False)


app = FastAPI(title="LaunchIAIQ API", version="0.1.0", lifespan=lifespan)

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
