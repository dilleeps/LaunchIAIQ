import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
_DEP_WRITE = Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead"))
from ..models import Dependency, Launch, User
from ..schemas import DependencyIn, DependencyOut


router = APIRouter(tags=["dependencies"])


@router.get("/dependencies", response_model=list[DependencyOut])
def list_deps(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Dependency).filter(Dependency.org_id == user.org_id).all()


@router.post("/dependencies", response_model=DependencyOut, dependencies=[_DEP_WRITE])
def create_dep(body: DependencyIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dep = Dependency(org_id=user.org_id, created_by=user.id, **body.model_dump())
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


@router.delete("/dependencies/{dep_id}", status_code=204, dependencies=[_DEP_WRITE])
def delete_dep(dep_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    dep = db.query(Dependency).filter(Dependency.id == dep_id, Dependency.org_id == user.org_id).first()
    if not dep:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(dep)
    db.commit()


@router.get("/launches/{launch_id}/downstream")
def downstream(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    launch = db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first()
    if not launch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    sql = text("""
        WITH RECURSIVE walk(source_type, source_id, target_type, target_id, link_type, depth) AS (
            SELECT source_type, source_id, target_type, target_id, link_type, 1
              FROM dependencies
             WHERE org_id = :org_id AND source_type = 'launch' AND source_id = :launch_id
            UNION
            SELECT d.source_type, d.source_id, d.target_type, d.target_id, d.link_type, w.depth + 1
              FROM dependencies d
              JOIN walk w ON d.source_type = w.target_type AND d.source_id = w.target_id
             WHERE d.org_id = :org_id AND w.depth < 6
        )
        SELECT * FROM walk
    """)
    rows = db.execute(sql, {"org_id": str(user.org_id), "launch_id": str(launch_id)}).mappings().all()
    return [dict(r) for r in rows]
