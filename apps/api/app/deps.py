import uuid
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .models import RoleAssignment, User
from .security import decode_token


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_role(*allowed: str):
    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.default_role not in allowed and user.default_role != "global_admin":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return _checker


def has_scope(db: Session, user: User, scope_type: str, scope_id: Optional[uuid.UUID]) -> bool:
    """Phase 1: global_admin sees all; viewer/role at org level sees all in org; granular scopes
    enforced when an assignment exists."""
    if user.default_role == "global_admin":
        return True
    q = db.query(RoleAssignment).filter(RoleAssignment.user_id == user.id)
    if not q.count():
        return True  # no granular assignments yet → fall back to org-wide via default_role
    if scope_id is None:
        return True
    return q.filter(
        RoleAssignment.scope_type == scope_type,
        RoleAssignment.scope_id == scope_id,
    ).count() > 0
