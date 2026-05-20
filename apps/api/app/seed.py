"""Seed demo data: an org, admin, 2 assets, 5 launches (L-001..L-005), milestone templates,
17 milestones per launch, a sample dependency, risks, KPIs, forecasts, and an openFDA connector
pre-configured for the demo assets.

Run: `python -m app.seed`
"""
from __future__ import annotations

import json
import uuid
from datetime import date

from sqlalchemy import select, text

from .database import SessionLocal, engine, Base
from .integrations.openfda import ensure_source
from .migrations_phase2 import apply_phase2_migrations
from .models import (
    Asset,
    Country,
    Dependency,
    Forecast,
    IntegrationConnector,
    KPI,
    Launch,
    Milestone,
    MilestoneTemplate,
    Organization,
    PRD,
    PRDVersion,
    Risk,
    RiskLaunchLink,
    Role,
    User,
    Workstream,
)
from .security import hash_password


COUNTRIES = [
    ("USA", "United States", "North America", "USD", "FDA"),
    ("DEU", "Germany", "Europe", "EUR", "G-BA/IQWiG"),
    ("JPN", "Japan", "Japan", "JPY", "PMDA/Chuikyo"),
    ("GBR", "United Kingdom", "Europe", "GBP", "NICE"),
    ("FRA", "France", "Europe", "EUR", "HAS"),
    ("CAN", "Canada", "North America", "CAD", "CADTH"),
    ("AUS", "Australia", "APAC", "AUD", "PBAC"),
]

WORKSTREAMS = [
    "Regulatory",
    "Market Access",
    "Medical",
    "Commercial",
    "Supply Chain",
    "Compliance",
]

STANDARD_MILESTONES = [
    ("Regulatory submission", "Regulatory", 1.0, False),
    ("Regulatory approval received", "Regulatory", 2.0, True),
    ("Local label finalized", "Regulatory", 1.0, False),
    ("Pricing dossier submitted", "Market Access", 1.0, False),
    ("HTA / reimbursement decision", "Market Access", 2.0, True),
    ("National formulary listing", "Market Access", 1.0, False),
    ("Tender submission (if applicable)", "Market Access", 0.5, False),
    ("Launch stock delivered in-country", "Supply Chain", 1.0, True),
    ("Field force hired & trained", "Commercial", 1.0, False),
    ("Medical / MSL team trained", "Medical", 1.0, False),
    ("Promotional materials approved (MLR/PRC)", "Compliance", 1.0, False),
    ("KOL advisory board completed", "Medical", 0.5, False),
    ("Patient support program live", "Commercial", 0.5, False),
    ("First commercial sale (FCS)", "Commercial", 2.0, True),
    ("Launch event / symposium", "Commercial", 0.5, False),
    ("30-day post-launch review", "Commercial", 0.5, False),
    ("90-day post-launch review", "Commercial", 0.5, False),
]


def _get_or_create(db, model, defaults=None, **kwargs):
    obj = db.query(model).filter_by(**kwargs).first()
    if obj:
        return obj, False
    params = {**kwargs, **(defaults or {})}
    obj = model(**params)
    db.add(obj)
    db.flush()
    return obj, True


