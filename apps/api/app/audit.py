"""Lightweight audit-log helper. Records before/after JSON for any tracked write.

Used by milestone updates, task CRUD, PRD versioning, risk edits, etc.
Failure to log NEVER blocks the underlying write — caught and swallowed."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from .models import AuditLog


def _serialize(o: Any) -> Any:
    if o is None or isinstance(o, (str, int, float, bool)):
        return o
    if isinstance(o, uuid.UUID):
        return str(o)
    try:
        import datetime as _dt
        if isinstance(o, (_dt.date, _dt.datetime)):
            return o.isoformat()
    except Exception:
        pass
    if hasattr(o, "__dict__"):
        return {k: _serialize(v) for k, v in o.__dict__.items() if not k.startswith("_")}
    return str(o)


def log(
    db: Session,
    *,
    org_id: uuid.UUID,
    user_id: uuid.UUID | None,
    entity: str,
    entity_id: str | uuid.UUID,
    action: str,
    before: dict | None = None,
    after: dict | None = None,
) -> None:
    try:
        row = AuditLog(
            org_id=org_id,
            user_id=user_id,
            entity=entity,
            entity_id=str(entity_id),
            action=action,
            before={k: _serialize(v) for k, v in (before or {}).items()} or None,
            after={k: _serialize(v) for k, v in (after or {}).items()} or None,
        )
        db.add(row)
    except Exception:
        # Audit must never block the underlying write.
        pass


def diff_orm(before_obj, after_obj, fields: list[str]) -> tuple[dict, dict]:
    """Return (before_dict, after_dict) of only the fields that actually changed."""
    b, a = {}, {}
    for f in fields:
        bv = getattr(before_obj, f, None)
        av = getattr(after_obj, f, None)
        if bv != av:
            b[f] = bv
            a[f] = av
    return b, a
