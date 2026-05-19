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
from ..models import Launch, User


router = APIRouter(tags=["gates"])


class GateIn(BaseModel):
    name: str
    required_role_names: list[str] = []


class ApproveIn(BaseModel):
    note: Optional[str] = None


@router.post("/launches/{launch_id}/gates")
def create_gate(
    launch_id: uuid.UUID,
    body: GateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    gid = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO stage_gates (id, launch_id, name, required_role_names, status) "
            "VALUES (:id, :lid, :name, CAST(:roles AS jsonb), 'pending')"
        ),
        {
            "id": str(gid),
            "lid": str(launch_id),
            "name": body.name,
            "roles": json.dumps(body.required_role_names),
        },
    )
    db.commit()
    return {"id": str(gid), "name": body.name, "status": "pending"}


@router.get("/launches/{launch_id}/gates")
def list_gates(
    launch_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    rows = db.execute(
        text(
            "SELECT id, launch_id, name, required_role_names, status, decided_at, decided_by, decision_note "
            "FROM stage_gates WHERE launch_id = :lid ORDER BY name"
        ),
        {"lid": str(launch_id)},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/gates/{gate_id}/approve")
def approve_gate(
    gate_id: uuid.UUID,
    body: ApproveIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    gate = db.execute(
        text(
            "SELECT g.id, g.launch_id, g.required_role_names, g.status "
            "FROM stage_gates g JOIN launches l ON l.id = g.launch_id "
            "WHERE g.id = :id AND l.org_id = :org"
        ),
        {"id": str(gate_id), "org": str(user.org_id)},
    ).mappings().first()
    if not gate:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Gate not found")
    if gate["status"] != "pending":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Gate already decided")
    required = gate["required_role_names"] or []
    if isinstance(required, str):
        required = json.loads(required)
    if user.default_role != "global_admin" and user.default_role not in required:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your role is not allowed to approve this gate")
    db.execute(
        text(
            "UPDATE stage_gates SET status = 'approved', decided_at = :ts, decided_by = :uid, decision_note = :note "
            "WHERE id = :id"
        ),
        {"id": str(gate_id), "ts": datetime.utcnow(), "uid": str(user.id), "note": body.note},
    )
    db.commit()
    return {"id": str(gate_id), "status": "approved"}
