"""Admin utility endpoints: trigger seeds, inspect counts. Admin-only."""
from __future__ import annotations

import importlib

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import User


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/counts", dependencies=[Depends(require_role("global_admin"))])
def counts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """One-shot diagnostic — what's actually in this org."""
    rows = db.execute(text("""
        SELECT
          (SELECT COUNT(*) FROM organizations) AS organizations,
          (SELECT COUNT(*) FROM users WHERE org_id = :o) AS users,
          (SELECT COUNT(*) FROM assets WHERE org_id = :o) AS assets,
          (SELECT COUNT(*) FROM launches WHERE org_id = :o) AS launches,
          (SELECT COUNT(*) FROM milestones m JOIN launches l ON l.id = m.launch_id WHERE l.org_id = :o) AS milestones,
          (SELECT COUNT(*) FROM forecasts f JOIN launches l ON l.id = f.launch_id WHERE l.org_id = :o) AS forecasts,
          (SELECT COUNT(*) FROM risks WHERE org_id = :o) AS risks,
          (SELECT COUNT(*) FROM dependencies WHERE org_id = :o) AS dependencies,
          (SELECT COUNT(*) FROM integration_connectors WHERE org_id = :o) AS connectors,
          (SELECT COUNT(*) FROM market_intel_records) AS market_intel_records_global,
          (SELECT COUNT(*) FROM competitive_intel WHERE org_id = :o) AS competitor_records
    """), {"o": str(user.org_id)}).mappings().first()
    return dict(rows)


@router.post("/reseed/base", dependencies=[Depends(require_role("global_admin"))])
def reseed_base():
    try:
        mod = importlib.import_module("app.seed")
        importlib.reload(mod)
        mod.run()
        return {"ok": True, "ran": "app.seed"}
    except Exception as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Base seed failed: {exc}")


@router.post("/reseed/takeda", dependencies=[Depends(require_role("global_admin"))])
def reseed_takeda():
    try:
        mod = importlib.import_module("app.seed_takeda")
        importlib.reload(mod)
        mod.run()
        return {"ok": True, "ran": "app.seed_takeda"}
    except Exception as exc:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Takeda seed failed: {exc}")


@router.post("/reseed/all", dependencies=[Depends(require_role("global_admin"))])
def reseed_all():
    results = {}
    for name in ("app.seed", "app.seed_takeda"):
        try:
            mod = importlib.import_module(name)
            importlib.reload(mod)
            mod.run()
            results[name] = "ok"
        except Exception as exc:
            results[name] = f"error: {exc}"
    return results
