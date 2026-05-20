"""Per-launch activity feed (audit log scoped + cross-entity) + watchers."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import AuditLog, Launch, Milestone, Risk, RiskLaunchLink, User


router = APIRouter(tags=["activity"])


def _ensure_watchers_table(db: Session) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS launch_watchers (
            id uuid PRIMARY KEY,
            user_id uuid NOT NULL,
            launch_id uuid NOT NULL,
            created_at timestamp DEFAULT now(),
            UNIQUE(user_id, launch_id)
        )
    """))
    db.commit()


@router.get("/launches/{launch_id}/activity")
def launch_activity(
    launch_id: uuid.UUID,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    launch = db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first()
    if not launch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")

    # Collect IDs of related entities so the feed picks up milestone / risk edits too
    ms_ids = [str(m.id) for m in db.query(Milestone).filter(Milestone.launch_id == launch_id).all()]
    risk_ids = [
        str(r[0]) for r in db.query(Risk.id).join(RiskLaunchLink, RiskLaunchLink.risk_id == Risk.id)
        .filter(RiskLaunchLink.launch_id == launch_id).all()
    ]
    related = [str(launch_id)] + ms_ids + risk_ids

    q = db.query(AuditLog).filter(
        AuditLog.org_id == user.org_id,
        AuditLog.entity_id.in_(related),
        AuditLog.at >= datetime.utcnow() - timedelta(days=days),
    ).order_by(AuditLog.at.desc()).limit(limit)
    rows = q.all()
    user_emails: dict[uuid.UUID, str] = {}
    for r in rows:
        if r.user_id and r.user_id not in user_emails:
            u = db.get(User, r.user_id)
            user_emails[r.user_id] = u.email if u else "system"

    return [
        {
            "id": str(r.id),
            "at": r.at.isoformat() if r.at else None,
            "user_email": user_emails.get(r.user_id, "system") if r.user_id else "system",
            "entity": r.entity,
            "entity_id": r.entity_id,
            "action": r.action,
            "before": r.before,
            "after": r.after,
        }
        for r in rows
    ]


# ── Watchers ─────────────────────────────────────────────────────────

@router.get("/me/watchlist")
def my_watchlist(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_watchers_table(db)
    rows = db.execute(text("""
        SELECT w.launch_id, l.launch_code, a.brand_name, c.name AS country, l.overall_rag, l.target_launch_date, w.created_at
        FROM launch_watchers w
        JOIN launches l ON l.id = w.launch_id
        JOIN assets a   ON a.id = l.asset_id
        JOIN countries c ON c.id = l.country_id
        WHERE w.user_id = :u AND l.org_id = :o
        ORDER BY w.created_at DESC
    """), {"u": str(user.id), "o": str(user.org_id)}).mappings().all()
    return [
        {
            **dict(r),
            "launch_id": str(r["launch_id"]),
            "target_launch_date": r["target_launch_date"].isoformat() if r["target_launch_date"] else None,
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]


@router.post("/launches/{launch_id}/watch")
def watch(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_watchers_table(db)
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    db.execute(text("""
        INSERT INTO launch_watchers (id, user_id, launch_id)
        VALUES (:id, :u, :l)
        ON CONFLICT (user_id, launch_id) DO NOTHING
    """), {"id": str(uuid.uuid4()), "u": str(user.id), "l": str(launch_id)})
    db.commit()
    return {"watching": True}


@router.delete("/launches/{launch_id}/watch", status_code=204)
def unwatch(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_watchers_table(db)
    db.execute(text("DELETE FROM launch_watchers WHERE user_id = :u AND launch_id = :l"),
               {"u": str(user.id), "l": str(launch_id)})
    db.commit()


@router.get("/me/feed")
def my_feed(
    days: int = Query(default=7, ge=1, le=90),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Aggregate activity across all launches the user watches (+ ones they own)."""
    _ensure_watchers_table(db)
    watched_ids = [
        r[0] for r in db.execute(
            text("SELECT launch_id FROM launch_watchers WHERE user_id = :u"),
            {"u": str(user.id)},
        ).fetchall()
    ]
    # Also include launches they own
    owned = [
        str(l.id) for l in db.query(Launch).filter(
            Launch.org_id == user.org_id,
            (Launch.country_launch_lead_user_id == user.id) | (Launch.global_brand_lead_user_id == user.id),
        ).all()
    ]
    launch_ids = list({str(x) for x in watched_ids} | set(owned))
    if not launch_ids:
        return []

    # Pull related milestone + risk ids too
    ms_ids = [str(m[0]) for m in db.execute(
        text("SELECT id FROM milestones WHERE launch_id = ANY(:lids::uuid[])"),
        {"lids": launch_ids},
    ).fetchall()]
    risk_ids = [str(r[0]) for r in db.execute(
        text("SELECT DISTINCT r.id FROM risks r JOIN risk_launch_links rl ON rl.risk_id = r.id WHERE rl.launch_id = ANY(:lids::uuid[])"),
        {"lids": launch_ids},
    ).fetchall()]
    related = list(set(launch_ids + ms_ids + risk_ids))

    rows = db.query(AuditLog).filter(
        AuditLog.org_id == user.org_id,
        AuditLog.entity_id.in_(related),
        AuditLog.at >= datetime.utcnow() - timedelta(days=days),
    ).order_by(AuditLog.at.desc()).limit(limit).all()

    user_emails: dict[uuid.UUID, str] = {}
    for r in rows:
        if r.user_id and r.user_id not in user_emails:
            u = db.get(User, r.user_id)
            user_emails[r.user_id] = u.email if u else "system"

    return [
        {
            "id": str(r.id),
            "at": r.at.isoformat() if r.at else None,
            "user_email": user_emails.get(r.user_id, "system") if r.user_id else "system",
            "entity": r.entity,
            "entity_id": r.entity_id,
            "action": r.action,
            "before": r.before,
            "after": r.after,
        }
        for r in rows
    ]
