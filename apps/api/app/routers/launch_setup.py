"""Launch setup wizard — templates, key assumptions, meetings, team members,
hierarchical activity tree. Pharma-industry standard launch framework model.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Asset, Country, Launch, User
from ..data.launch_templates import TEMPLATES, list_templates, get_template, flatten_for_seed


router = APIRouter(tags=["launch-setup"])


# ============================================================================
# Templates
# ============================================================================

@router.get("/launch-templates")
def get_templates(user: User = Depends(get_current_user)):
    return list_templates()


@router.get("/launch-templates/{key}")
def get_template_detail(key: str, user: User = Depends(get_current_user)):
    t = get_template(key)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Template not found")
    return t


# ============================================================================
# Wizard — Create New Launch (creates launch + setup + meetings + activities)
# ============================================================================

class MeetingIn(BaseModel):
    meeting_key: str
    name: str
    cadence: str
    day_of_month: Optional[int] = None
    offset_months_before_launch: Optional[int] = None
    scheduled_date: Optional[date] = None
    recurring: bool = False


class TeamMemberIn(BaseModel):
    user_id: Optional[uuid.UUID] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    role_label: str
    country_code: Optional[str] = None
    is_manager: bool = False
    therapy_area: Optional[str] = None


class AssumptionsIn(BaseModel):
    commercial_launch_date: Optional[date] = None
    regulatory_submission: Optional[date] = None
    regulatory_approval: Optional[date] = None
    pricing_submission: Optional[date] = None
    pricing_approval: Optional[date] = None
    reimbursement_submission: Optional[date] = None
    reimbursement_approval: Optional[date] = None
    trade_stock_available: Optional[date] = None
    phase3_results: Optional[date] = None
    amnog_dossier_submission: Optional[date] = None
    gba_decision: Optional[date] = None
    nhi_price_listing: Optional[date] = None
    mrp_value: Optional[float] = None
    mrp_currency: Optional[str] = "USD"
    mrp_year: Optional[int] = None
    cumulative_mrp: Optional[float] = None
    not_applicable: list[str] = []
    pending_confirmation: list[str] = []


class WizardCreateIn(BaseModel):
    # Step 1: identity
    launch_code: str
    template_key: str
    asset_id: uuid.UUID
    country_id: uuid.UUID
    indication_id: Optional[uuid.UUID] = None
    franchise: Optional[str] = None
    brand: Optional[str] = None
    indication_label: Optional[str] = None
    region: Optional[str] = None
    business_partner: Optional[str] = None
    local_launch_leader_user_id: Optional[uuid.UUID] = None
    launch_type: Optional[str] = None
    target_launch_date: Optional[date] = None
    # Step 2
    assumptions: AssumptionsIn = AssumptionsIn()
    # Step 3
    meetings: list[MeetingIn] = []
    # Step 4
    team_members: list[TeamMemberIn] = []


@router.post(
    "/launches/wizard",
    dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead"))],
)
def wizard_create(body: WizardCreateIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Validate FK targets are visible to this org
    asset = db.query(Asset).filter(Asset.id == body.asset_id, Asset.org_id == user.org_id).first()
    if not asset:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown asset")
    country = db.query(Country).filter(Country.id == body.country_id).first()
    if not country:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown country")
    tmpl = get_template(body.template_key)
    if not tmpl:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown launch template")

    # Create the Launch
    launch = Launch(
        org_id=user.org_id,
        launch_code=body.launch_code,
        asset_id=body.asset_id,
        country_id=body.country_id,
        indication_id=body.indication_id,
        launch_type=body.launch_type or tmpl["scope"],
        target_launch_date=body.target_launch_date or body.assumptions.commercial_launch_date,
        reg_approval_date=body.assumptions.regulatory_approval,
        country_launch_lead_user_id=body.local_launch_leader_user_id,
        status="Active",
        overall_rag="Green",
    )
    db.add(launch)
    db.flush()

    # launch_setup row
    a = body.assumptions
    db.execute(text("""
        INSERT INTO launch_setup (
            launch_id, template_key, franchise, brand, indication_label, region,
            business_partner, local_launch_leader_user_id,
            commercial_launch_date, regulatory_submission, regulatory_approval,
            pricing_submission, pricing_approval, reimbursement_submission,
            reimbursement_approval, trade_stock_available, phase3_results,
            amnog_dossier_submission, gba_decision, nhi_price_listing,
            mrp_value, mrp_currency, mrp_year, cumulative_mrp,
            not_applicable, pending_confirmation
        ) VALUES (
            :launch_id, :template_key, :franchise, :brand, :indication_label, :region,
            :business_partner, :local_lead,
            :cld, :rs, :ra, :ps, :pa, :rms, :rma, :tsa, :p3,
            :amnog, :gba, :nhi,
            :mrp_v, :mrp_c, :mrp_y, :cmrp,
            CAST(:na AS jsonb), CAST(:pc AS jsonb)
        )
        ON CONFLICT (launch_id) DO NOTHING
    """), {
        "launch_id": launch.id, "template_key": body.template_key,
        "franchise": body.franchise, "brand": body.brand or asset.brand_name,
        "indication_label": body.indication_label, "region": body.region or country.region,
        "business_partner": body.business_partner, "local_lead": body.local_launch_leader_user_id,
        "cld": a.commercial_launch_date, "rs": a.regulatory_submission, "ra": a.regulatory_approval,
        "ps": a.pricing_submission, "pa": a.pricing_approval,
        "rms": a.reimbursement_submission, "rma": a.reimbursement_approval,
        "tsa": a.trade_stock_available, "p3": a.phase3_results,
        "amnog": a.amnog_dossier_submission, "gba": a.gba_decision, "nhi": a.nhi_price_listing,
        "mrp_v": a.mrp_value, "mrp_c": a.mrp_currency, "mrp_y": a.mrp_year, "cmrp": a.cumulative_mrp,
        "na": _json_array(a.not_applicable), "pc": _json_array(a.pending_confirmation),
    })

    # Meetings — fall back to template defaults if none supplied
    meetings = body.meetings or [
        MeetingIn(
            meeting_key=m["key"], name=m["name"], cadence=m["cadence"],
            day_of_month=m["default"] if m["config_field"] == "day_of_month" else None,
            offset_months_before_launch=m["default"] if m["config_field"] == "offset_months_before_launch" else None,
            recurring=(m["cadence"] == "monthly"),
        )
        for m in tmpl["meetings"]
    ]
    for m in meetings:
        db.execute(text("""
            INSERT INTO launch_meetings (
                id, launch_id, meeting_key, name, cadence,
                day_of_month, offset_months_before_launch, scheduled_date, recurring
            ) VALUES (:id, :lid, :k, :n, :c, :dom, :off, :sd, :r)
            ON CONFLICT (launch_id, meeting_key) DO NOTHING
        """), {
            "id": uuid.uuid4(), "lid": launch.id, "k": m.meeting_key, "n": m.name, "c": m.cadence,
            "dom": m.day_of_month, "off": m.offset_months_before_launch,
            "sd": m.scheduled_date, "r": m.recurring,
        })

    # Team members
    for tm in body.team_members:
        db.execute(text("""
            INSERT INTO launch_team_members (
                id, launch_id, user_id, full_name, email, role_label,
                country_code, is_manager, therapy_area
            ) VALUES (:id, :lid, :uid, :fn, :em, :rl, :cc, :mgr, :ta)
        """), {
            "id": uuid.uuid4(), "lid": launch.id, "uid": tm.user_id,
            "fn": tm.full_name, "em": tm.email, "rl": tm.role_label,
            "cc": tm.country_code or country.code, "mgr": tm.is_manager, "ta": tm.therapy_area,
        })

    # Activity tree — seed from template
    _seed_activities(db, launch_id=launch.id, country_code=country.code, groups=tmpl["groups"])

    db.commit()
    return {
        "launch_id": str(launch.id),
        "launch_code": launch.launch_code,
        "template_key": body.template_key,
        "activities_created": len(flatten_for_seed(tmpl["groups"])),
        "meetings_created": len(meetings),
        "team_members_created": len(body.team_members),
    }


def _seed_activities(db: Session, *, launch_id: uuid.UUID, country_code: str, groups: list[dict]):
    rows = flatten_for_seed(groups)
    id_by_ordinal: dict[str, uuid.UUID] = {}
    for r in rows:
        new_id = uuid.uuid4()
        id_by_ordinal[r["ordinal"]] = new_id
        parent_id = id_by_ordinal.get(r["parent_ordinal"]) if r["parent_ordinal"] else None
        db.execute(text("""
            INSERT INTO launch_activities (
                id, launch_id, parent_id, group_key, group_name, ordinal, level,
                name, status, country_code, importance, manual_complete, assigned_count
            ) VALUES (
                :id, :lid, :pid, :gk, :gn, :ord, :lv,
                :nm, 'Not Started', :cc, :imp, false, 0
            )
            ON CONFLICT (launch_id, ordinal) DO NOTHING
        """), {
            "id": new_id, "lid": launch_id, "pid": parent_id,
            "gk": r["group_key"], "gn": r["group_name"],
            "ord": r["ordinal"], "lv": r["level"],
            "nm": r["name"], "cc": "Global" if r["level"] <= 2 else country_code,
            "imp": r["importance"],
        })


def _json_array(items: list[str]) -> str:
    import json
    return json.dumps(items or [])


# ============================================================================
# Setup retrieval / update
# ============================================================================

@router.get("/launches/{launch_id}/setup")
def get_setup(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    row = db.execute(text("SELECT * FROM launch_setup WHERE launch_id = :id"), {"id": launch_id}).mappings().first()
    return dict(row) if row else None


@router.put(
    "/launches/{launch_id}/assumptions",
    dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead"))],
)
def update_assumptions(launch_id: uuid.UUID, body: AssumptionsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    db.execute(text("""
        INSERT INTO launch_setup (launch_id) VALUES (:id)
        ON CONFLICT (launch_id) DO NOTHING
    """), {"id": launch_id})
    db.execute(text("""
        UPDATE launch_setup SET
            commercial_launch_date = :cld,
            regulatory_submission = :rs, regulatory_approval = :ra,
            pricing_submission = :ps, pricing_approval = :pa,
            reimbursement_submission = :rms, reimbursement_approval = :rma,
            trade_stock_available = :tsa, phase3_results = :p3,
            amnog_dossier_submission = :amnog, gba_decision = :gba, nhi_price_listing = :nhi,
            mrp_value = :mrp_v, mrp_currency = :mrp_c, mrp_year = :mrp_y, cumulative_mrp = :cmrp,
            not_applicable = CAST(:na AS jsonb), pending_confirmation = CAST(:pc AS jsonb),
            updated_at = now()
        WHERE launch_id = :id
    """), {
        "id": launch_id,
        "cld": body.commercial_launch_date, "rs": body.regulatory_submission, "ra": body.regulatory_approval,
        "ps": body.pricing_submission, "pa": body.pricing_approval,
        "rms": body.reimbursement_submission, "rma": body.reimbursement_approval,
        "tsa": body.trade_stock_available, "p3": body.phase3_results,
        "amnog": body.amnog_dossier_submission, "gba": body.gba_decision, "nhi": body.nhi_price_listing,
        "mrp_v": body.mrp_value, "mrp_c": body.mrp_currency, "mrp_y": body.mrp_year, "cmrp": body.cumulative_mrp,
        "na": _json_array(body.not_applicable), "pc": _json_array(body.pending_confirmation),
    })
    db.commit()
    return {"ok": True}


# ============================================================================
# Team members
# ============================================================================

@router.get("/launches/{launch_id}/team")
def get_team(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    rows = db.execute(text(
        "SELECT * FROM launch_team_members WHERE launch_id = :id ORDER BY is_manager DESC, role_label, full_name"
    ), {"id": launch_id}).mappings().all()
    return [dict(r) for r in rows]


@router.post(
    "/launches/{launch_id}/team",
    dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead"))],
)
def add_team_member(launch_id: uuid.UUID, body: TeamMemberIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    launch = db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first()
    if not launch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    new_id = uuid.uuid4()
    db.execute(text("""
        INSERT INTO launch_team_members (id, launch_id, user_id, full_name, email, role_label, country_code, is_manager, therapy_area)
        VALUES (:id, :lid, :uid, :fn, :em, :rl, :cc, :mgr, :ta)
    """), {
        "id": new_id, "lid": launch_id, "uid": body.user_id,
        "fn": body.full_name, "em": body.email, "rl": body.role_label,
        "cc": body.country_code or launch.country.code, "mgr": body.is_manager, "ta": body.therapy_area,
    })
    db.commit()
    return {"id": str(new_id)}


@router.delete(
    "/launches/{launch_id}/team/{member_id}",
    dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead"))],
)
def remove_team_member(launch_id: uuid.UUID, member_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    db.execute(text("DELETE FROM launch_team_members WHERE id = :id AND launch_id = :lid"),
               {"id": member_id, "lid": launch_id})
    db.commit()
    return {"ok": True}


# ============================================================================
# My Launch Team — cross-launch team roster (for "Welcome to My Launch" view)
# ============================================================================

@router.get("/my-launch-team")
def my_launch_team(
    therapy_area: Optional[str] = None,
    brand: Optional[str] = None,
    indication: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Aggregate team members across launches that the current user has visibility into.
    Filters: therapy_area, brand, indication, country."""
    sql = """
        SELECT tm.id, tm.launch_id, tm.user_id, tm.full_name, tm.email, tm.role_label,
               tm.country_code, tm.is_manager, tm.therapy_area,
               l.launch_code,
               a.brand_name AS brand,
               a.therapeutic_area AS asset_therapy_area,
               c.name AS country_name,
               i.label AS indication_label
        FROM launch_team_members tm
        JOIN launches l ON l.id = tm.launch_id AND l.org_id = :org_id
        JOIN assets a ON a.id = l.asset_id
        JOIN countries c ON c.id = l.country_id
        LEFT JOIN indications i ON i.id = l.indication_id
        WHERE 1=1
    """
    params: dict[str, Any] = {"org_id": user.org_id}
    if therapy_area:
        sql += " AND (a.therapeutic_area ILIKE :ta OR tm.therapy_area ILIKE :ta)"
        params["ta"] = f"%{therapy_area}%"
    if brand:
        sql += " AND a.brand_name ILIKE :br"
        params["br"] = f"%{brand}%"
    if indication:
        sql += " AND i.label ILIKE :ind"
        params["ind"] = f"%{indication}%"
    if country:
        sql += " AND (c.code = :cc OR c.name ILIKE :cn)"
        params["cc"] = country.upper()
        params["cn"] = f"%{country}%"
    sql += " ORDER BY tm.is_manager DESC, a.brand_name, c.name, tm.full_name"
    rows = db.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/my-launch-team/filters")
