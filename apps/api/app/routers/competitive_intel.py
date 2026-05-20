"""Competitive intelligence — static competitor records per asset, merged with
live market-intel hits (openFDA approvals, ClinicalTrials.gov updates) about
the same therapeutic area / molecule class."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Asset, User


router = APIRouter(prefix="/competitive-intel", tags=["competitive-intel"])


class CompetitorIn(BaseModel):
    competitor_name: str
    company: str | None = None
    moa: str | None = None
    stage: str | None = None
    notes: str | None = None


@router.get("/assets/{asset_id}")
def get_for_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.org_id == user.org_id).first()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")

    competitors = db.execute(
        text("""SELECT id, competitor_name, company, moa, stage, notes, created_at
                FROM competitive_intel WHERE asset_id = :a ORDER BY created_at"""),
        {"a": str(asset_id)},
    ).mappings().all()

    # Pull recent live intel records that match this asset's brand or TA
    intel = db.execute(
        text("""SELECT id, country_code, record_type, title, occurred_at
                FROM market_intel_records
                WHERE asset_match ILIKE :brand OR therapeutic_area = :ta
                ORDER BY occurred_at DESC NULLS LAST
                LIMIT 25"""),
        {"brand": f"%{asset.brand_name}%", "ta": asset.therapeutic_area},
    ).mappings().all()

    return {
        "asset": {
            "id": str(asset.id),
            "brand_name": asset.brand_name,
            "inn": asset.inn,
            "therapeutic_area": asset.therapeutic_area,
            "moa": asset.moa,
        },
        "competitors": [
            {**dict(c), "id": str(c["id"]), "created_at": c["created_at"].isoformat() if c["created_at"] else None}
            for c in competitors
        ],
        "live_intel": [
            {**dict(r), "id": str(r["id"]), "occurred_at": r["occurred_at"].isoformat() if r["occurred_at"] else None}
            for r in intel
        ],
    }


@router.post("/assets/{asset_id}", dependencies=[Depends(require_role("global_admin", "global_brand_lead"))])
def add_competitor(
    asset_id: uuid.UUID,
    body: CompetitorIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.org_id == user.org_id).first()
    if not asset:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
    new_id = uuid.uuid4()
    db.execute(
        text("""INSERT INTO competitive_intel (id, org_id, asset_id, competitor_name, company, moa, stage, notes)
                VALUES (:id, :o, :a, :n, :c, :m, :s, :no)"""),
        {"id": str(new_id), "o": str(user.org_id), "a": str(asset_id),
         "n": body.competitor_name, "c": body.company, "m": body.moa, "s": body.stage, "no": body.notes},
    )
    db.commit()
    return {"id": str(new_id), "competitor_name": body.competitor_name}


@router.get("/portfolio")
def portfolio_intel(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Aggregate competitive intel + market-intel hit count across the portfolio."""
    rows = db.execute(text("""
        SELECT a.id AS asset_id, a.brand_name, a.therapeutic_area,
               COUNT(DISTINCT ci.id) AS competitor_count,
               COUNT(DISTINCT mir.id) FILTER (WHERE mir.occurred_at >= NOW() - INTERVAL '90 days') AS intel_90d
        FROM assets a
        LEFT JOIN competitive_intel ci ON ci.asset_id = a.id
        LEFT JOIN market_intel_records mir ON mir.asset_match ILIKE '%' || a.brand_name || '%' OR mir.therapeutic_area = a.therapeutic_area
        WHERE a.org_id = :o
        GROUP BY a.id, a.brand_name, a.therapeutic_area
        ORDER BY a.brand_name
    """), {"o": str(user.org_id)}).mappings().all()
    return [{**dict(r), "asset_id": str(r["asset_id"])} for r in rows]
