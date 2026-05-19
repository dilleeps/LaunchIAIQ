from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx
from sqlalchemy.orm import Session

from ..models import IntegrationConnector, MarketIntelRecord, MarketIntelSource
from .base import BaseConnector


SOURCE_NAME = "ClinicalTrials.gov"


def ensure_source(db: Session) -> MarketIntelSource:
    src = db.query(MarketIntelSource).filter(MarketIntelSource.name == SOURCE_NAME).first()
    if not src:
        src = MarketIntelSource(
            name=SOURCE_NAME,
            kind="market_intel",
            base_url="https://clinicaltrials.gov/api/v2",
            free=True,
            rate_limit_per_min=120,
        )
        db.add(src)
        db.commit()
        db.refresh(src)
    return src


class ClinicalTrialsConnector(BaseConnector):
    kind = "clinicaltrials_gov"
    label = "ClinicalTrials.gov — trial registry"
    auth = "none"
    phase = 1

    def fetch_studies(self, term: str | None, limit: int = 25) -> list[dict]:
        params: dict[str, Any] = {"pageSize": min(limit, 100), "format": "json"}
        if term:
            params["query.term"] = term
        with httpx.Client(timeout=20.0) as client:
            r = client.get("https://clinicaltrials.gov/api/v2/studies", params=params)
            r.raise_for_status()
            return r.json().get("studies", [])

    def sync(self, db: Session, connector_row: IntegrationConnector) -> dict[str, Any]:
        source = ensure_source(db)
        cfg = connector_row.config or {}
        term = cfg.get("asset_query") or cfg.get("term")
        try:
            studies = self.fetch_studies(term=term, limit=cfg.get("limit", 25))
        except httpx.HTTPError as exc:
            self._stamp(db, connector_row, f"error: {exc}")
            return {"ok": False, "error": str(exc)}

        ingested = 0
        for study in studies:
            proto = study.get("protocolSection", {}) or {}
            ident = proto.get("identificationModule", {}) or {}
            status_mod = proto.get("statusModule", {}) or {}
            ext_id = ident.get("nctId") or ""
            if not ext_id:
                continue
            existing = (
                db.query(MarketIntelRecord)
                .filter(MarketIntelRecord.source_id == source.id, MarketIntelRecord.external_id == ext_id)
                .first()
            )
            if existing:
                continue
            title = ident.get("briefTitle") or ident.get("officialTitle") or ext_id
            occurred_at = None
            sd = status_mod.get("startDateStruct", {}).get("date") or status_mod.get("statusVerifiedDate")
            if sd:
                for fmt in ("%Y-%m-%d", "%Y-%m"):
                    try:
                        occurred_at = datetime.strptime(sd, fmt)
                        break
                    except ValueError:
                        continue
            db.add(
                MarketIntelRecord(
                    source_id=source.id,
                    country_code=None,
                    asset_match=term,
                    record_type="trial",
                    external_id=ext_id,
                    title=f"Trial: {title[:180]}",
                    url=f"https://clinicaltrials.gov/study/{ext_id}",
                    occurred_at=occurred_at,
                    payload=study,
                )
            )
            ingested += 1

        db.commit()
        self._stamp(db, connector_row, f"ok: {ingested} new records")
        return {"ok": True, "ingested": ingested}
