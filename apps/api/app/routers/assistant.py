import uuid
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import Launch, Risk, RiskLaunchLink, User


router = APIRouter(prefix="/assistant", tags=["assistant"])


class RiskSummarizeIn(BaseModel):
    launch_id: uuid.UUID


class MitigationIn(BaseModel):
    risk_id: uuid.UUID


def _call_claude(prompt: str, max_tokens: int = 600) -> Optional[str]:
    if not settings.anthropic_api_key:
        return None
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.anthropic_model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            r.raise_for_status()
            data = r.json()
            blocks = data.get("content", [])
            return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    except httpx.HTTPError:
        return None


@router.post("/summarize-risks")
def summarize_risks(
    body: RiskSummarizeIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    launch = db.query(Launch).filter(Launch.id == body.launch_id, Launch.org_id == user.org_id).first()
    if not launch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    risks = (
        db.query(Risk)
        .join(RiskLaunchLink, RiskLaunchLink.risk_id == Risk.id)
        .filter(Risk.org_id == user.org_id, RiskLaunchLink.launch_id == launch.id)
        .order_by(Risk.score.desc())
        .all()
    )
    risk_lines = [
        f"- [{r.category or 'general'}] (L={r.likelihood}/I={r.impact}, score {r.score}) {r.description}"
        for r in risks
    ]

    if settings.anthropic_api_key and risks:
        prompt = (
            f"Summarize the following pharmaceutical launch risks for launch {launch.launch_code} "
            f"in 3 concise bullets focused on the most material exposures and what's blocking them. "
            f"Be specific.\n\nRisks:\n" + "\n".join(risk_lines)
        )
        text_out = _call_claude(prompt)
        if text_out:
            return {"mode": "live", "launch_code": launch.launch_code, "summary": text_out}

    # Offline fallback
    if not risks:
        summary = (
            "- No open risks logged for this launch yet.\n"
            "- Encourage workstream owners to log known exposures.\n"
            "- Re-run summary after the next launch governance meeting."
        )
    else:
        top = risks[:3]
        bullets = []
        for r in top:
            bullets.append(
                f"- {r.category or 'Risk'}: {r.description[:140]} (score {r.score}, status {r.status})."
            )
        while len(bullets) < 3:
            bullets.append("- No further high-priority risks beyond those listed above.")
        summary = "\n".join(bullets)
    return {"mode": "offline", "launch_code": launch.launch_code, "summary": summary}


@router.post("/suggest-mitigation")
def suggest_mitigation(
    body: MitigationIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    risk = db.query(Risk).filter(Risk.id == body.risk_id, Risk.org_id == user.org_id).first()
    if not risk:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Risk not found")

    if settings.anthropic_api_key:
        prompt = (
            f"You are an experienced pharma launch readiness consultant. Suggest 2-3 concrete, "
            f"actionable mitigation tactics for this risk. Each tactic should be one short sentence, "
            f"action verb first.\n\nRisk category: {risk.category}\n"
            f"Description: {risk.description}\n"
            f"Current mitigation: {risk.mitigation or 'none'}"
        )
        out = _call_claude(prompt, max_tokens=400)
        if out:
            return {"mode": "live", "risk_id": str(risk.id), "suggestions": out}

    # Offline canned suggestions by category
    cat = (risk.category or "").lower()
    if "supply" in cat:
        suggestions = [
            "Qualify a secondary CMO/CDMO by L-90 and stage validation lots in parallel.",
            "Pre-build 6 months of finished-goods safety stock in regional 3PL warehouses.",
            "Add weekly supply S&OP review with launch-tier escalation triggers.",
        ]
    elif "access" in cat or "market" in cat or "price" in cat:
        suggestions = [
            "Develop outcomes-based contract proposals tailored to the top 5 payers/PBMs.",
            "Run a pricing sensitivity workshop with HEOR to refine the value dossier.",
            "Pre-engage HTA bodies with early scientific advice meetings before submission.",
        ]
    elif "reg" in cat:
        suggestions = [
            "Schedule a Type B / pre-submission meeting with the agency in the next 60 days.",
            "Build a labeling negotiation playbook with fallback positions on key claims.",
            "Stand up a daily reg-team standup once the filing window opens.",
        ]
    else:
        suggestions = [
            "Assign a single accountable owner with weekly status reporting to the launch lead.",
            "Add a leading-indicator KPI tied to this risk on the launch dashboard.",
            "Define a clear escalation trigger and route to the launch steering committee.",
        ]
    return {"mode": "offline", "risk_id": str(risk.id), "suggestions": "\n".join(f"- {s}" for s in suggestions)}
