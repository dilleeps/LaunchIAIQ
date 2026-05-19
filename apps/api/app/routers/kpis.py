import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import KPI, Launch, User
from ..schemas import KPIOut


router = APIRouter(tags=["kpis"])


@router.get("/launches/{launch_id}/kpis", response_model=list[KPIOut])
def list_kpis(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    return db.query(KPI).filter(KPI.launch_id == launch_id).order_by(KPI.category, KPI.name).all()
