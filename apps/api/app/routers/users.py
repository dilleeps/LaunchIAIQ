import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import User
from ..security import hash_password


router = APIRouter(prefix="/users", tags=["users"])


class UserIn(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    default_role: str = "viewer"


@router.get("", dependencies=[Depends(require_role("global_admin"))])
def list_users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(User).filter(User.org_id == user.org_id).order_by(User.email).all()
    return [
        {
            "id": str(r.id),
            "email": r.email,
            "full_name": r.full_name,
            "default_role": r.default_role,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("", dependencies=[Depends(require_role("global_admin"))])
def create_user(body: UserIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    u = User(
        org_id=user.org_id,
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        default_role=body.default_role,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": str(u.id), "email": u.email, "default_role": u.default_role}
