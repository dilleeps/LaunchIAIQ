import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Asset, Country, Launch, User
from ..schemas import LaunchIn, LaunchOut


router = APIRouter(prefix="/launches", tags=["launches"])


@router.get("", response_model=list[LaunchOut])
def list_launches(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Launch).filter(Launch.org_id == user.org_id).order_by(Launch.launch_code).all()
    return rows


@router.get("/{launch_id}", response_model=LaunchOut)
def get_launch(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    launch = db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first()
    if not launch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    return launch


@router.post(
    "",
    response_model=LaunchOut,
    dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead"))],
)
def create_launch(body: LaunchIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Asset).filter(Asset.id == body.asset_id, Asset.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown asset")
    if not db.query(Country).filter(Country.id == body.country_id).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown country")
    launch = Launch(org_id=user.org_id, **body.model_dump(exclude_none=True))
    db.add(launch)
    db.commit()
    db.refresh(launch)
    return launch
