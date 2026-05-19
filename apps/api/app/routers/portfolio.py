import uuid
from collections import defaultdict
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Forecast, Launch, Milestone, Risk, User
from ..schemas import MatrixCell, MatrixRow, OverviewStat


router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/overview", response_model=OverviewStat)
def overview(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    launches = db.query(Launch).filter(Launch.org_id == user.org_id).all()
    on_track = sum(1 for ln in launches if ln.overall_rag == "Green")

    forecasts = (
        db.query(Forecast)
        .join(Launch, Launch.id == Forecast.launch_id)
        .filter(Launch.org_id == user.org_id, Forecast.is_current.is_(True))
        .all()
    )
    peak = 0.0
    peak_ccy = "USD"
    for f in forecasts:
        for yr_p, yr_pr in [
            (f.y1_patients, f.y1_net_price),
            (f.y2_patients, f.y2_net_price),
            (f.y3_patients, f.y3_net_price),
        ]:
            if yr_p and yr_pr:
                rev = float(yr_p) * float(yr_pr)
                if rev > peak:
                    peak = rev
                    peak_ccy = f.currency

    high_risks = (
        db.query(Risk)
        .filter(
            Risk.org_id == user.org_id,
            Risk.status != "Closed",
            Risk.score >= 6,
        )
        .count()
    )

    next_ms = (
        db.query(Milestone)
        .join(Launch, Launch.id == Milestone.launch_id)
        .filter(
            Launch.org_id == user.org_id,
            Milestone.target_date.is_not(None),
            Milestone.target_date >= date.today(),
            Milestone.status != "Complete",
        )
        .order_by(Milestone.target_date.asc())
        .first()
    )
    nm = None
    if next_ms:
        ln = db.get(Launch, next_ms.launch_id)
        nm = {
            "name": next_ms.name,
            "target_date": next_ms.target_date.isoformat() if next_ms.target_date else None,
            "launch_code": ln.launch_code if ln else None,
            "asset_brand": ln.asset.brand_name if ln and ln.asset else None,
        }

    return OverviewStat(
        on_track_count=on_track,
        total_launches=len(launches),
        peak_revenue=peak,
        peak_revenue_currency=peak_ccy,
        high_risks_open=high_risks,
        next_milestone=nm,
    )


@router.get("/matrix", response_model=list[MatrixRow])
def matrix(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    launches = db.query(Launch).filter(Launch.org_id == user.org_id).all()
    by_asset: dict[uuid.UUID, dict] = {}
    for ln in launches:
        row = by_asset.setdefault(
            ln.asset_id,
            {"asset_id": ln.asset_id, "brand_name": ln.asset.brand_name, "cells": {}},
        )
        ms_rows = db.query(Milestone).filter(Milestone.launch_id == ln.id).all()
        total = len(ms_rows) or 1
        complete = sum(1 for m in ms_rows if m.status == "Complete")
        row["cells"][ln.country.code] = MatrixCell(
            launch_id=ln.id,
            launch_code=ln.launch_code,
            rag=ln.overall_rag,
            milestones_complete_pct=round(100.0 * complete / total, 1),
        )
    return list(by_asset.values())
