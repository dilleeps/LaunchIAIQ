import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Launch, Milestone, User
from ..schemas import MilestoneOut, MilestoneUpdateIn


router = APIRouter(tags=["milestones"])


@router.get("/launches/{launch_id}/milestones", response_model=list[MilestoneOut])
def list_for_launch(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    launch = db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first()
    if not launch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    return db.query(Milestone).filter(Milestone.launch_id == launch_id).order_by(Milestone.target_date.asc().nullslast()).all()


@router.get("/milestones/upcoming", response_model=list[MilestoneOut])
def upcoming(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cutoff = date.today() + timedelta(days=days)
    return (
        db.query(Milestone)
        .join(Launch, Launch.id == Milestone.launch_id)
        .filter(
            Launch.org_id == user.org_id,
            Milestone.target_date.is_not(None),
            Milestone.target_date <= cutoff,
            Milestone.status != "Complete",
        )
        .order_by(Milestone.target_date.asc())
        .all()
    )


@router.patch("/milestones/{milestone_id}", response_model=MilestoneOut)
def update_milestone(
    milestone_id: uuid.UUID,
    body: MilestoneUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ms = (
        db.query(Milestone)
        .join(Launch, Launch.id == Milestone.launch_id)
        .filter(Milestone.id == milestone_id, Launch.org_id == user.org_id)
        .first()
    )
    if not ms:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(ms, k, v)
    db.commit()
    db.refresh(ms)
    return ms
