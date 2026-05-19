import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import User


router = APIRouter(prefix="/fx-assumptions", tags=["fx"])


class FxIn(BaseModel):
    from_ccy: str
    to_ccy: str
    year: int
    rate: float
    version: int = 1
    source: str = "manual"


@router.get("")
def list_fx(
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sql = "SELECT id, org_id, from_ccy, to_ccy, year, rate, version, source FROM fx_assumptions WHERE org_id = :org"
    params: dict = {"org": str(user.org_id)}
    if year is not None:
        sql += " AND year = :year"
        params["year"] = year
    sql += " ORDER BY year, from_ccy, to_ccy"
    return [dict(r) for r in db.execute(text(sql), params).mappings().all()]


@router.post("", dependencies=[Depends(require_role("global_admin", "finance"))])
def create_fx(body: FxIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    fid = uuid.uuid4()
    db.execute(
        text(
            "INSERT INTO fx_assumptions (id, org_id, from_ccy, to_ccy, year, rate, version, source) "
            "VALUES (:id, :org, :f, :t, :y, :r, :v, :s)"
        ),
        {
            "id": str(fid),
            "org": str(user.org_id),
            "f": body.from_ccy.upper(),
            "t": body.to_ccy.upper(),
            "y": body.year,
            "r": body.rate,
            "v": body.version,
            "s": body.source,
        },
    )
    db.commit()
    return {"id": str(fid)}


@router.delete("/{fx_id}", status_code=204, dependencies=[Depends(require_role("global_admin", "finance"))])
def delete_fx(fx_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    res = db.execute(
        text("DELETE FROM fx_assumptions WHERE id = :id AND org_id = :org"),
        {"id": str(fx_id), "org": str(user.org_id)},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
