"""Launch readiness scorecard — composite score (0-100) per launch with workstream breakdown.

Score = weighted avg of workstream scores - risk penalty - gate penalty
Workstream score = sum(weight × completion) / sum(weight) × 100
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Launch, Milestone, Risk, RiskLaunchLink, User, Workstream


router = APIRouter(tags=["readiness"])


# Workstream weights for the composite score (tuned for pharma launches)
WORKSTREAM_WEIGHTS = {
    "Regulatory":    30,
    "Market Access": 25,
    "Commercial":    20,
    "Medical":       15,
    "Supply Chain":  10,
    "Compliance":     5,
}


def _workstream_score(db: Session, launch_id: uuid.UUID) -> dict[str, dict]:
    """Per-workstream completion %, weighted by milestone.weight."""
    rows = db.execute(text("""
        SELECT w.name AS workstream,
               COALESCE(SUM(m.weight) FILTER (WHERE m.status = 'Complete'), 0) AS done,
               COALESCE(SUM(m.weight), 0) AS total,
               COUNT(*) FILTER (WHERE m.status = 'Complete') AS done_count,
               COUNT(*) AS total_count
        FROM workstreams w
        LEFT JOIN milestones m ON m.workstream_id = w.id AND m.launch_id = :lid
        GROUP BY w.name
        ORDER BY w.name
    """), {"lid": str(launch_id)}).mappings().all()
    out = {}
    for r in rows:
        total = float(r["total"] or 0)
        done = float(r["done"] or 0)
        out[r["workstream"]] = {
            "score": round((done / total) * 100, 1) if total > 0 else None,
            "done_weight": done,
            "total_weight": total,
            "done_count": r["done_count"],
            "total_count": r["total_count"],
        }
    return out


def _gate_status(db: Session, launch: Launch) -> dict:
    """Pass/at-risk/pending status of L-180, L-90, L-30 readiness gates."""
    today = date.today()
    tgt = launch.target_launch_date
    if not tgt:
        return {"L-180": "n/a", "L-90": "n/a", "L-30": "n/a", "L+0": "n/a"}

    gates = []
    for name, days_before in (("L-180", 180), ("L-90", 90), ("L-30", 30), ("L+0", 0)):
        gate_date = tgt - timedelta(days=days_before)
        passed = today > gate_date
        ms_due = db.query(Milestone).filter(
            Milestone.launch_id == launch.id,
            Milestone.target_date.is_not(None),
            Milestone.target_date <= gate_date,
        ).all()
        total = len(ms_due)
        done = sum(1 for m in ms_due if m.status == "Complete")
        completion = (done / total) if total > 0 else 1.0

        if not passed and completion >= 0.7:
            status_label = "on-track"
        elif not passed and completion >= 0.4:
            status_label = "at-risk"
        elif not passed:
            status_label = "behind"
        elif passed and completion >= 0.85:
            status_label = "passed"
        elif passed and completion >= 0.6:
            status_label = "passed-with-gaps"
        else:
            status_label = "failed"
        gates.append({
            "gate": name, "date": gate_date.isoformat(),
            "completion_pct": round(completion * 100, 1),
            "done": done, "total": total,
            "status": status_label,
        })
    return gates


@router.get("/launches/{launch_id}/readiness")
def launch_readiness(
    launch_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    launch = db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first()
    if not launch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")

    ws_scores = _workstream_score(db, launch_id)

    # Composite: weighted average of workstream scores, weighted by configured business priority
    total_w, weighted = 0.0, 0.0
    for ws, weight in WORKSTREAM_WEIGHTS.items():
        s = ws_scores.get(ws, {}).get("score")
        if s is None:
            continue
        weighted += s * weight
        total_w += weight
    composite = weighted / total_w if total_w else 0

    # Risk penalty: -5 per open high-risk
    high_risks = (
        db.query(Risk)
        .join(RiskLaunchLink, RiskLaunchLink.risk_id == Risk.id)
        .filter(
            RiskLaunchLink.launch_id == launch_id,
            Risk.status != "Closed",
            Risk.score >= 6,
        )
        .count()
    )
    risk_penalty = high_risks * 5

    gates = _gate_status(db, launch)
    failed_gates = sum(1 for g in gates if isinstance(g, dict) and g["status"] in ("failed", "behind"))
    gate_penalty = failed_gates * 7

    final_score = max(0.0, min(100.0, composite - risk_penalty - gate_penalty))

    if final_score >= 80:    band = "Ready"
    elif final_score >= 60:  band = "Tracking"
    elif final_score >= 40:  band = "At risk"
    else:                    band = "Behind"

    return {
        "launch_id": str(launch_id),
        "launch_code": launch.launch_code,
        "asset": launch.asset.brand_name,
        "country": launch.country.name,
        "target_launch_date": launch.target_launch_date.isoformat() if launch.target_launch_date else None,
        "overall_rag": launch.overall_rag,
        "composite_score": round(final_score, 1),
        "band": band,
        "components": {
            "milestone_score": round(composite, 1),
            "risk_penalty": risk_penalty,
            "gate_penalty": gate_penalty,
            "high_risks_open": high_risks,
        },
        "workstreams": [
            {"name": w, "weight_pct": wgt, **ws_scores.get(w, {"score": None, "done_count": 0, "total_count": 0})}
            for w, wgt in WORKSTREAM_WEIGHTS.items()
        ],
        "gates": gates,
    }


@router.get("/portfolio/readiness")
def portfolio_readiness(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Readiness summary for every launch in the org — for the Readiness dashboard."""
    launches = db.query(Launch).filter(Launch.org_id == user.org_id).order_by(Launch.launch_code).all()
    out = []
    for ln in launches:
        # Reuse launch_readiness logic inline for performance (avoid 20 separate calls)
        ws_scores = _workstream_score(db, ln.id)
        total_w, weighted = 0.0, 0.0
        for ws, weight in WORKSTREAM_WEIGHTS.items():
            s = ws_scores.get(ws, {}).get("score")
            if s is None:
                continue
            weighted += s * weight
            total_w += weight
        composite = weighted / total_w if total_w else 0
        hr = (
            db.query(Risk)
            .join(RiskLaunchLink, RiskLaunchLink.risk_id == Risk.id)
            .filter(RiskLaunchLink.launch_id == ln.id, Risk.status != "Closed", Risk.score >= 6)
            .count()
        )
        gates = _gate_status(db, ln)
        failed = sum(1 for g in gates if isinstance(g, dict) and g["status"] in ("failed", "behind"))
        score = max(0.0, min(100.0, composite - hr * 5 - failed * 7))
        out.append({
            "launch_id": str(ln.id),
            "launch_code": ln.launch_code,
            "asset": ln.asset.brand_name,
            "country": ln.country.name,
            "target_launch_date": ln.target_launch_date.isoformat() if ln.target_launch_date else None,
            "overall_rag": ln.overall_rag,
            "composite_score": round(score, 1),
            "band": "Ready" if score >= 80 else "Tracking" if score >= 60 else "At risk" if score >= 40 else "Behind",
            "workstreams": {w: ws_scores.get(w, {}).get("score") for w in WORKSTREAM_WEIGHTS},
            "high_risks": hr,
        })
    return out
