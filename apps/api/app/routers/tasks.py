"""Tasks — sub-items under milestones. CRUD with audit logging."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from ..audit import log as audit_log
from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Launch, Milestone, Task, User


router = APIRouter(tags=["tasks"])

_WRITE = Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead", "medical", "market_access"))


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    milestone_id: uuid.UUID
    name: str
    status: str
    owner_user_id: Optional[uuid.UUID] = None
    due_date: Optional[date] = None


class TaskIn(BaseModel):
    name: str
    status: str = "Not Started"
    owner_user_id: Optional[uuid.UUID] = None
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    owner_user_id: Optional[uuid.UUID] = None
    due_date: Optional[date] = None


def _owned_milestone(db: Session, milestone_id: uuid.UUID, org_id: uuid.UUID) -> Milestone:
    ms = (
        db.query(Milestone)
        .join(Launch, Launch.id == Milestone.launch_id)
        .filter(Milestone.id == milestone_id, Launch.org_id == org_id)
        .first()
    )
    if not ms:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Milestone not found")
    return ms


@router.get("/milestones/{milestone_id}/tasks", response_model=list[TaskOut])
def list_tasks(milestone_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _owned_milestone(db, milestone_id, user.org_id)
    return db.query(Task).filter(Task.milestone_id == milestone_id).order_by(Task.due_date.asc().nullslast()).all()


@router.post("/milestones/{milestone_id}/tasks", response_model=TaskOut, dependencies=[_WRITE])
def create_task(
    milestone_id: uuid.UUID,
    body: TaskIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _owned_milestone(db, milestone_id, user.org_id)
    t = Task(milestone_id=milestone_id, **body.model_dump())
    db.add(t)
    db.flush()
    audit_log(
        db, org_id=user.org_id, user_id=user.id,
        entity="task", entity_id=t.id, action="create",
        after={"name": t.name, "status": t.status, "due_date": t.due_date, "milestone_id": milestone_id},
    )
    db.commit()
    db.refresh(t)
    return t


@router.patch("/tasks/{task_id}", response_model=TaskOut, dependencies=[_WRITE])
def update_task(
    task_id: uuid.UUID,
    body: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    t = (
        db.query(Task)
        .join(Milestone, Milestone.id == Task.milestone_id)
        .join(Launch, Launch.id == Milestone.launch_id)
        .filter(Task.id == task_id, Launch.org_id == user.org_id)
        .first()
    )
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")

    tracked = ["name", "status", "owner_user_id", "due_date"]
    before_snap = {f: getattr(t, f) for f in tracked}
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(t, k, v)

    before, after = {}, {}
    for f in tracked:
        nv = getattr(t, f)
        if before_snap[f] != nv:
            before[f] = before_snap[f]
            after[f] = nv
    if before:
        audit_log(
            db, org_id=user.org_id, user_id=user.id,
            entity="task", entity_id=t.id, action="update",
            before=before, after=after,
        )
    db.commit()
    db.refresh(t)
    return t


@router.delete("/tasks/{task_id}", status_code=204, dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead"))])
def delete_task(task_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    t = (
        db.query(Task)
        .join(Milestone, Milestone.id == Task.milestone_id)
        .join(Launch, Launch.id == Milestone.launch_id)
        .filter(Task.id == task_id, Launch.org_id == user.org_id)
        .first()
    )
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    audit_log(
        db, org_id=user.org_id, user_id=user.id,
        entity="task", entity_id=t.id, action="delete",
        before={"name": t.name, "milestone_id": t.milestone_id},
    )
    db.delete(t)
    db.commit()
