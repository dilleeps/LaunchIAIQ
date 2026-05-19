from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..models import IntegrationConnector, MarketIntelRecord, MarketIntelSource
from .base import BaseConnector


SOURCE_NAME = "DailyMed"


def ensure_source(db: Session) -> MarketIntelSource:
    src = db.query(MarketIntelSource).filter(MarketIntelSource.name == SOURCE_NAME).first()
    if not src:
        src = MarketIntelSource(
            name=SOURCE_NAME,
            kind="market_intel",
            base_url="https://dailymed.nlm.nih.gov/dailymed/services/v2",
            free=True,
            rate_limit_per_min=120,
        )
        db.add(src)
        db.commit()
        db.refresh(src)
    return src


class DailyMedConnector(BaseConnector):
    kind = "dailymed"
    label = "DailyMed (NIH) — structured product labels"
    auth = "none"
    phase = 1

    def fetch_labels(self, drug_name: str | None, limit: int = 25) -> list[dict]:
        params: dict[str, Any] = {"pagesize": min(limit, 100)}
        if drug_name:
            params["drug_name"] = drug_name
        with httpx.Client(timeout=20.0) as client:
            r = client.get(
                "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json",
                params=params,
            )
            r.raise_for_status()
            return r.json().get("data", [])

    def sync(self, db: Session, connector_row: IntegrationConnector) -> dict[str, Any]:
        source = ensure_source(db)
        cfg = connector_row.config or {}
        drug_name = cfg.get("asset_query") or cfg.get("drug_name")
        try:
            labels = self.fetch_labels(drug_name=drug_name, limit=cfg.get("limit", 25))
        except httpx.HTTPError as exc:
            self._stamp(db, connector_row, f"error: {exc}")
            return {"ok": False, "error": str(exc)}

        ingested = 0
        for item in labels:
            ext_id = item.get("setid") or ""
            if not ext_id:
                continue
            existing = (
                db.query(MarketIntelRecord)
                .filter(MarketIntelRecord.source_id == source.id, MarketIntelRecord.external_id == ext_id)
                .first()
            )
            if existing:
                continue
            title = item.get("title") or ext_id
            db.add(
                MarketIntelRecord(
                    source_id=source.id,
                    country_code="USA",
                    asset_match=drug_name,
                    record_type="label",
                    external_id=ext_id,
                    title=f"Label: {title[:180]}",
                    url=f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={ext_id}",
                    payload=item,
                )
            )
            ingested += 1

        db.commit()
        self._stamp(db, connector_row, f"ok: {ingested} new records")
        return {"ok": True, "ingested": ingested}
