from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Asset, User
from ..schemas import AssetIn, AssetOut


router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[AssetOut])
def list_assets(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Asset).filter(Asset.org_id == user.org_id).order_by(Asset.brand_name).all()


@router.post("", response_model=AssetOut, dependencies=[Depends(require_role("global_admin", "global_brand_lead"))])
def create_asset(body: AssetIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    asset = Asset(org_id=user.org_id, **body.model_dump(exclude_none=True))
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
