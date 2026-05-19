import uuid
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User


router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalIn(BaseModel):
    entity: str
    entity_id: uuid.UUID
    approver_role_name: str


class DecisionIn(BaseModel):
    status: Literal["approved", "rejected"]
    comment: Optional[str] = None


@router.post("")
def create_approval(
    body: ApprovalIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    aid = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO approvals (id, entity, entity_id, requested_by, approver_role_name, status) "
            "VALUES (:id, :ent, :eid, :uid, :role, 'pending')"
        ),
        {
            "id": str(aid),
            "ent": body.entity,
            "eid": str(body.entity_id),
            "uid": str(user.id),
            "role": body.approver_role_name,
        },
    )
    db.commit()
    return {"id": str(aid), "status": "pending"}


@router.get("")
def list_approvals(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Filter by approver visibility: requester sees own; approvers see those matching their role; admin sees all.
    sql = (
        "SELECT id, entity, entity_id, requested_by, approver_role_name, approver_user_id, status, comment, requested_at, decided_at "
        "FROM approvals WHERE 1=1"
    )
    params: dict = {}
    if status_filter:
        sql += " AND status = :s"
        params["s"] = status_filter
    sql += " ORDER BY requested_at DESC"
    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.post("/{approval_id}/decide")
def decide(
    approval_id: uuid.UUID,
    body: DecisionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    row = db.execute(
        text("SELECT id, approver_role_name, status FROM approvals WHERE id = :id"),
        {"id": str(approval_id)},
    ).mappings().first()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Approval not found")
    if row["status"] != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Already decided")
    if user.default_role != "global_admin" and user.default_role != row["approver_role_name"]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role cannot decide this approval")
    db.execute(
        text(
            "UPDATE approvals SET status = :s, comment = :c, approver_user_id = :uid, decided_at = :ts WHERE id = :id"
        ),
        {
            "id": str(approval_id),
            "s": body.status,
            "c": body.comment,
            "uid": str(user.id),
            "ts": datetime.utcnow(),
        },
    )
    db.commit()
    return {"id": str(approval_id), "status": body.status}
