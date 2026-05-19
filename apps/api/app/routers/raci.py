import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Launch, RaciEntry, User
from ..schemas import RaciOut


router = APIRouter(tags=["raci"])


@router.get("/launches/{launch_id}/raci", response_model=list[RaciOut])
def list_raci(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    return db.query(RaciEntry).filter(RaciEntry.launch_id == launch_id).all()
