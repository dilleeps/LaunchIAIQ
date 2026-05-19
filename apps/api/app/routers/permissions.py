import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import User


router = APIRouter(prefix="/permissions", tags=["permissions"])


class PermissionIn(BaseModel):
    role_name: str
    entity: str
    field: str
    access: Literal["read", "write", "none"]


@router.get("")
def list_permissions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.execute(
        text("SELECT id, role_name, entity, field, access FROM field_permissions ORDER BY role_name, entity, field")
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("", dependencies=[Depends(require_role("global_admin"))])
def upsert_permission(
    body: PermissionIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    existing = db.execute(
        text(
            "SELECT id FROM field_permissions WHERE role_name = :r AND entity = :e AND field = :f"
        ),
        {"r": body.role_name, "e": body.entity, "f": body.field},
    ).mappings().first()
    if existing:
        db.execute(
            text("UPDATE field_permissions SET access = :a WHERE id = :id"),
            {"a": body.access, "id": existing["id"]},
        )
        pid = existing["id"]
    else:
        pid = uuid.uuid4()
        db.execute(
            text(
                "INSERT INTO field_permissions (id, role_name, entity, field, access) "
                "VALUES (:id, :r, :e, :f, :a)"
            ),
            {"id": str(pid), "r": body.role_name, "e": body.entity, "f": body.field, "a": body.access},
        )
    db.commit()
    return {"id": str(pid)}
