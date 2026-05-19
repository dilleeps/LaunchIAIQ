from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..models import IntegrationConnector, MarketIntelRecord, MarketIntelSource
from .base import BaseConnector


SOURCE_NAME = "CMS Open Payments"
# Latest CY general payments dataset (Socrata Open Data API). 2022 detail is a long-standing resource id.
DATASET = "v6e3-h4qa"


def ensure_source(db: Session) -> MarketIntelSource:
    src = db.query(MarketIntelSource).filter(MarketIntelSource.name == SOURCE_NAME).first()
    if not src:
        src = MarketIntelSource(
            name=SOURCE_NAME,
            kind="market_intel",
            base_url="https://openpaymentsdata.cms.gov/resource",
            free=True,
            rate_limit_per_min=60,
        )
        db.add(src)
        db.commit()
        db.refresh(src)
    return src


class CMSOpenPaymentsConnector(BaseConnector):
    kind = "cms_open_payments"
    label = "CMS Open Payments — HCP industry payments"
    auth = "none"
    phase = 1

    def fetch_payments(self, drug_name: str | None, limit: int = 25) -> list[dict]:
        params: dict[str, Any] = {"$limit": min(limit, 100)}
        if drug_name:
            params["$q"] = drug_name
        with httpx.Client(timeout=30.0) as client:
            r = client.get(
                f"https://openpaymentsdata.cms.gov/resource/{DATASET}.json",
                params=params,
            )
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else []

    def sync(self, db: Session, connector_row: IntegrationConnector) -> dict[str, Any]:
        source = ensure_source(db)
        cfg = connector_row.config or {}
        drug_name = cfg.get("asset_query") or cfg.get("drug_name")
        try:
            payments = self.fetch_payments(drug_name=drug_name, limit=cfg.get("limit", 25))
        except httpx.HTTPError as exc:
            self._stamp(db, connector_row, f"error: {exc}")
            return {"ok": False, "error": str(exc)}

        ingested = 0
        for p in payments:
            ext_id = (
                p.get("record_id")
                or p.get("change_type")
                or p.get("program_year") and f"{p.get('program_year')}-{p.get('teaching_hospital_id') or p.get('physician_profile_id') or ''}"
            )
            ext_id = str(ext_id or "")
            if not ext_id:
                continue
            existing = (
                db.query(MarketIntelRecord)
                .filter(MarketIntelRecord.source_id == source.id, MarketIntelRecord.external_id == ext_id)
                .first()
            )
            if existing:
                continue
            recipient = (
                p.get("physician_first_name") or p.get("teaching_hospital_name") or "Recipient"
            )
            amount = p.get("total_amount_of_payment_usdollars")
            title = f"Payment: {recipient} ${amount}" if amount else f"Payment: {recipient}"
            db.add(
                MarketIntelRecord(
                    source_id=source.id,
                    country_code="USA",
                    asset_match=drug_name,
                    record_type="payment",
                    external_id=ext_id,
                    title=title[:200],
                    url=None,
                    payload=p,
                )
            )
            ingested += 1

        db.commit()
        self._stamp(db, connector_row, f"ok: {ingested} new records")
        return {"ok": True, "ingested": ingested}
