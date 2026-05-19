import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import IntelSubscription, MarketIntelRecord, MarketIntelSource, User
from ..schemas import MarketIntelOut


router = APIRouter(prefix="/intel", tags=["market_intel"])


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
