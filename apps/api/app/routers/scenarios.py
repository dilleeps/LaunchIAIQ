import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Launch, User


router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class ScenarioIn(BaseModel):
    name: str
    base_launch_id: uuid.UUID
    parent_scenario_id: Optional[uuid.UUID] = None


class OverrideIn(BaseModel):
    entity: str
    entity_id: uuid.UUID
    field: str
    value: Any


def _scenario_row(db: Session, scenario_id: uuid.UUID, org_id: uuid.UUID) -> dict:
    row = db.execute(
        text("SELECT * FROM scenarios WHERE id = :id AND org_id = :org"),
        {"id": str(scenario_id), "org": str(org_id)},
    ).mappings().first()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scenario not found")
    return dict(row)


@router.get("")
def list_scenarios(
    launch_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sql = "SELECT id, org_id, base_launch_id, name, parent_scenario_id, created_by, created_at FROM scenarios WHERE org_id = :org"
    params: dict[str, Any] = {"org": str(user.org_id)}
    if launch_id:
        sql += " AND base_launch_id = :lid"
        params["lid"] = str(launch_id)
    sql += " ORDER BY created_at DESC"
    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.post("")
def create_scenario(body: ScenarioIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == body.base_launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Base launch not found")
    sid = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO scenarios (id, org_id, base_launch_id, name, parent_scenario_id, created_by) "
            "VALUES (:id, :org, :base, :name, :parent, :uid)"
        ),
        {
            "id": str(sid),
            "org": str(user.org_id),
            "base": str(body.base_launch_id),
            "name": body.name,
            "parent": str(body.parent_scenario_id) if body.parent_scenario_id else None,
            "uid": str(user.id),
        },
    )
    db.commit()
    return {"id": str(sid), "name": body.name, "base_launch_id": str(body.base_launch_id)}


@router.post("/{scenario_id}/overrides")
def add_override(
    scenario_id: uuid.UUID,
    body: OverrideIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _scenario_row(db, scenario_id, user.org_id)
    import json
    oid = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO scenario_overrides (id, scenario_id, entity, entity_id, field, value) "
            "VALUES (:id, :sid, :ent, :eid, :field, CAST(:val AS jsonb))"
        ),
        {
            "id": str(oid),
            "sid": str(scenario_id),
            "ent": body.entity,
            "eid": str(body.entity_id),
            "field": body.field,
            "val": json.dumps(body.value),
        },
    )
    db.commit()
    return {"id": str(oid)}


@router.get("/{scenario_id}/compare-to-base")
def compare_to_base(
    scenario_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scen = _scenario_row(db, scenario_id, user.org_id)
    base_launch_id = scen["base_launch_id"]
    overrides = db.execute(
        text("SELECT entity, entity_id, field, value FROM scenario_overrides WHERE scenario_id = :sid"),
        {"sid": str(scenario_id)},
    ).mappings().all()

    out: dict[str, dict[str, Any]] = {}
    for ov in overrides:
        entity = ov["entity"]
        eid = ov["entity_id"]
        field = ov["field"]
        # Fetch base value for the entity.field
        base_val: Any = None
        try:
            res = db.execute(
                text(f"SELECT {field} AS v FROM {entity} WHERE id = :id"),
                {"id": str(eid)},
            ).mappings().first()
            if res:
                base_val = res["v"]
        except Exception:
            base_val = None
        key = f"{entity}.{eid}.{field}"
        out[key] = {"base": base_val, "override": ov["value"]}
    return {"scenario_id": str(scenario_id), "base_launch_id": str(base_launch_id), "fields": out}
