import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
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


@router.post(
    "/sync-asset/{asset_id}",
    dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead", "medical", "market_access"))],
)
def sync_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Run every live market-intel connector against the asset's brand_name.

    Each kind in _ASSET_SYNC_KINDS is invoked once with the asset name patched
    into its config. If no IntegrationConnector row exists for that kind, one
    is auto-created (enabled, with the asset query) so subsequent nightly
    cron pulls also include this asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.org_id == user.org_id).first()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")

    results: list[dict] = []
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
            # Auto-provision so future scheduled syncs include this asset too
            conn = IntegrationConnector(
                org_id=user.org_id,
                kind=kind,
                config={"asset_query": asset.brand_name, "query": asset.brand_name, "limit": 25},
                enabled=True,
            )
            db.add(conn)
            db.flush()

        original_config = dict(conn.config or {})
        patched = dict(original_config)
        patched["asset_query"] = asset.brand_name  # openFDA uses this
        patched["query"] = asset.brand_name        # ClinicalTrials.gov / DailyMed
        conn.config = patched
        db.commit()

        try:
            connector = get_connector(kind)
            result = connector.sync(db=db, connector_row=conn)
            results.append({"kind": kind, **result})
        except Exception as exc:  # noqa: BLE001
            db.rollback()  # so subsequent connector syncs can use the session
            results.append({"kind": kind, "ok": False, "error": str(exc)[:200]})
        finally:
            try:
                conn.config = original_config
                db.commit()
            except Exception:
                db.rollback()

    # Quick count for the UI: total intel records that match this asset right
    # now (by brand_name or TA), to show the impact of the sync.
    total_matching = db.query(MarketIntelRecord).filter(
        (MarketIntelRecord.asset_match.ilike(f"%{asset.brand_name}%"))
        | (MarketIntelRecord.therapeutic_area == asset.therapeutic_area)
    ).count()

    return {
        "asset_id": str(asset_id),
        "asset_name": asset.brand_name,
        "therapeutic_area": asset.therapeutic_area,
        "ran": results,
        "total_intel_records_matching": total_matching,
    }
