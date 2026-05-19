"""Nightly market-intelligence pulls. Hook into FastAPI lifespan."""
from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler

from ..database import SessionLocal
from ..integrations.registry import get_connector
from ..models import IntegrationConnector


def sync_all_market_intel():
    """Sync every enabled market-intel connector across all orgs."""
    db = SessionLocal()
    try:
        conns = db.query(IntegrationConnector).filter(IntegrationConnector.enabled.is_(True)).all()
        for c in conns:
            try:
                connector = get_connector(c.kind)
                connector.sync(db=db, connector_row=c)
            except Exception as exc:  # noqa: BLE001
                c.last_sync_status = f"error: {exc}"
                db.commit()
    finally:
        db.close()


def build_scheduler() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="UTC")
    # Nightly at 03:00 UTC
    sched.add_job(sync_all_market_intel, "cron", hour=3, minute=0, id="market_intel_nightly")
    return sched
