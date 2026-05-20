import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Forecast, Launch, User


router = APIRouter(tags=["variance"])

THRESHOLD_PCT = 10.0


class ActualIn(BaseModel):
    period: str  # YYYY-MM
    net_sales: Optional[float] = None
    patients: Optional[int] = None
    source: str = "manual"


def _monthly_targets(fc: Forecast) -> dict[str, dict[str, float]]:
    """Return {metric: {'monthly_patients': v, 'monthly_net_sales': v}} for Y1 simple pro-rata."""
    y1p = fc.y1_patients or 0
    y1pr = fc.y1_net_price or 0.0
    return {
        "patients": y1p / 12.0,
        "net_sales": (y1p * y1pr) / 12.0,
    }


@router.post("/launches/{launch_id}/actuals", dependencies=[Depends(require_role("global_admin", "finance"))])
def post_actual(
    launch_id: uuid.UUID,
    body: ActualIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")

    # Upsert actual
    existing = db.execute(
        text("SELECT id FROM actuals WHERE launch_id = :lid AND period = :p"),
        {"lid": str(launch_id), "p": body.period},
    ).mappings().first()
    if existing:
        db.execute(
            text(
                "UPDATE actuals SET net_sales = :ns, patients = :pt, source = :s WHERE id = :id"
            ),
            {"id": existing["id"], "ns": body.net_sales, "pt": body.patients, "s": body.source},
        )
        aid = existing["id"]
    else:
        aid = uuid.uuid4()
        db.execute(
            text(
                "INSERT INTO actuals (id, launch_id, period, net_sales, patients, source) "
                "VALUES (:id, :lid, :p, :ns, :pt, :s)"
            ),
            {
                "id": str(aid),
                "lid": str(launch_id),
                "p": body.period,
                "ns": body.net_sales,
                "pt": body.patients,
                "s": body.source,
            },
        )

    # Recompute variance vs current forecast (Y1 pro-rated monthly)
    fc = (
        db.query(Forecast)
        .filter(Forecast.launch_id == launch_id, Forecast.is_current == True)  # noqa: E712
        .order_by(Forecast.version.desc())
        .first()
    )
    if fc:
        targets = _monthly_targets(fc)
        for metric, monthly_target in targets.items():
            actual_val = body.patients if metric == "patients" else body.net_sales
            if actual_val is None or monthly_target == 0:
                continue
            variance = (actual_val - monthly_target) / monthly_target * 100.0
            status_val = "open" if abs(variance) >= THRESHOLD_PCT else "ok"
            # Upsert variance_alerts
            existing_v = db.execute(
                text(
                    "SELECT id FROM variance_alerts WHERE launch_id = :lid AND period = :p AND metric = :m"
                ),
                {"lid": str(launch_id), "p": body.period, "m": metric},
            ).mappings().first()
            if existing_v:
                db.execute(
                    text(
                        "UPDATE variance_alerts SET forecast_value = :f, actual_value = :a, "
                        "variance_pct = :v, threshold_pct = :t, status = :s WHERE id = :id"
                    ),
                    {
                        "id": existing_v["id"],
                        "f": monthly_target,
                        "a": actual_val,
                        "v": variance,
                        "t": THRESHOLD_PCT,
                        "s": status_val,
                    },
                )
            else:
                db.execute(
                    text(
                        "INSERT INTO variance_alerts (id, launch_id, period, metric, forecast_value, actual_value, variance_pct, threshold_pct, status) "
                        "VALUES (:id, :lid, :p, :m, :f, :a, :v, :t, :s)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "lid": str(launch_id),
                        "p": body.period,
                        "m": metric,
                        "f": monthly_target,
                        "a": actual_val,
                        "v": variance,
                        "t": THRESHOLD_PCT,
                        "s": status_val,
                    },
                )

    db.commit()
    return {"id": str(aid), "period": body.period}


@router.get("/launches/{launch_id}/variance-alerts")
def list_alerts(
    launch_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    rows = db.execute(
        text(
            "SELECT id, launch_id, period, metric, forecast_value, actual_value, variance_pct, threshold_pct, status "
            "FROM variance_alerts WHERE launch_id = :lid ORDER BY period DESC, metric"
        ),
        {"lid": str(launch_id)},
    ).mappings().all()
    return [dict(r) for r in rows]
