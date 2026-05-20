"""Read-only audit log query."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import AuditLog, User


router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead", "medical", "market_access", "finance"))])
def list_audit(
    entity: str | None = None,
    entity_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=200, le=2000),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(AuditLog).filter(AuditLog.org_id == user.org_id)
    if entity:
        q = q.filter(AuditLog.entity == entity)
    if entity_id:
        q = q.filter(AuditLog.entity_id == str(entity_id))
    if user_id:
        q = q.filter(AuditLog.user_id == user_id)
    q = q.filter(AuditLog.at >= datetime.utcnow() - timedelta(days=days))
    rows = q.order_by(AuditLog.at.desc()).limit(limit).all()
    # Resolve user emails for display
    user_emails: dict[uuid.UUID, str] = {}
    for r in rows:
        if r.user_id and r.user_id not in user_emails:
            u = db.get(User, r.user_id)
            user_emails[r.user_id] = u.email if u else "system"
    return [
        {
            "id": str(r.id),
            "at": r.at.isoformat() if r.at else None,
            "user_id": str(r.user_id) if r.user_id else None,
            "user_email": user_emails.get(r.user_id, "system") if r.user_id else "system",
            "entity": r.entity,
            "entity_id": r.entity_id,
            "action": r.action,
            "before": r.before,
            "after": r.after,
        }
        for r in rows
    ]
