"""Auto-RAG rollup. Computes a launch's overall_rag from milestones + risks + variance.

Phase 1: invoked on demand (e.g. nightly job, after milestone/risk write).
Phase 2 will be wrapped in a materialized view + triggers."""
from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Launch, Milestone, Risk, RiskLaunchLink


def compute_rag(db: Session, launch_id) -> str:
    ms = db.query(Milestone).filter(Milestone.launch_id == launch_id).all()
    total_weight = sum(m.weight for m in ms) or 1.0
    done_weight = sum(m.weight for m in ms if m.status == "Complete")
    pct = done_weight / total_weight

    gate_blocker = any(m.is_gate and m.status in ("At Risk", "Delayed", "Blocked") for m in ms)

    high_risks = (
        db.query(Risk)
        .join(RiskLaunchLink, RiskLaunchLink.risk_id == Risk.id)
        .filter(RiskLaunchLink.launch_id == launch_id, Risk.status != "Closed", Risk.score >= 6)
        .count()
    )

    if gate_blocker or high_risks >= 2:
        return "Red"
    if pct < 0.4 or high_risks >= 1:
        return "Amber"
    return "Green"


def recompute_and_save(db: Session, launch_id) -> str:
    rag = compute_rag(db, launch_id)
    launch = db.get(Launch, launch_id)
    if launch:
        launch.overall_rag = rag
        db.commit()
    return rag
