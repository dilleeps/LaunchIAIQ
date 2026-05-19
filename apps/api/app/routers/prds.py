import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import PRD, Launch, PRDFieldHistory, PRDVersion, User
from ..schemas import PRDOut, PRDUpdateIn


router = APIRouter(tags=["prds"])


def _flatten(d: dict, prefix: str = "") -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in (d or {}).items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = "" if v is None else str(v)
    return out


def _current(db: Session, prd: PRD) -> PRDVersion | None:
    return (
        db.query(PRDVersion)
        .filter(PRDVersion.prd_id == prd.id, PRDVersion.version == prd.current_version)
        .first()
    )


@router.get("/launches/{launch_id}/prd", response_model=PRDOut)
def get_prd(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    launch = db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first()
    if not launch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    prd = db.query(PRD).filter(PRD.launch_id == launch_id).first()
    if not prd:
        prd = PRD(launch_id=launch_id, current_version=1)
        db.add(prd)
        db.flush()
        db.add(PRDVersion(prd_id=prd.id, version=1, payload={}, is_baseline=True))
        db.commit()
        db.refresh(prd)
    ver = _current(db, prd)
    return PRDOut(id=prd.id, launch_id=launch_id, current_version=prd.current_version, payload=ver.payload if ver else {})


@router.put("/launches/{launch_id}/prd", response_model=PRDOut)
def update_prd(
    launch_id: uuid.UUID,
    body: PRDUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    launch = db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first()
    if not launch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    prd = db.query(PRD).filter(PRD.launch_id == launch_id).first()
    if not prd:
        prd = PRD(launch_id=launch_id, current_version=0)
        db.add(prd)
        db.flush()
    current = _current(db, prd)
    old_payload = current.payload if current else {}
    # Diff and record field history
    old_flat = _flatten(old_payload)
    new_flat = _flatten(body.payload)
    for key in set(old_flat) | set(new_flat):
        if old_flat.get(key, "") != new_flat.get(key, ""):
            section, _, field = key.partition(".")
            db.add(
                PRDFieldHistory(
                    prd_id=prd.id,
                    section=section,
                    field=field or section,
                    old_value=old_flat.get(key),
                    new_value=new_flat.get(key),
                    changed_by=user.id,
                    comment=body.change_reason,
                )
            )
    prd.current_version += 1
    db.add(
        PRDVersion(
            prd_id=prd.id,
            version=prd.current_version,
            payload=body.payload,
            change_reason=body.change_reason,
            created_by=user.id,
        )
    )
    db.commit()
    db.refresh(prd)
    return PRDOut(id=prd.id, launch_id=launch_id, current_version=prd.current_version, payload=body.payload)


@router.get("/prds/{prd_id}/history")
def history(prd_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(PRDFieldHistory)
        .filter(PRDFieldHistory.prd_id == prd_id)
        .order_by(PRDFieldHistory.changed_at.desc())
        .all()
    )
    return [
        {
            "section": r.section,
            "field": r.field,
            "old_value": r.old_value,
            "new_value": r.new_value,
            "changed_at": r.changed_at.isoformat() if r.changed_at else None,
            "comment": r.comment,
        }
        for r in rows
    ]
