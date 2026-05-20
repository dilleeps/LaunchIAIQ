"""Launch budget — planned + actual OPEX by category, computed P&L vs revenue forecast."""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..audit import log as audit_log
from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Forecast, Launch, User


router = APIRouter(tags=["budget"])


# Standard pharma launch OPEX categories — could be made org-configurable later
DEFAULT_CATEGORIES = [
    "Field force",
    "MLR / promotional materials",
    "Congresses & symposia",
    "KOL & medical affairs",
    "Patient support program",
    "Market research",
    "Market access dossiers",
    "Supply & manufacturing",
    "Launch event",
    "Digital / omnichannel",
]


def _ensure_budget_tables(db: Session) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS launch_budgets (
            id uuid PRIMARY KEY,
            launch_id uuid NOT NULL,
            category text NOT NULL,
            planned_amount numeric(18, 2) DEFAULT 0,
            currency varchar(3) DEFAULT 'USD',
            notes text,
            created_at timestamp DEFAULT now(),
            UNIQUE(launch_id, category)
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS launch_spend (
            id uuid PRIMARY KEY,
            launch_id uuid NOT NULL,
            category text NOT NULL,
            period varchar(7) NOT NULL,
            actual_amount numeric(18, 2) NOT NULL,
            currency varchar(3) DEFAULT 'USD',
            source text DEFAULT 'manual',
            notes text,
            created_at timestamp DEFAULT now()
        )
    """))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_launch_spend_launch ON launch_spend(launch_id)"))
    db.commit()


class BudgetLineIn(BaseModel):
    category: str
    planned_amount: float
    currency: str = "USD"
    notes: Optional[str] = None


class SpendIn(BaseModel):
    category: str
    period: str  # YYYY-MM
    actual_amount: float
    currency: str = "USD"
    notes: Optional[str] = None


def _owned_launch(db: Session, launch_id: uuid.UUID, org_id: uuid.UUID) -> Launch:
    l = db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == org_id).first()
    if not l:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    return l


@router.get("/launches/{launch_id}/budget")
def get_budget(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _ensure_budget_tables(db)
    _owned_launch(db, launch_id, user.org_id)

    plan_rows = db.execute(text(
        "SELECT category, planned_amount, currency, notes FROM launch_budgets WHERE launch_id = :l"
    ), {"l": str(launch_id)}).mappings().all()
    spend_rows = db.execute(text("""
        SELECT category, SUM(actual_amount) AS spent
        FROM launch_spend WHERE launch_id = :l GROUP BY category
    """), {"l": str(launch_id)}).mappings().all()
    spent_by_cat = {r["category"]: float(r["spent"]) for r in spend_rows}

    seen = {r["category"] for r in plan_rows}
    lines = []
    for r in plan_rows:
        planned = float(r["planned_amount"])
        spent = spent_by_cat.get(r["category"], 0.0)
        lines.append({
            "category": r["category"],
            "planned": planned,
            "actual": spent,
            "remaining": planned - spent,
            "utilization_pct": round((spent / planned) * 100, 1) if planned > 0 else 0.0,
            "currency": r["currency"],
            "notes": r["notes"],
        })
    # Categories with spend but no plan
    for cat, spent in spent_by_cat.items():
        if cat not in seen:
            lines.append({
                "category": cat, "planned": 0, "actual": spent, "remaining": -spent,
                "utilization_pct": None, "currency": "USD", "notes": "(unbudgeted)",
            })

    # Compute P&L vs Y1 forecast revenue
    fc = db.query(Forecast).filter(
        Forecast.launch_id == launch_id, Forecast.is_current.is_(True)
    ).order_by(Forecast.version.desc()).first()
    y1_rev = (fc.y1_patients or 0) * (fc.y1_net_price or 0) if fc else 0

    total_planned = sum(l["planned"] for l in lines)
    total_actual = sum(l["actual"] for l in lines)
    return {
        "launch_id": str(launch_id),
        "currency": (fc.currency if fc else "USD"),
        "lines": sorted(lines, key=lambda x: -x["planned"]),
        "totals": {
            "planned": total_planned,
            "actual": total_actual,
            "remaining": total_planned - total_actual,
            "utilization_pct": round((total_actual / total_planned) * 100, 1) if total_planned > 0 else 0,
        },
        "pnl": {
            "y1_revenue_forecast": y1_rev,
            "y1_opex_planned": total_planned,
            "y1_gross_margin_pct": round(((y1_rev - total_planned) / y1_rev) * 100, 1) if y1_rev > 0 else None,
            "actual_to_date": total_actual,
        },
        "available_categories": DEFAULT_CATEGORIES,
    }


@router.post("/launches/{launch_id}/budget", dependencies=[Depends(require_role("global_admin", "global_brand_lead", "finance"))])
def upsert_budget_line(
    launch_id: uuid.UUID,
    body: BudgetLineIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ensure_budget_tables(db)
    _owned_launch(db, launch_id, user.org_id)
    existing = db.execute(text(
        "SELECT id, planned_amount FROM launch_budgets WHERE launch_id = :l AND category = :c"
    ), {"l": str(launch_id), "c": body.category}).mappings().first()
    if existing:
        db.execute(text(
            "UPDATE launch_budgets SET planned_amount = :p, currency = :cur, notes = :n WHERE id = :id"
        ), {"p": body.planned_amount, "cur": body.currency, "n": body.notes, "id": existing["id"]})
        audit_log(db, org_id=user.org_id, user_id=user.id, entity="budget", entity_id=existing["id"], action="update",
                  before={"planned": float(existing["planned_amount"])}, after={"planned": body.planned_amount})
    else:
        new_id = uuid.uuid4()
        db.execute(text(
            "INSERT INTO launch_budgets (id, launch_id, category, planned_amount, currency, notes) "
            "VALUES (:id, :l, :c, :p, :cur, :n)"
        ), {"id": str(new_id), "l": str(launch_id), "c": body.category,
            "p": body.planned_amount, "cur": body.currency, "n": body.notes})
        audit_log(db, org_id=user.org_id, user_id=user.id, entity="budget", entity_id=new_id, action="create",
                  after={"category": body.category, "planned": body.planned_amount})
    db.commit()
    return {"ok": True}


@router.post("/launches/{launch_id}/spend", dependencies=[Depends(require_role("global_admin", "global_brand_lead", "finance"))])
def record_spend(
    launch_id: uuid.UUID,
    body: SpendIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ensure_budget_tables(db)
    _owned_launch(db, launch_id, user.org_id)
    new_id = uuid.uuid4()
    db.execute(text(
        "INSERT INTO launch_spend (id, launch_id, category, period, actual_amount, currency, notes) "
        "VALUES (:id, :l, :c, :p, :a, :cur, :n)"
    ), {"id": str(new_id), "l": str(launch_id), "c": body.category, "p": body.period,
        "a": body.actual_amount, "cur": body.currency, "n": body.notes})
    audit_log(db, org_id=user.org_id, user_id=user.id, entity="spend", entity_id=new_id, action="create",
              after={"category": body.category, "period": body.period, "actual": body.actual_amount})
    db.commit()
    return {"id": str(new_id)}
