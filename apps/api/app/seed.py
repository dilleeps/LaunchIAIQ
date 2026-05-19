"""Seed demo data: an org, admin, 2 assets, 5 launches (L-001..L-005), milestone templates,
17 milestones per launch, a sample dependency, risks, KPIs, forecasts, and an openFDA connector
pre-configured for the demo assets.

Run: `python -m app.seed`
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import select

from .database import SessionLocal, engine, Base
from .integrations.openfda import ensure_source
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
    db = SessionLocal()
    try:
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
        print(f"Seed complete. Org: {org.slug}. Admin: admin@demo.example / demo123")
    finally:
        db.close()


if __name__ == "__main__":
    run()
