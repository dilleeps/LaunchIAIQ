import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Organization, User
from ..schemas import LoginIn, RegisterOrgIn, TokenOut, UserOut
from ..security import create_access_token, hash_password, verify_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    return TokenOut(
        access_token=create_access_token(
            str(user.id),
            extra={"org_id": str(user.org_id), "role": user.default_role},
        )
    )


@router.post("/register-org", response_model=TokenOut)
def register_org(body: RegisterOrgIn, db: Session = Depends(get_db)):
    if db.query(Organization).filter(Organization.slug == body.org_slug).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Org slug taken")
    if db.query(User).filter(User.email == body.admin_email).first():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")
    org = Organization(name=body.org_name, slug=body.org_slug)
    db.add(org)
    db.flush()
    admin = User(
        org_id=org.id,
        email=body.admin_email,
        password_hash=hash_password(body.admin_password),
        full_name=body.admin_full_name,
        default_role="global_admin",
    )
    db.add(admin)
    db.commit()
    return TokenOut(
        access_token=create_access_token(
            str(admin.id), extra={"org_id": str(admin.org_id), "role": admin.default_role}
        )
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
