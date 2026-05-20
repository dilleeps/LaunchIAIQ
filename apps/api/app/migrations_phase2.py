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
    # ----- Launch setup (template, assumptions, meetings, team, activity tree) -----
    """
    CREATE TABLE IF NOT EXISTS launch_setup (
        launch_id uuid PRIMARY KEY,
        template_key text NULL,
        franchise text NULL,
        brand text NULL,
        indication_label text NULL,
        region text NULL,
        business_partner text NULL,
        local_launch_leader_user_id uuid NULL,
        commercial_launch_date date NULL,
        regulatory_submission date NULL,
        regulatory_approval date NULL,
        pricing_submission date NULL,
        pricing_approval date NULL,
        reimbursement_submission date NULL,
        reimbursement_approval date NULL,
        trade_stock_available date NULL,
        phase3_results date NULL,
        amnog_dossier_submission date NULL,
        gba_decision date NULL,
        nhi_price_listing date NULL,
        mrp_value numeric NULL,
        mrp_currency varchar(8) NULL,
        mrp_year int NULL,
        cumulative_mrp numeric NULL,
        not_applicable jsonb DEFAULT '[]'::jsonb,
        pending_confirmation jsonb DEFAULT '[]'::jsonb,
        created_at timestamp DEFAULT now(),
        updated_at timestamp DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS launch_meetings (
        id uuid PRIMARY KEY,
        launch_id uuid NOT NULL,
        meeting_key text NOT NULL,
        name text NOT NULL,
        cadence text NOT NULL,
        day_of_month int NULL,
        offset_months_before_launch int NULL,
        scheduled_date date NULL,
        recurring boolean DEFAULT false,
        notes text NULL,
        created_at timestamp DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_launch_meetings_launch ON launch_meetings(launch_id)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_launch_meetings_key ON launch_meetings(launch_id, meeting_key)",
    """
    CREATE TABLE IF NOT EXISTS launch_team_members (
        id uuid PRIMARY KEY,
        launch_id uuid NOT NULL,
        user_id uuid NULL,
        full_name text NULL,
        email text NULL,
        role_label text NOT NULL,
        country_code varchar(3) NULL,
        is_manager boolean DEFAULT false,
        therapy_area text NULL,
        added_at timestamp DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_team_members_launch ON launch_team_members(launch_id)",
    "CREATE INDEX IF NOT EXISTS ix_team_members_user ON launch_team_members(user_id)",
    """
    CREATE TABLE IF NOT EXISTS launch_activities (
        id uuid PRIMARY KEY,
        launch_id uuid NOT NULL,
        parent_id uuid NULL,
        group_key text NOT NULL,
        group_name text NOT NULL,
        ordinal text NOT NULL,
        level int NOT NULL DEFAULT 1,
        name text NOT NULL,
        status text DEFAULT 'Not Started',
        country_code varchar(16) NULL,
        importance text DEFAULT 'Standard',
        manual_complete boolean DEFAULT false,
        start_date date NULL,
        end_date date NULL,
        organisation text NULL,
        owner_user_id uuid NULL,
        assigned_count int DEFAULT 0,
        created_at timestamp DEFAULT now(),
        updated_at timestamp DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_launch_activities_launch ON launch_activities(launch_id)",
    "CREATE INDEX IF NOT EXISTS ix_launch_activities_parent ON launch_activities(parent_id)",
    "CREATE INDEX IF NOT EXISTS ix_launch_activities_group ON launch_activities(launch_id, group_key)",
    "CREATE UNIQUE INDEX IF NOT EXISTS uq_launch_activities_ordinal ON launch_activities(launch_id, ordinal)",
]


def apply_phase2_migrations(engine: Engine) -> None:
    with engine.begin() as conn:
        for stmt in _STATEMENTS:
            conn.execute(text(stmt))
