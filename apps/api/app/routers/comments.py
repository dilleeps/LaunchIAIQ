import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import PRD, User


router = APIRouter(tags=["comments"])


class CommentIn(BaseModel):
    section: str
    field: Optional[str] = None
    body: str
    mentions: list[str] = []
    parent_id: Optional[uuid.UUID] = None


def _prd_in_org(db: Session, prd_id: uuid.UUID, org_id: uuid.UUID) -> bool:
    return db.execute(
        text(
            "SELECT 1 FROM prds p JOIN launches l ON l.id = p.launch_id "
            "WHERE p.id = :pid AND l.org_id = :org"
        ),
        {"pid": str(prd_id), "org": str(org_id)},
    ).first() is not None


@router.post("/prds/{prd_id}/comments")
def create_comment(
    prd_id: uuid.UUID,
    body: CommentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _prd_in_org(db, prd_id, user.org_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PRD not found")
    cid = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO prd_comments (id, prd_id, section, field, user_id, body, mentions, parent_id) "
            "VALUES (:id, :pid, :section, :field, :uid, :body, CAST(:mentions AS jsonb), :parent)"
        ),
        {
            "id": str(cid),
            "pid": str(prd_id),
            "section": body.section,
            "field": body.field,
            "uid": str(user.id),
            "body": body.body,
            "mentions": json.dumps(body.mentions),
            "parent": str(body.parent_id) if body.parent_id else None,
        },
    )
    db.commit()
    return {"id": str(cid)}


@router.get("/prds/{prd_id}/comments")
def list_comments(
    prd_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _prd_in_org(db, prd_id, user.org_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PRD not found")
    rows = db.execute(
        text(
            "SELECT id, prd_id, section, field, user_id, body, mentions, parent_id, resolved_at, created_at "
            "FROM prd_comments WHERE prd_id = :pid ORDER BY created_at ASC"
        ),
        {"pid": str(prd_id)},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/comments/{comment_id}/resolve")
def resolve_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    res = db.execute(
        text(
            "UPDATE prd_comments SET resolved_at = :ts WHERE id = :id "
            "AND prd_id IN (SELECT p.id FROM prds p JOIN launches l ON l.id = p.launch_id WHERE l.org_id = :org)"
        ),
        {"ts": datetime.utcnow(), "id": str(comment_id), "org": str(user.org_id)},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    return {"id": str(comment_id), "resolved": True}
