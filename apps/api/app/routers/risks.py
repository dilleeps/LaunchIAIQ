import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Launch, Risk, RiskLaunchLink, User
from ..schemas import RiskIn, RiskOut


router = APIRouter(prefix="/risks", tags=["risks"])

_SCORE_MAP = {"L": 1, "M": 2, "H": 3}


def _score(l: str, i: str) -> int:
    return _SCORE_MAP.get(l, 2) * _SCORE_MAP.get(i, 2)


@router.get("", response_model=list[RiskOut])
def list_risks(
    launch_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(Risk).filter(Risk.org_id == user.org_id)
    if launch_id:
        q = q.join(RiskLaunchLink, RiskLaunchLink.risk_id == Risk.id).filter(
            RiskLaunchLink.launch_id == launch_id
        )
    return q.order_by(Risk.score.desc()).all()


@router.post("", response_model=RiskOut, dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead", "medical", "market_access"))])
def create_risk(body: RiskIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    data = body.model_dump(exclude={"launch_ids"})
    risk = Risk(org_id=user.org_id, score=_score(body.likelihood, body.impact), **data)
    db.add(risk)
    db.flush()
    for lid in body.launch_ids:
        if db.query(Launch).filter(Launch.id == lid, Launch.org_id == user.org_id).first():
            db.add(RiskLaunchLink(risk_id=risk.id, launch_id=lid))
    db.commit()
    db.refresh(risk)
    return risk
