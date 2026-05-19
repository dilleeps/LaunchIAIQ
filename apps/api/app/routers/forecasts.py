import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Forecast, Launch, User
from ..schemas import ForecastOut


router = APIRouter(tags=["forecasts"])


class DriverIn(BaseModel):
    driver: str  # e.g. 'penetration', 'price', 'share'
    low: float
    base: float
    high: float


@router.get("/launches/{launch_id}/forecast", response_model=list[ForecastOut])
def list_forecasts(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    return db.query(Forecast).filter(Forecast.launch_id == launch_id).order_by(Forecast.version.desc()).all()


def _current_forecast(db: Session, launch_id: uuid.UUID) -> Optional[Forecast]:
    return (
        db.query(Forecast)
        .filter(Forecast.launch_id == launch_id, Forecast.is_current == True)  # noqa: E712
        .order_by(Forecast.version.desc())
        .first()
    )


@router.post("/launches/{launch_id}/forecast/drivers")
def set_driver(
    launch_id: uuid.UUID,
    body: DriverIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    fc = _current_forecast(db, launch_id)
    if not fc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No current forecast on this launch")
    # Upsert by (forecast_id, driver)
    existing = db.execute(
        text("SELECT id FROM forecast_drivers WHERE forecast_id = :fid AND driver = :d"),
        {"fid": str(fc.id), "d": body.driver},
    ).mappings().first()
    if existing:
        db.execute(
            text("UPDATE forecast_drivers SET low = :l, base = :b, high = :h WHERE id = :id"),
            {"id": existing["id"], "l": body.low, "b": body.base, "h": body.high},
        )
        did = existing["id"]
    else:
        did = uuid.uuid4()
        db.execute(
            text(
                "INSERT INTO forecast_drivers (id, forecast_id, driver, low, base, high) "
                "VALUES (:id, :fid, :d, :l, :b, :h)"
            ),
            {"id": str(did), "fid": str(fc.id), "d": body.driver, "l": body.low, "b": body.base, "h": body.high},
        )
    db.commit()
    return {"id": str(did), "forecast_id": str(fc.id), "driver": body.driver}


@router.get("/launches/{launch_id}/sensitivity")
def sensitivity(
    launch_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    fc = _current_forecast(db, launch_id)
    if not fc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No current forecast")
    drivers = db.execute(
        text("SELECT driver, low, base, high FROM forecast_drivers WHERE forecast_id = :fid"),
        {"fid": str(fc.id)},
    ).mappings().all()

    base_patients = [fc.y1_patients or 0, fc.y2_patients or 0, fc.y3_patients or 0]
    base_price = [fc.y1_net_price or 0.0, fc.y2_net_price or 0.0, fc.y3_net_price or 0.0]

    def factor(scenario: str, driver_name: str) -> float:
        for d in drivers:
            if d["driver"] == driver_name:
                return float(d[scenario])
        return 1.0

    scenarios = []
    for label in ("low", "base", "high"):
        pen = factor(label, "penetration")
        prc = factor(label, "price")
        shr = factor(label, "share")
        years = []
        for i in range(3):
            p = base_patients[i] * pen * shr
            price = base_price[i] * prc
            years.append({"year": i + 1, "patients": round(p, 1), "net_price": round(price, 2), "revenue": round(p * price, 2)})
        scenarios.append({
            "scenario": label,
            "factors": {"penetration": pen, "price": prc, "share": shr},
            "currency": fc.currency,
            "years": years,
            "total_revenue": round(sum(y["revenue"] for y in years), 2),
        })
    return {"launch_id": str(launch_id), "forecast_id": str(fc.id), "scenarios": scenarios}
