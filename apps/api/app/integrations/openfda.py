from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import IntegrationConnector, MarketIntelRecord, MarketIntelSource
from .base import BaseConnector


SOURCE_NAME = "openFDA"


def ensure_source(db: Session) -> MarketIntelSource:
    src = db.query(MarketIntelSource).filter(MarketIntelSource.name == SOURCE_NAME).first()
    if not src:
        src = MarketIntelSource(
            name=SOURCE_NAME,
            kind="market_intel",
            base_url="https://api.fda.gov",
            free=True,
            rate_limit_per_min=240,
        )
        db.add(src)
        db.commit()
        db.refresh(src)
    return src


class OpenFDAConnector(BaseConnector):
    kind = "openfda"
    label = "openFDA — drug approvals, labels, recalls"
    auth = "api_key (optional)"
    phase = 1

    def _params(self, search: str, limit: int = 25) -> dict[str, Any]:
        p = {"search": search, "limit": limit}
        if settings.openfda_api_key:
            p["api_key"] = settings.openfda_api_key
        return p

    def fetch_drug_labels(self, asset_query: str | None = None, limit: int = 25) -> list[dict]:
        search = "_exists_:openfda.brand_name"
        if asset_query:
            search = f'openfda.brand_name:"{asset_query}"'
        with httpx.Client(timeout=20.0) as client:
            r = client.get(f"https://api.fda.gov/drug/label.json", params=self._params(search, limit))
            # 404 = no matches for this query — that's a normal outcome for pre-approval assets
            if r.status_code == 404:
                return []
            r.raise_for_status()
            return r.json().get("results", [])

    def fetch_drug_recalls(self, asset_query: str | None = None, limit: int = 25) -> list[dict]:
        search = "status:Ongoing"
        if asset_query:
            search = f'product_description:"{asset_query}" AND status:Ongoing'
        with httpx.Client(timeout=20.0) as client:
            r = client.get(
                "https://api.fda.gov/drug/enforcement.json",
                params=self._params(search, limit),
            )
            if r.status_code == 404:
                return []
            r.raise_for_status()
            return r.json().get("results", [])

    def sync(self, db: Session, connector_row: IntegrationConnector) -> dict[str, Any]:
        source = ensure_source(db)
        cfg = connector_row.config or {}
        asset_query = cfg.get("asset_query")
        try:
            labels = self.fetch_drug_labels(asset_query=asset_query, limit=cfg.get("limit", 25))
            recalls = self.fetch_drug_recalls(asset_query=asset_query, limit=cfg.get("limit", 25))
        except httpx.HTTPError as exc:
            self._stamp(db, connector_row, f"error: {exc}")
            return {"ok": False, "error": str(exc)}

        ingested = 0
        for label in labels:
            ext_id = label.get("id") or label.get("set_id") or ""
            if not ext_id:
                continue
            existing = (
                db.query(MarketIntelRecord)
                .filter(MarketIntelRecord.source_id == source.id, MarketIntelRecord.external_id == ext_id)
                .first()
            )
            brand = (label.get("openfda", {}).get("brand_name") or [None])[0]
            title = f"Label: {brand}" if brand else "Drug label"
            effective_time = label.get("effective_time")
            occurred_at = None
            if effective_time and len(effective_time) == 8:
                try:
                    occurred_at = datetime.strptime(effective_time, "%Y%m%d")
                except ValueError:
                    pass
            if existing:
                continue
            db.add(
                MarketIntelRecord(
                    source_id=source.id,
                    country_code="USA",
                    asset_match=brand,
                    record_type="label",
                    external_id=ext_id,
                    title=title,
                    url=None,
                    occurred_at=occurred_at,
                    payload=label,
                )
            )
            ingested += 1

        for rec in recalls:
            ext_id = rec.get("recall_number") or ""
            if not ext_id:
                continue
            existing = (
                db.query(MarketIntelRecord)
                .filter(MarketIntelRecord.source_id == source.id, MarketIntelRecord.external_id == ext_id)
                .first()
            )
            if existing:
                continue
            db.add(
                MarketIntelRecord(
                    source_id=source.id,
                    country_code="USA",
                    asset_match=rec.get("product_description"),
                    record_type="recall",
                    external_id=ext_id,
                    title=f"Recall: {rec.get('reason_for_recall', '')[:160]}",
                    url=None,
                    payload=rec,
                )
            )
            ingested += 1

        db.commit()
        self._stamp(db, connector_row, f"ok: {ingested} new records")
        return {"ok": True, "ingested": ingested}