def my_team_filters(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Distinct values for the dropdowns on the team page."""
    therapy_areas = [r[0] for r in db.execute(text(
        "SELECT DISTINCT a.therapeutic_area FROM assets a "
        "JOIN launches l ON l.asset_id = a.id WHERE l.org_id = :o AND a.therapeutic_area IS NOT NULL "
        "ORDER BY 1"
    ), {"o": user.org_id}).all()]
    brands = [r[0] for r in db.execute(text(
        "SELECT DISTINCT a.brand_name FROM assets a "
        "JOIN launches l ON l.asset_id = a.id WHERE l.org_id = :o ORDER BY 1"
    ), {"o": user.org_id}).all()]
    indications = [r[0] for r in db.execute(text(
        "SELECT DISTINCT i.label FROM indications i "
        "JOIN launches l ON l.indication_id = i.id WHERE l.org_id = :o AND i.label IS NOT NULL ORDER BY 1"
    ), {"o": user.org_id}).all()]
    countries = [{"code": r[0], "name": r[1]} for r in db.execute(text(
        "SELECT DISTINCT c.code, c.name FROM countries c "
        "JOIN launches l ON l.country_id = c.id WHERE l.org_id = :o ORDER BY c.name"
    ), {"o": user.org_id}).all()]
    return {
        "therapy_areas": therapy_areas, "brands": brands,
        "indications": indications, "countries": countries,
    }


# ============================================================================
# Meetings
# ============================================================================

@router.get("/launches/{launch_id}/meetings")
def get_meetings(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    rows = db.execute(text("SELECT * FROM launch_meetings WHERE launch_id = :id ORDER BY meeting_key"),
                      {"id": launch_id}).mappings().all()
    return [dict(r) for r in rows]


# ============================================================================
# Activity tree
# ============================================================================

class ActivityUpdateIn(BaseModel):
    status: Optional[str] = None
    importance: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    organisation: Optional[str] = None
    country_code: Optional[str] = None
    manual_complete: Optional[bool] = None
    owner_user_id: Optional[uuid.UUID] = None


@router.get("/launches/{launch_id}/activities")
def get_activities(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    rows = db.execute(text("""
        SELECT id, launch_id, parent_id, group_key, group_name, ordinal, level,
               name, status, country_code, importance, manual_complete,
               start_date, end_date, organisation, owner_user_id, assigned_count
        FROM launch_activities WHERE launch_id = :id
        ORDER BY string_to_array(ordinal, '.')::int[]
    """), {"id": launch_id}).mappings().all()
    return [dict(r) for r in rows]


@router.patch(
    "/activities/{activity_id}",
    dependencies=[Depends(require_role("global_admin", "global_brand_lead", "country_launch_lead", "medical", "market_access"))],
)
def update_activity(activity_id: uuid.UUID, body: ActivityUpdateIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Check activity belongs to a launch in this org
    own = db.execute(text("""
        SELECT a.id FROM launch_activities a
        JOIN launches l ON l.id = a.launch_id
        WHERE a.id = :aid AND l.org_id = :org
    """), {"aid": activity_id, "org": user.org_id}).first()
    if not own:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Activity not found")
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return {"ok": True}
    set_clauses = ", ".join(f"{k} = :{k}" for k in updates) + ", updated_at = now()"
    updates["aid"] = activity_id
    db.execute(text(f"UPDATE launch_activities SET {set_clauses} WHERE id = :aid"), updates)
    db.commit()
    return {"ok": True}


@router.get("/launches/{launch_id}/activity-summary")
def activity_summary(launch_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Roll up activity tree by group + status for the launch dashboard header."""
    if not db.query(Launch).filter(Launch.id == launch_id, Launch.org_id == user.org_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Launch not found")
    rows = db.execute(text("""
        SELECT group_key, group_name, status, COUNT(*) AS n
        FROM launch_activities WHERE launch_id = :id
        GROUP BY group_key, group_name, status
        ORDER BY group_key
    """), {"id": launch_id}).mappings().all()
    by_group: dict[str, dict[str, Any]] = {}
    for r in rows:
        g = by_group.setdefault(r["group_key"], {"group_key": r["group_key"], "group_name": r["group_name"], "total": 0, "by_status": {}})
        g["by_status"][r["status"]] = r["n"]
        g["total"] += r["n"]
    return list(by_group.values())
