from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..models import IntegrationConnector, MarketIntelRecord, MarketIntelSource
from .base import BaseConnector


SOURCE_NAME = "WHO GHO"


def ensure_source(db: Session) -> MarketIntelSource:
    src = db.query(MarketIntelSource).filter(MarketIntelSource.name == SOURCE_NAME).first()
    if not src:
        src = MarketIntelSource(
            name=SOURCE_NAME,
            kind="market_intel",
            base_url="https://ghoapi.azureedge.net/api",
            free=True,
            rate_limit_per_min=120,
        )
        db.add(src)
        db.commit()
        db.refresh(src)
    return src


class WHOGHOConnector(BaseConnector):
    kind = "who_gho"
    label = "WHO Global Health Observatory — health indicators"
    auth = "none"
    phase = 1

    def fetch_indicators(self, limit: int = 50) -> list[dict]:
        with httpx.Client(timeout=20.0) as client:
            r = client.get("https://ghoapi.azureedge.net/api/Indicator")
            r.raise_for_status()
            return (r.json().get("value", []) or [])[:limit]

    def sync(self, db: Session, connector_row: IntegrationConnector) -> dict[str, Any]:
        source = ensure_source(db)
        cfg = connector_row.config or {}
        try:
            indicators = self.fetch_indicators(limit=cfg.get("limit", 50))
        except httpx.HTTPError as exc:
            self._stamp(db, connector_row, f"error: {exc}")
            return {"ok": False, "error": str(exc)}

        ingested = 0
        for ind in indicators:
            ext_id = str(ind.get("IndicatorCode") or "")
            if not ext_id:
                continue
            existing = (
                db.query(MarketIntelRecord)
                .filter(MarketIntelRecord.source_id == source.id, MarketIntelRecord.external_id == ext_id)
                .first()
            )
            if existing:
                continue
            title = ind.get("IndicatorName") or ext_id
            db.add(
                MarketIntelRecord(
                    source_id=source.id,
                    country_code=None,
                    asset_match=None,
                    record_type="indicator",
                    external_id=ext_id,
                    title=f"Indicator: {title[:180]}",
                    url=ind.get("Language"),
                    payload=ind,
                )
            )
            ingested += 1

        db.commit()
        self._stamp(db, connector_row, f"ok: {ingested} new records")
        return {"ok": True, "ingested": ingested}