def run() -> None:
    Base.metadata.create_all(bind=engine)
    apply_phase2_migrations(engine)
    db = SessionLocal()
    try:
        # Advisory lock so only one container in a multi-replica deploy seeds at a time.
        # Other replicas block here briefly, then find data already present and become no-ops.
        db.execute(text("SELECT pg_advisory_lock(727292727292)"))
        # Org + admin
        org, _ = _get_or_create(db, Organization, name="Demo Pharma Co.", slug="demo")
        admin = db.query(User).filter(User.email == "admin@demo.example").first()
        if not admin:
            admin = User(
                org_id=org.id,
                email="admin@demo.example",
                password_hash=hash_password("demo123"),
                full_name="Demo Admin",
                default_role="global_admin",
            )
            db.add(admin)
            db.flush()
        # Demo viewer
        if not db.query(User).filter(User.email == "viewer@demo.example").first():
            db.add(
                User(
                    org_id=org.id,
                    email="viewer@demo.example",
                    password_hash=hash_password("demo123"),
                    full_name="Demo Viewer",
                    default_role="viewer",
                )
            )

        # Roles (built-ins)
        for rname in ["global_admin", "global_brand_lead", "country_launch_lead", "medical", "market_access", "finance", "viewer"]:
            _get_or_create(db, Role, defaults={"scope_type": "org"}, org_id=org.id, name=rname)

        # Countries (global lookup)
        for code, name, region, ccy, hta in COUNTRIES:
            _get_or_create(db, Country, defaults={"name": name, "region": region, "currency_code": ccy, "hta_body": hta}, code=code)

        # Workstreams
        ws_by_name = {}
        for w in WORKSTREAMS:
            obj, _ = _get_or_create(db, Workstream, name=w)
            ws_by_name[w] = obj

        # Assets
        asset_a, _ = _get_or_create(
            db,
            Asset,
            defaults={
                "inn": "demo-mab-a",
                "molecule_type": "Biologic",
                "therapeutic_area": "Oncology",
                "moa": "Anti-PD-1 monoclonal antibody",
                "line_of_therapy": "1L",
                "route": "IV",
                "dosing": "240 mg Q3W",
            },
            org_id=org.id,
            brand_name="Brand A",
        )
        asset_b, _ = _get_or_create(
            db,
            Asset,
            defaults={
                "inn": "demo-imm-b",
                "molecule_type": "Biologic",
                "therapeutic_area": "Immunology",
                "moa": "IL-23 inhibitor",
                "line_of_therapy": "2L",
                "route": "SC",
                "dosing": "100 mg Q8W",
            },
            org_id=org.id,
            brand_name="Brand B",
        )

        # Milestone templates (NCE)
        for name, ws_name, weight, is_gate in STANDARD_MILESTONES:
            _get_or_create(
                db,
                MilestoneTemplate,
                defaults={"workstream_id": ws_by_name[ws_name].id, "weight": weight, "is_gate": is_gate, "default_offset_days": 0},
                org_id=org.id,
                launch_type="NCE",
                name=name,
            )

        # Launches
        countries_by_code = {c.code: c for c in db.query(Country).all()}
        seeded = [
            ("L-001", asset_a, "USA", "NCE", "Pre-launch", date(2026, 9, 1), date(2026, 6, 15), "Pending", "Amber"),
            ("L-002", asset_a, "DEU", "NCE", "Pre-launch", date(2026, 11, 1), date(2026, 8, 30), "Pending", "Green"),
            ("L-003", asset_a, "JPN", "NCE", "Pre-launch", date(2027, 1, 15), date(2026, 12, 1), "Pending", "Green"),
            ("L-004", asset_b, "GBR", "New Indication", "Launch", date(2026, 4, 1), date(2026, 2, 10), "Positive", "Green"),
            ("L-005", asset_b, "FRA", "New Indication", "Pre-launch", date(2026, 7, 1), date(2026, 5, 20), "Pending", "Amber"),
        ]
        launches_by_code: dict[str, Launch] = {}
        for code, asset, ccy_code, ltype, lphase, tgt, reg, hta, rag in seeded:
            launch, created = _get_or_create(
                db,
                Launch,
                defaults={
                    "asset_id": asset.id,
                    "country_id": countries_by_code[ccy_code].id,
                    "launch_type": ltype,
                    "launch_phase": lphase,
                    "target_launch_date": tgt,
                    "reg_approval_date": reg,
                    "hta_decision": hta,
                    "overall_rag": rag,
                    "country_launch_lead_user_id": admin.id,
                    "global_brand_lead_user_id": admin.id,
                },
                org_id=org.id,
                launch_code=code,
            )
            launches_by_code[code] = launch

            if created:
                # Milestones from template
                offset = 0
                for name, ws_name, weight, is_gate in STANDARD_MILESTONES:
                    db.add(
                        Milestone(
                            launch_id=launch.id,
                            workstream_id=ws_by_name[ws_name].id,
                            name=name,
                            target_date=date.fromordinal(tgt.toordinal() + offset),
                            status="Not Started",
                            weight=weight,
                            is_gate=is_gate,
                        )
                    )
                    offset += 14
                # PRD
                prd = PRD(launch_id=launch.id, current_version=1)
                db.add(prd)
                db.flush()
                db.add(
                    PRDVersion(
                        prd_id=prd.id,
                        version=1,
                        is_baseline=True,
                        payload={
                            "identification": {
                                "launch_id": code,
                                "asset": asset.brand_name,
                                "country": countries_by_code[ccy_code].name,
                                "launch_type": ltype,
                                "launch_phase": lphase,
                            },
                            "executive_summary": {
                                "launch_vision": "Achieve premium reimbursement and rapid HCP uptake in the launch year.",
                                "priority_1": "Reimbursement at premium price",
                                "priority_2": "HCP aided awareness 70% by L+90",
                                "priority_3": "Hit Y1 patient target",
                            },
                            "asset_overview": {
                                "inn": asset.inn,
                                "molecule_type": asset.molecule_type,
                                "moa": asset.moa,
                                "line_of_therapy": asset.line_of_therapy,
                                "route": asset.route,
                                "dosing": asset.dosing,
                            },
                        },
                    )
                )
                # KPIs (subset of workbook)
                for cat, name, unit in [
                    ("Leading", "HCP aided awareness", "%"),
                    ("Leading", "Formulary / hospital listings achieved", "#"),
                    ("Leading", "MSL interactions with target KOLs", "#"),
                    ("Lagging", "New patient starts", "#"),
                    ("Lagging", "Net sales vs forecast", "%"),
                    ("Lagging", "Market share — volume", "%"),
                ]:
                    db.add(KPI(launch_id=launch.id, category=cat, name=name, unit=unit))

        # Forecasts (matches workbook)
        fc_data = [
            ("L-001", "USD", 1200, 3500, 6000, 400000.0, 405000.0, 410000.0),
            ("L-002", "EUR", 800, 2200, 3800, 118000.0, 115000.0, 112000.0),
            ("L-003", "JPY", 500, 1600, 2900, 13000000.0, 12500000.0, 12000000.0),
            ("L-004", "GBP", 350, 900, 1500, 80000.0, 78000.0, 76000.0),
            ("L-005", "EUR", 280, 750, 1300, 78000.0, 76000.0, 74000.0),
        ]
        for code, ccy, y1p, y2p, y3p, y1pr, y2pr, y3pr in fc_data:
            launch = launches_by_code[code]
            if not db.query(Forecast).filter(Forecast.launch_id == launch.id).first():
                db.add(
                    Forecast(
                        launch_id=launch.id,
                        currency=ccy,
                        source="bottom_up",
                        y1_patients=y1p,
                        y2_patients=y2p,
                        y3_patients=y3p,
                        y1_net_price=y1pr,
                        y2_net_price=y2pr,
                        y3_net_price=y3pr,
                    )
                )

        # Sample risks (one shared across multiple launches)
        if not db.query(Risk).filter(Risk.description.like("%API supply%")).first():
            r1 = Risk(
                org_id=org.id,
                scope_type="portfolio",
                category="Supply",
                description="API supply constraint at single-source CMO could delay launch stock in EU and US",
                likelihood="M",
                impact="H",
                score=6,
                mitigation="Qualify second CMO by L-90; pre-build 6 months safety stock.",
                target_resolution_date=date(2026, 7, 1),
                status="Open",
            )
            db.add(r1)
            db.flush()
            for code in ["L-001", "L-002"]:
                db.add(RiskLaunchLink(risk_id=r1.id, launch_id=launches_by_code[code].id))

            r2 = Risk(
                org_id=org.id,
                scope_type="launch",
                scope_id=launches_by_code["L-001"].id,
                category="Market Access",
                description="ICER threshold may force aggressive list-price discount in US",
                likelihood="H",
                impact="H",
                score=9,
                mitigation="Develop outcomes-based contract proposals with top 5 PBMs.",
                target_resolution_date=date(2026, 5, 1),
                status="Open",
            )
            db.add(r2)
            db.flush()
            db.add(RiskLaunchLink(risk_id=r2.id, launch_id=launches_by_code["L-001"].id))

        # Sample dependency: Germany G-BA decision blocks 4 IRP reference markets
        deu_launch = launches_by_code["L-002"]
        if not db.query(Dependency).filter(Dependency.source_id == deu_launch.id).first():
            for code in ["L-004", "L-005"]:
                db.add(
                    Dependency(
                        org_id=org.id,
                        source_type="launch",
                        source_id=deu_launch.id,
                        target_type="launch",
                        target_id=launches_by_code[code].id,
                        link_type="references_price",
                        notes="Germany G-BA decision sets IRP basket anchor",
                    )
                )

        # openFDA market intel source + connector
        ensure_source(db)
        if not db.query(IntegrationConnector).filter(IntegrationConnector.org_id == org.id, IntegrationConnector.kind == "openfda").first():
            db.add(
                IntegrationConnector(
                    org_id=org.id,
                    kind="openfda",
                    config={"asset_query": None, "limit": 25},
                    enabled=True,
                )
            )

        db.commit()

        # ---------- Phase 2-4 demo data (idempotent) ----------
        l001 = launches_by_code["L-001"]
        l002 = launches_by_code["L-002"]
        l004 = launches_by_code["L-004"]
        l005 = launches_by_code["L-005"]

        # Stage gates on L-001
        existing_gates = {
            r["name"]
            for r in db.execute(
                text("SELECT name FROM stage_gates WHERE launch_id = :lid"),
                {"lid": str(l001.id)},
            ).mappings().all()
        }
        gates_seed = [
            ("Reg Approval Gate", ["global_admin"]),
            ("Launch Go/No-Go", ["global_brand_lead"]),
        ]
        for gname, roles in gates_seed:
            if gname in existing_gates:
                continue
            db.execute(
                text(
                    "INSERT INTO stage_gates (id, launch_id, name, required_role_names, status) "
                    "VALUES (:id, :lid, :name, CAST(:roles AS jsonb), 'pending')"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "lid": str(l001.id),
                    "name": gname,
                    "roles": json.dumps(roles),
                },
            )

        # Reference pricing link DEU -> FRA
        existing_rpl = db.execute(
            text(
                "SELECT 1 FROM reference_pricing_links WHERE source_launch_id = :s AND target_launch_id = :t"
            ),
            {"s": str(l002.id), "t": str(l005.id)},
        ).first()
        if not existing_rpl:
            db.execute(
                text(
                    "INSERT INTO reference_pricing_links (id, source_launch_id, target_launch_id, weight, basket_role) "
                    "VALUES (:id, :s, :t, 1.0, 'anchor')"
                ),
                {"id": str(uuid.uuid4()), "s": str(l002.id), "t": str(l005.id)},
            )

        # FX EUR->USD 2026
        existing_fx = db.execute(
            text(
                "SELECT 1 FROM fx_assumptions WHERE org_id = :org AND from_ccy = 'EUR' AND to_ccy = 'USD' AND year = 2026"
            ),
            {"org": str(org.id)},
        ).first()
        if not existing_fx:
            db.execute(
                text(
                    "INSERT INTO fx_assumptions (id, org_id, from_ccy, to_ccy, year, rate, version, source) "
                    "VALUES (:id, :org, 'EUR', 'USD', 2026, 1.08, 1, 'manual')"
                ),
                {"id": str(uuid.uuid4()), "org": str(org.id)},
            )

        # Forecast drivers on L-001's forecast
        l001_fc = db.query(Forecast).filter(Forecast.launch_id == l001.id).first()
        if l001_fc:
            existing_drivers = {
                r["driver"]
                for r in db.execute(
                    text("SELECT driver FROM forecast_drivers WHERE forecast_id = :fid"),
                    {"fid": str(l001_fc.id)},
                ).mappings().all()
            }
            drivers_seed = [
                ("penetration", 0.7, 1.0, 1.3),
                ("price", 0.85, 1.0, 1.1),
            ]
            for dname, lo, ba, hi in drivers_seed:
                if dname in existing_drivers:
                    continue
                db.execute(
                    text(
                        "INSERT INTO forecast_drivers (id, forecast_id, driver, low, base, high) "
                        "VALUES (:id, :fid, :d, :l, :b, :h)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "fid": str(l001_fc.id),
                        "d": dname,
                        "l": lo,
                        "b": ba,
                        "h": hi,
                    },
                )

        # Actuals on L-004 (Launch phase) for 3 months at 80% of pro-rated Y1 forecast
        l004_fc = db.query(Forecast).filter(Forecast.launch_id == l004.id).first()
        if l004_fc and l004_fc.y1_patients:
            monthly_patients_target = l004_fc.y1_patients / 12.0
            monthly_sales_target = (l004_fc.y1_patients * (l004_fc.y1_net_price or 0)) / 12.0
            actual_patients = round(monthly_patients_target * 0.8)
            actual_sales = monthly_sales_target * 0.8
            for period in ("2026-03", "2026-04", "2026-05"):
                existing_act = db.execute(
                    text("SELECT 1 FROM actuals WHERE launch_id = :lid AND period = :p"),
                    {"lid": str(l004.id), "p": period},
                ).first()
                if existing_act:
                    continue
                db.execute(
                    text(
                        "INSERT INTO actuals (id, launch_id, period, net_sales, patients, source) "
                        "VALUES (:id, :lid, :p, :ns, :pt, 'seed')"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "lid": str(l004.id),
                        "p": period,
                        "ns": actual_sales,
                        "pt": actual_patients,
                    },
                )
                # Variance alerts (80% of target → -20% variance, exceeds 10% threshold)
                for metric, forecast_val, actual_val in (
                    ("patients", monthly_patients_target, actual_patients),
                    ("net_sales", monthly_sales_target, actual_sales),
                ):
                    if forecast_val == 0:
                        continue
                    var_pct = (actual_val - forecast_val) / forecast_val * 100.0
                    existing_va = db.execute(
                        text(
                            "SELECT 1 FROM variance_alerts WHERE launch_id = :lid AND period = :p AND metric = :m"
                        ),
                        {"lid": str(l004.id), "p": period, "m": metric},
                    ).first()
                    if existing_va:
                        continue
                    db.execute(
                        text(
                            "INSERT INTO variance_alerts (id, launch_id, period, metric, forecast_value, actual_value, variance_pct, threshold_pct, status) "
                            "VALUES (:id, :lid, :p, :m, :f, :a, :v, 10.0, 'open')"
                        ),
                        {
                            "id": str(uuid.uuid4()),
                            "lid": str(l004.id),
                            "p": period,
                            "m": metric,
                            "f": forecast_val,
                            "a": actual_val,
                            "v": var_pct,
                        },
                    )

        # PRD comment on L-001 executive_summary.launch_vision
        l001_prd = db.query(PRD).filter(PRD.launch_id == l001.id).first()
        if l001_prd:
            existing_cmt = db.execute(
                text(
                    "SELECT 1 FROM prd_comments WHERE prd_id = :pid AND section = 'executive_summary' AND field = 'launch_vision'"
                ),
                {"pid": str(l001_prd.id)},
            ).first()
            if not existing_cmt:
                db.execute(
                    text(
                        "INSERT INTO prd_comments (id, prd_id, section, field, user_id, body, mentions) "
                        "VALUES (:id, :pid, 'executive_summary', 'launch_vision', :uid, :body, CAST('[]' AS jsonb))"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "pid": str(l001_prd.id),
                        "uid": str(admin.id),
                        "body": "Recommend tightening vision to a 12-month measurable outcome (e.g., reimbursed access in 30 IDNs).",
                    },
                )

        db.commit()
        print(f"Seed complete. Org: {org.slug}. Admin: admin@demo.example / demo123")
    finally:
        try:
            db.execute(text("SELECT pg_advisory_unlock(727292727292)"))
            db.commit()
        except Exception:
            pass
        db.close()


if __name__ == "__main__":
    run()
