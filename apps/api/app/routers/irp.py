import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Forecast, Launch, User


router = APIRouter(prefix="/irp", tags=["irp"])


class IRPIn(BaseModel):
    source_launch_id: uuid.UUID
    new_net_price: float
    ccy: Optional[str] = None


@router.post("/simulate")
def simulate(body: IRPIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    src = (
        db.query(Launch)
        .filter(Launch.id == body.source_launch_id, Launch.org_id == user.org_id)
        .first()
    )
    if not src:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Source launch not found")

    # Collect target launch ids from reference_pricing_links and dependencies (link_type='references_price')
    targets: dict[str, dict] = {}
    for row in db.execute(
        text(
            "SELECT target_launch_id::text AS tid, weight, basket_role "
            "FROM reference_pricing_links WHERE source_launch_id = :sid"
        ),
        {"sid": str(body.source_launch_id)},
    ).mappings().all():
        targets[row["tid"]] = {"weight": row["weight"] or 1.0, "basket_role": row["basket_role"]}

    for row in db.execute(
        text(
            "SELECT target_id::text AS tid FROM dependencies "
            "WHERE org_id = :org AND source_type = 'launch' AND source_id = :sid "
            "AND target_type = 'launch' AND link_type = 'references_price'"
        ),
        {"org": str(user.org_id), "sid": str(body.source_launch_id)},
    ).mappings().all():
        targets.setdefault(row["tid"], {"weight": 1.0, "basket_role": "dependency"})

    if not targets:
        return []

    impacts = []
    for tid, meta in targets.items():
        target = db.query(Launch).filter(Launch.id == uuid.UUID(tid), Launch.org_id == user.org_id).first()
        if not target:
            continue
        fc = (
            db.query(Forecast)
            .filter(Forecast.launch_id == target.id, Forecast.is_current == True)  # noqa: E712
            .order_by(Forecast.version.desc())
            .first()
        )
        current_price = fc.y1_net_price if fc and fc.y1_net_price else 0.0
        weight = float(meta["weight"] or 1.0)
        new_implied = body.new_net_price * weight
        # Revenue delta over Y1 if patient count known
        y1p = fc.y1_patients if fc and fc.y1_patients else 0
        revenue_delta = (new_implied - current_price) * y1p
        impacts.append(
            {
                "target_launch_id": tid,
                "target_launch_code": target.launch_code,
                "current_price": current_price,
                "new_implied_price": new_implied,
                "weight": weight,
                "basket_role": meta["basket_role"],
                "y1_patients": y1p,
                "revenue_delta": revenue_delta,
                "currency": fc.currency if fc else (body.ccy or "USD"),
            }
        )
    return impacts
