import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..integrations.registry import get_connector
from ..models import Asset, IntegrationConnector, IntelSubscription, MarketIntelRecord, MarketIntelSource, User
from ..schemas import MarketIntelOut


router = APIRouter(prefix="/intel", tags=["market_intel"])


# Market-intel connector kinds we'll run when "sync by asset" is invoked.
_ASSET_SYNC_KINDS = ("openfda", "clinicaltrials_gov", "dailymed")


@router.get("/sources")
def sources(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return [
        {"id": str(s.id), "name": s.name, "kind": s.kind, "free": s.free, "base_url": s.base_url}
        for s in db.query(MarketIntelSource).all()
    ]


@router.get("/records", response_model=list[MarketIntelOut])
def records(
    asset_match: str | None = None,
    country_code: str | None = None,
    therapeutic_area: str | None = None,
    since: datetime | None = None,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(MarketIntelRecord)
    if asset_match:
        q = q.filter(MarketIntelRecord.asset_match.ilike(f"%{asset_match}%"))
    if country_code:
        q = q.filter(MarketIntelRecord.country_code == country_code)
    if therapeutic_area:
        q = q.filter(MarketIntelRecord.therapeutic_area == therapeutic_area)
    if since:
        q = q.filter(MarketIntelRecord.occurred_at >= since)
    return q.order_by(MarketIntelRecord.occurred_at.desc().nullslast()).limit(limit).all()


@router.post("/subscriptions")
def subscribe(
    scope_type: str,
    scope_id: uuid.UUID | None = None,
    keywords: list[str] = [],
    source_ids: list[uuid.UUID] = [],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = IntelSubscription(
        org_id=user.org_id,
        scope_type=scope_type,
        scope_id=scope_id,
        keywords=keywords,
        source_ids=[str(s) for s in source_ids],
    )
    db.add(sub)
    db.commit()
    return {"id": str(sub.id)}


@router.get("/sync-asset/{asset_id}/terms")
def get_asset_terms(asset_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """List the search synonyms registered for this asset (research code, INN, etc)."""
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.org_id == user.org_id).first()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    rows = db.execute(
        text("SELECT term FROM asset_search_terms WHERE asset_id = :a ORDER BY term"),
        {"a": str(asset.id)},
    ).all()
    return {
        "asset_id": str(asset.id),
        "brand_name": asset.brand_name,
        "inn": asset.inn,
        "extra_terms": [r[0] for r in rows],
    }


@router.post(
    "/sync-asset/{asset_id}/terms",
    dependencies=[Depends(require_role("global_admin", "global_brand_lead"))],
)
def add_asset_term(asset_id: uuid.UUID, term: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.org_id == user.org_id).first()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    t = term.strip()
    if not t:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Term cannot be empty")
    db.execute(
        text("INSERT INTO asset_search_terms (asset_id, term) VALUES (:a, :t) ON CONFLICT DO NOTHING"),
        {"a": str(asset.id), "t": t},
    )
    db.commit()
    return {"ok": True, "term": t}


@router.delete(
    "/sync-asset/{asset_id}/terms/{term}",
    dependencies=[Depends(require_role("global_admin", "global_brand_lead"))],
)
def remove_asset_term(asset_id: uuid.UUID, term: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Asset).filter(Asset.id == asset_id, Asset.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    db.execute(
        text("DELETE FROM asset_search_terms WHERE asset_id = :a AND term = :t"),
        {"a": str(asset_id), "t": term},
    )
    db.commit()
    return {"ok": True}


@router.post(
    "/sync-asset/{asset_id}",
    dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead", "medical", "market_access"))],
)
def sync_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Run every live market-intel connector against multiple search terms
    derived from the asset (brand name, INN, research code, MoA).

    Pre-approval pipeline drugs (e.g. Oveporexton / TAK-861) often have ZERO
    matches under the brand name on openFDA/DailyMed because they aren't
    FDA-approved yet. ClinicalTrials.gov frequently registers trials only
    under the research code (TAK-861, PTG-300, TAK-279). We fan out the
    sync across every term we have so the cockpit shows everything matching.
    """
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.org_id == user.org_id).first()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")

    # Build the list of search terms to try.
    raw_terms: list[str | None] = [asset.brand_name, asset.inn]
    # Pull research codes / synonyms from asset_search_terms.
    try:
        extra = db.execute(
            text("SELECT term FROM asset_search_terms WHERE asset_id = :a"),
            {"a": str(asset.id)},
        ).all()
        for row in extra:
            if row[0]:
                raw_terms.append(row[0])
    except Exception:
        db.rollback()
    # De-dupe (case-insensitive) and drop empties
    seen: set[str] = set()
    search_terms: list[str] = []
    for t in raw_terms:
        if not t:
            continue
        key = t.strip().lower()
        if key and key not in seen:
            seen.add(key)
            search_terms.append(t.strip())

    results: list[dict] = []
    total_ingested = 0
    for kind in _ASSET_SYNC_KINDS:
        conn = (
            db.query(IntegrationConnector)
            .filter(
                IntegrationConnector.org_id == user.org_id,
                IntegrationConnector.kind == kind,
            )
            .order_by(IntegrationConnector.last_sync_at.desc().nullslast())
            .first()
        )

        if conn is None:
            conn = IntegrationConnector(
                org_id=user.org_id,
                kind=kind,
                config={"asset_query": asset.brand_name, "query": asset.brand_name, "limit": 25},
                enabled=True,
            )
            db.add(conn)
            db.flush()

        original_config = dict(conn.config or {})
        per_kind_ingested = 0
        per_kind_errors: list[str] = []
        terms_tried: list[str] = []

        for term in search_terms:
            patched = dict(original_config)
            patched["asset_query"] = term
            patched["query"] = term
            patched["term"] = term
            patched["drug_name"] = term
            conn.config = patched
            db.commit()
            terms_tried.append(term)
            try:
                connector = get_connector(kind)
                result = connector.sync(db=db, connector_row=conn)
                if result.get("ok"):
                    per_kind_ingested += int(result.get("ingested", 0) or 0)
                else:
                    per_kind_errors.append(f"{term}: {result.get('error','?')[:80]}")
            except Exception as exc:  # noqa: BLE001
                db.rollback()
                per_kind_errors.append(f"{term}: {str(exc)[:80]}")

        # Restore original config
        try:
            conn.config = original_config
            db.commit()
        except Exception:
            db.rollback()

        results.append({
            "kind": kind,
            "ok": per_kind_ingested > 0 or not per_kind_errors,
            "ingested": per_kind_ingested,
            "terms_tried": terms_tried,
            "errors": per_kind_errors,
        })
        total_ingested += per_kind_ingested

    # Count current matching records (by any of the terms or TA)
    if search_terms:
        like_clauses = " OR ".join([f"asset_match ILIKE :t{i}" for i in range(len(search_terms))])
        params: dict[str, Any] = {f"t{i}": f"%{t}%" for i, t in enumerate(search_terms)}
        params["ta"] = asset.therapeutic_area
        total_matching = db.execute(
            text(f"SELECT COUNT(*) FROM market_intel_records WHERE ({like_clauses}) OR therapeutic_area = :ta"),
            params,
        ).scalar() or 0
    else:
        total_matching = 0

    return {
        "asset_id": str(asset_id),
        "asset_name": asset.brand_name,
        "therapeutic_area": asset.therapeutic_area,
        "search_terms": search_terms,
        "ran": results,
        "ingested_this_run": total_ingested,
        "total_intel_records_matching": total_matching,
    }
