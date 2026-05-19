from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ---------- Identity & RBAC ----------

class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    default_role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer")
    sso_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False, default="org")
    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_role_org_name"),)


class RoleAssignment(Base):
    __tablename__ = "role_assignments"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)  # portfolio|asset|launch|workstream|org
    scope_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    before: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    after: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------- Portfolio hierarchy ----------

class Portfolio(Base):
    __tablename__ = "portfolios"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    fiscal_year_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    portfolio_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("portfolios.id"), nullable=True)
    brand_name: Mapped[str] = mapped_column(String(200), nullable=False)
    inn: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    molecule_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    moa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    therapeutic_area: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    line_of_therapy: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    route: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    dosing: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    companion_dx: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cold_chain: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class Indication(Base):
    __tablename__ = "indications"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    population_segment: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class Country(Base):
    __tablename__ = "countries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    hta_body: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class Launch(Base):
    __tablename__ = "launches"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    launch_code: Mapped[str] = mapped_column(String(32), nullable=False)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    indication_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("indications.id"), nullable=True)
    country_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("countries.id"), nullable=False, index=True)
    launch_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    launch_phase: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    target_launch_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    reg_approval_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    hta_decision: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    overall_rag: Mapped[str] = mapped_column(String(16), nullable=False, default="Green")
    country_launch_lead_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    global_brand_lead_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Active")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    __table_args__ = (UniqueConstraint("org_id", "launch_code", name="uq_launch_org_code"),)

    asset: Mapped["Asset"] = relationship(lazy="joined", foreign_keys=[asset_id])
    country: Mapped["Country"] = relationship(lazy="joined", foreign_keys=[country_id])


# ---------- PRD & versioning ----------

class PRD(Base):
    __tablename__ = "prds"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    launch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("launches.id"), unique=True, nullable=False)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class PRDVersion(Base):
    __tablename__ = "prd_versions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    prd_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prds.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_baseline: Mapped[bool] = mapped_column(Boolean, default=False)


class PRDFieldHistory(Base):
    __tablename__ = "prd_field_history"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    prd_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("prds.id"), nullable=False, index=True)
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# ---------- Workstreams & milestones ----------

class Workstream(Base):
    __tablename__ = "workstreams"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class MilestoneTemplate(Base):
    __tablename__ = "milestone_templates"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    launch_type: Mapped[str] = mapped_column(String(64), nullable=False)
    workstream_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("workstreams.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    default_offset_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_gate: Mapped[bool] = mapped_column(Boolean, default=False)


class Milestone(Base):
    __tablename__ = "milestones"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    launch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("launches.id"), nullable=False, index=True)
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("milestone_templates.id"), nullable=True)
    workstream_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("workstreams.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Not Started")
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_gate: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    milestone_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("milestones.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Not Started")
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# ---------- Dependency engine ----------

class Dependency(Base):
    __tablename__ = "dependencies"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    link_type: Mapped[str] = mapped_column(String(32), nullable=False)  # blocks|informs|references_price|shares_supply|shares_evidence
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ---------- Forecasts ----------

class Forecast(Base):
    __tablename__ = "forecasts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    launch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("launches.id"), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    source: Mapped[str] = mapped_column(String(16), nullable=False, default="bottom_up")
    y1_patients: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    y2_patients: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    y3_patients: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    y1_net_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y2_net_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y3_net_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y1_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y2_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    y3_share: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)


# ---------- Risks ----------

class Risk(Base):
    __tablename__ = "risks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False, default="launch")
    scope_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    likelihood: Mapped[str] = mapped_column(String(8), nullable=False, default="M")
    impact: Mapped[str] = mapped_column(String(8), nullable=False, default="M")
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    mitigation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    target_resolution_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="Open")


class RiskLaunchLink(Base):
    __tablename__ = "risk_launch_links"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    risk_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("risks.id"), nullable=False, index=True)
    launch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("launches.id"), nullable=False, index=True)


# ---------- KPIs & RACI ----------

class KPI(Base):
    __tablename__ = "kpis"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    launch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("launches.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    l_minus_30: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    l_plus_30: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    l_plus_60: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    l_plus_90: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    l_plus_180: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    l_plus_365: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rag: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    owner_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)


class RaciEntry(Base):
    __tablename__ = "raci_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    launch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("launches.id"), nullable=False, index=True)
    workstream_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workstreams.id"), nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("roles.id"), nullable=False)
    raci: Mapped[str] = mapped_column(String(2), nullable=False)


# ---------- Integrations & Market Intelligence ----------

class IntegrationConnector(Base):
    __tablename__ = "integration_connectors"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    credentials_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_sync_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)


class ExternalRecord(Base):
    __tablename__ = "external_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    connector_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("integration_connectors.id"), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class MarketIntelSource(Base):
    __tablename__ = "market_intel_sources"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), nullable=False)
    free: Mapped[bool] = mapped_column(Boolean, default=True)
    rate_limit_per_min: Mapped[int] = mapped_column(Integer, default=60)


class MarketIntelRecord(Base):
    __tablename__ = "market_intel_records"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("market_intel_sources.id"), nullable=False, index=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    asset_match: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    therapeutic_area: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    record_type: Mapped[str] = mapped_column(String(32), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint("source_id", "external_id", name="uq_intel_source_extid"),)


class IntelSubscription(Base):
    __tablename__ = "intel_subscriptions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    scope_type: Mapped[str] = mapped_column(String(32), nullable=False)
    scope_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    source_ids: Mapped[list] = mapped_column(JSON, default=list)
