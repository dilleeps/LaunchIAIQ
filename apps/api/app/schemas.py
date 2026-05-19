from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------- Auth ----------

class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterOrgIn(BaseModel):
    org_name: str
    org_slug: str
    admin_email: EmailStr
    admin_password: str
    admin_full_name: str


class UserOut(ORMBase):
    id: uuid.UUID
    org_id: uuid.UUID
    email: EmailStr
    full_name: str
    default_role: str


# ---------- Lookups ----------

class CountryOut(ORMBase):
    id: uuid.UUID
    code: str
    name: str
    region: Optional[str] = None
    currency_code: Optional[str] = None
    hta_body: Optional[str] = None


# ---------- Assets / Launches ----------

class AssetOut(ORMBase):
    id: uuid.UUID
    brand_name: str
    inn: Optional[str] = None
    therapeutic_area: Optional[str] = None
    molecule_type: Optional[str] = None
    moa: Optional[str] = None


class AssetIn(BaseModel):
    brand_name: str
    inn: Optional[str] = None
    therapeutic_area: Optional[str] = None
    molecule_type: Optional[str] = None
    moa: Optional[str] = None


class LaunchOut(ORMBase):
    id: uuid.UUID
    launch_code: str
    asset: AssetOut
    country: CountryOut
    launch_type: Optional[str] = None
    launch_phase: Optional[str] = None
    target_launch_date: Optional[date] = None
    reg_approval_date: Optional[date] = None
    hta_decision: Optional[str] = None
    overall_rag: str
    status: str
    notes: Optional[str] = None


class LaunchIn(BaseModel):
    launch_code: str
    asset_id: uuid.UUID
    country_id: uuid.UUID
    indication_id: Optional[uuid.UUID] = None
    launch_type: Optional[str] = None
    launch_phase: Optional[str] = None
    target_launch_date: Optional[date] = None
    reg_approval_date: Optional[date] = None
    hta_decision: Optional[str] = None
    overall_rag: Optional[str] = "Green"
    notes: Optional[str] = None


# ---------- Milestones ----------

class MilestoneOut(ORMBase):
    id: uuid.UUID
    launch_id: uuid.UUID
    name: str
    target_date: Optional[date] = None
    actual_date: Optional[date] = None
    status: str
    weight: float
    is_gate: bool
    notes: Optional[str] = None


class MilestoneUpdateIn(BaseModel):
    status: Optional[str] = None
    actual_date: Optional[date] = None
    target_date: Optional[date] = None
    notes: Optional[str] = None


# ---------- Risks ----------

class RiskOut(ORMBase):
    id: uuid.UUID
    scope_type: str
    scope_id: Optional[uuid.UUID] = None
    category: Optional[str] = None
    description: str
    likelihood: str
    impact: str
    score: int
    mitigation: Optional[str] = None
    target_resolution_date: Optional[date] = None
    status: str


class RiskIn(BaseModel):
    scope_type: str = "launch"
    scope_id: Optional[uuid.UUID] = None
    category: Optional[str] = None
    description: str
    likelihood: str = "M"
    impact: str = "M"
    mitigation: Optional[str] = None
    target_resolution_date: Optional[date] = None
    status: str = "Open"
    launch_ids: list[uuid.UUID] = []


# ---------- Forecasts ----------

class ForecastOut(ORMBase):
    id: uuid.UUID
    launch_id: uuid.UUID
    currency: str
    source: str
    y1_patients: Optional[int] = None
    y2_patients: Optional[int] = None
    y3_patients: Optional[int] = None
    y1_net_price: Optional[float] = None
    y2_net_price: Optional[float] = None
    y3_net_price: Optional[float] = None
    y1_share: Optional[float] = None
    y2_share: Optional[float] = None
    y3_share: Optional[float] = None
    version: int
    is_current: bool


# ---------- PRD ----------

class PRDOut(ORMBase):
    id: uuid.UUID
    launch_id: uuid.UUID
    current_version: int
    payload: dict[str, Any]


class PRDUpdateIn(BaseModel):
    payload: dict[str, Any]
    change_reason: Optional[str] = None


# ---------- Dependencies ----------

class DependencyOut(ORMBase):
    id: uuid.UUID
    source_type: str
    source_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    link_type: str
    notes: Optional[str] = None


class DependencyIn(BaseModel):
    source_type: str
    source_id: uuid.UUID
    target_type: str
    target_id: uuid.UUID
    link_type: str
    notes: Optional[str] = None


# ---------- Portfolio overview ----------

class OverviewStat(BaseModel):
    on_track_count: int
    total_launches: int
    peak_revenue: float
    peak_revenue_currency: str
    high_risks_open: int
    next_milestone: Optional[dict[str, Any]] = None


class MatrixCell(BaseModel):
    launch_id: uuid.UUID
    launch_code: str
    rag: str
    milestones_complete_pct: float


class MatrixRow(BaseModel):
    asset_id: uuid.UUID
    brand_name: str
    cells: dict[str, MatrixCell]  # country_code → cell


# ---------- Market intel ----------

class MarketIntelOut(ORMBase):
    id: uuid.UUID
    source_id: uuid.UUID
    country_code: Optional[str] = None
    asset_match: Optional[str] = None
    therapeutic_area: Optional[str] = None
    record_type: str
    title: str
    url: Optional[str] = None
    occurred_at: Optional[datetime] = None


# ---------- KPIs / RACI ----------

class KPIOut(ORMBase):
    id: uuid.UUID
    launch_id: uuid.UUID
    category: str
    name: str
    unit: Optional[str] = None
    target: Optional[float] = None
    l_minus_30: Optional[float] = None
    l_plus_30: Optional[float] = None
    l_plus_60: Optional[float] = None
    l_plus_90: Optional[float] = None
    l_plus_180: Optional[float] = None
    l_plus_365: Optional[float] = None
    rag: Optional[str] = None


class RaciOut(ORMBase):
    id: uuid.UUID
    launch_id: uuid.UUID
    workstream_id: uuid.UUID
    role_id: uuid.UUID
    raci: str
