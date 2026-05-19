"""Phase 2-4 additive schema. Idempotent CREATE TABLE IF NOT EXISTS run on app startup.

Kept intentionally separate from Alembic so the original migration stays untouched.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine


_STATEMENTS: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS scenarios (
        id uuid PRIMARY KEY,
        org_id uuid NOT NULL,
        base_launch_id uuid NOT NULL,
        name text NOT NULL,
        parent_scenario_id uuid NULL,
        created_by uuid NULL,
        created_at timestamp DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_scenarios_org ON scenarios(org_id)",
    "CREATE INDEX IF NOT EXISTS ix_scenarios_base ON scenarios(base_launch_id)",
    """
    CREATE TABLE IF NOT EXISTS scenario_overrides (
        id uuid PRIMARY KEY,
        scenario_id uuid NOT NULL,
        entity text NOT NULL,
        entity_id uuid NOT NULL,
        field text NOT NULL,
        value jsonb
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_scenario_overrides_scenario ON scenario_overrides(scenario_id)",
    """
    CREATE TABLE IF NOT EXISTS stage_gates (
        id uuid PRIMARY KEY,
        launch_id uuid NOT NULL,
        name text NOT NULL,
        required_role_names jsonb DEFAULT '[]'::jsonb,
        status text DEFAULT 'pending',
        decided_at timestamp NULL,
        decided_by uuid NULL,
        decision_note text NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_stage_gates_launch ON stage_gates(launch_id)",
    """
    CREATE TABLE IF NOT EXISTS approvals (
        id uuid PRIMARY KEY,
        entity text NOT NULL,
        entity_id uuid NOT NULL,
        requested_by uuid NULL,
        approver_role_name text NOT NULL,
        approver_user_id uuid NULL,
        status text DEFAULT 'pending',
        comment text NULL,
        requested_at timestamp DEFAULT now(),
        decided_at timestamp NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_approvals_status ON approvals(status)",
    """
    CREATE TABLE IF NOT EXISTS fx_assumptions (
        id uuid PRIMARY KEY,
        org_id uuid NOT NULL,
        from_ccy varchar(3) NOT NULL,
        to_ccy varchar(3) NOT NULL,
        year int NOT NULL,
        rate float NOT NULL,
        version int DEFAULT 1,
        source text DEFAULT 'manual'
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_fx_org ON fx_assumptions(org_id)",
    """
    CREATE TABLE IF NOT EXISTS forecast_drivers (
        id uuid PRIMARY KEY,
        forecast_id uuid NOT NULL,
        driver text NOT NULL,
        low float NOT NULL,
        base float NOT NULL,
        high float NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_forecast_drivers_forecast ON forecast_drivers(forecast_id)",
    """
    CREATE TABLE IF NOT EXISTS actuals (
        id uuid PRIMARY KEY,
        launch_id uuid NOT NULL,
        period varchar(7) NOT NULL,
        net_sales float NULL,
        patients int NULL,
        source text DEFAULT 'manual'
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_actuals_launch ON actuals(launch_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_actuals_launch_period ON actuals(launch_id, period)",
    """
    CREATE TABLE IF NOT EXISTS variance_alerts (
        id uuid PRIMARY KEY,
        launch_id uuid NOT NULL,
        period varchar(7) NOT NULL,
        metric text NOT NULL,
        forecast_value float NOT NULL,
        actual_value float NOT NULL,
        variance_pct float NOT NULL,
        threshold_pct float NOT NULL,
        status text DEFAULT 'open'
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_variance_launch ON variance_alerts(launch_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_variance_launch_period_metric ON variance_alerts(launch_id, period, metric)",
    """
    CREATE TABLE IF NOT EXISTS reference_pricing_links (
        id uuid PRIMARY KEY,
        source_launch_id uuid NOT NULL,
        target_launch_id uuid NOT NULL,
        weight float DEFAULT 1.0,
        basket_role text NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_refprice_source ON reference_pricing_links(source_launch_id)",
    "CREATE INDEX IF NOT EXISTS ix_refprice_target ON reference_pricing_links(target_launch_id)",
    """
    CREATE TABLE IF NOT EXISTS prd_comments (
        id uuid PRIMARY KEY,
        prd_id uuid NOT NULL,
        section text NOT NULL,
        field text NULL,
        user_id uuid NULL,
        body text NOT NULL,
        mentions jsonb DEFAULT '[]'::jsonb,
        parent_id uuid NULL,
        resolved_at timestamp NULL,
        created_at timestamp DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_prd_comments_prd ON prd_comments(prd_id)",
    """
    CREATE TABLE IF NOT EXISTS field_permissions (
        id uuid PRIMARY KEY,
        role_name text NOT NULL,
        entity text NOT NULL,
        field text NOT NULL,
        access text NOT NULL
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_field_permissions ON field_permissions(role_name, entity, field)",
]


def apply_phase2_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
        for stmt in _STATEMENTS:
            conn.execute(text(stmt))
