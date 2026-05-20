"""Takeda flagship pipeline launches + competitive intelligence seed.

Adds 3 real Takeda Phase 3 assets and 15 country launches (5 markets each):
- Oveporexton (TAK-861) — orexin-2 agonist, narcolepsy type 1
- Rusfertide (TAK-587) — hepcidin mimetic, polycythemia vera
- Zasocitinib (TAK-279) — oral TYK2 inhibitor, psoriasis / PsA

Pre-configures market-intel connectors with each asset's query terms so the
Market Pulse tab on every Takeda launch populates with real records on first sync.
Also seeds known competitors as static competitive_intel rows.

Run after `python -m app.seed` (idempotent on launch_code).
"""
from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import text

from .database import SessionLocal
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
    Organization,
    PRD,
    PRDVersion,
    Risk,
    RiskLaunchLink,
    Workstream,
)


# Real Takeda Phase 3 pipeline (publicly known as of 2025-2026)
TAKEDA_ASSETS = [
    {
        "brand_name": "Oveporexton",
        "inn": "oveporexton",
        "code": "TAK-861",
        "therapeutic_area": "Neurology",
        "molecule_type": "Small molecule",
        "moa": "Orexin-2 receptor (OX2R) agonist",
        "indication": "Narcolepsy type 1",
        "line_of_therapy": "1L",
        "route": "Oral",
        "dosing": "Once daily",
        "intel_terms": ["Oveporexton", "TAK-861", "narcolepsy"],
        "trial_id": "NCT06316245",
        "competitors": [
            {"name": "Wakix (pitolisant)", "company": "Bioprojet/Harmony", "moa": "H3 inverse agonist", "stage": "Marketed"},
            {"name": "Xyrem / Xywav (oxybate)", "company": "Jazz Pharma", "moa": "GHB receptor", "stage": "Marketed"},
            {"name": "Sunosi (solriamfetol)", "company": "Axsome", "moa": "DNRI", "stage": "Marketed"},
            {"name": "Orexin-2 agonist (TAK-925/danavorexton)", "company": "Takeda (terminated)", "moa": "OX2R", "stage": "Discontinued"},
        ],
    },
    {
        "brand_name": "Rusfertide",
        "inn": "rusfertide",
        "code": "PTG-300",
        "therapeutic_area": "Hematology",
        "molecule_type": "Peptide",
        "moa": "Hepcidin mimetic (injectable)",
        "indication": "Polycythemia vera",
        "line_of_therapy": "1L-2L",
        "route": "SC injection",
        "dosing": "Weekly",
        "intel_terms": ["Rusfertide", "PTG-300", "polycythemia vera"],
        "trial_id": "NCT05210790",
        "competitors": [
            {"name": "Besremi (ropeginterferon)", "company": "PharmaEssentia", "moa": "PEGylated interferon", "stage": "Marketed"},
            {"name": "Hydroxyurea", "company": "Generic", "moa": "Cytoreductive", "stage": "Marketed (generic)"},
            {"name": "Jakafi (ruxolitinib)", "company": "Incyte", "moa": "JAK1/2 inhibitor", "stage": "Marketed (2L)"},
        ],
    },
    {
        "brand_name": "Zasocitinib",
        "inn": "zasocitinib",
        "code": "TAK-279",
        "therapeutic_area": "Immunology",
        "molecule_type": "Small molecule",
        "moa": "Allosteric TYK2 inhibitor (oral)",
        "indication": "Moderate-to-severe plaque psoriasis; PsA",
        "line_of_therapy": "1L-2L",
        "route": "Oral",
        "dosing": "Once daily",
        "intel_terms": ["Zasocitinib", "TAK-279", "psoriasis", "psoriatic arthritis"],
        "trial_id": "NCT06088043",
        "competitors": [
            {"name": "Sotyktu (deucravacitinib)", "company": "BMS", "moa": "TYK2 inhibitor", "stage": "Marketed (direct competitor)"},
            {"name": "Skyrizi (risankizumab)", "company": "AbbVie", "moa": "IL-23 inhibitor", "stage": "Marketed (gold standard)"},
            {"name": "Cosentyx (secukinumab)", "company": "Novartis", "moa": "IL-17A inhibitor", "stage": "Marketed"},
            {"name": "Tremfya (guselkumab)", "company": "J&J", "moa": "IL-23 inhibitor", "stage": "Marketed"},
            {"name": "Otezla (apremilast)", "company": "Amgen", "moa": "PDE4 inhibitor", "stage": "Marketed (oral comparator)"},
        ],
    },
]


COUNTRIES_FIVE = [  # (code, type, phase, target_offset_days_from_2026Q3, expected_rag)
    ("USA", "NCE", "Pre-launch", 0,   "Amber"),
    ("DEU", "NCE", "Pre-launch", 60,  "Green"),
    ("JPN", "NCE", "Pre-launch", 120, "Green"),
    ("GBR", "NCE", "Pre-launch", 90,  "Amber"),
    ("FRA", "NCE", "Pre-launch", 180, "Amber"),
]


# Realistic per-market launch financials (relative; rounded). Net price per patient/year.
FINANCIALS = {
    "Oveporexton": {  # narcolepsy ≈ 1 in 2000; small specialty market
        "USA": (1800, 6500, 12000, 18000, 17500, 17000, "USD"),
        "DEU": (900, 3200, 6000, 12000, 11800, 11500, "EUR"),
        "JPN": (700, 2500, 4800, 1700000, 1650000, 1600000, "JPY"),
        "GBR": (400, 1500, 2800, 9000, 8800, 8500, "GBP"),
        "FRA": (450, 1700, 3100, 10500, 10300, 10000, "EUR"),
    },
    "Rusfertide": {  # PV ≈ 100k US patients; uncontrolled subset for rusfertide
        "USA": (650, 1700, 2800, 75000, 76500, 78000, "USD"),
        "DEU": (350, 950, 1600, 52000, 53000, 54000, "EUR"),
        "JPN": (200, 550, 950, 7800000, 8000000, 8200000, "JPY"),
        "GBR": (180, 480, 820, 45000, 46000, 47000, "GBP"),
        "FRA": (220, 600, 1050, 48000, 49000, 50000, "EUR"),
    },
    "Zasocitinib": {  # psoriasis large but crowded biologic class
        "USA": (4500, 14000, 24000, 38000, 39000, 40000, "USD"),
        "DEU": (1800, 5800, 10500, 16500, 17000, 17500, "EUR"),
        "JPN": (1200, 4000, 7500, 2200000, 2250000, 2300000, "JPY"),
        "GBR": (950, 3200, 5800, 12500, 13000, 13500, "GBP"),
        "FRA": (1100, 3800, 6900, 14000, 14500, 15000, "EUR"),
    },
}


def _ensure_competitive_intel_table(db) -> None:
    # No DEFAULT gen_random_uuid() — RDS doesn't ship pgcrypto enabled for
    # non-superuser roles. We generate UUIDs in Python on insert instead.
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS competitive_intel (
            id uuid PRIMARY KEY,
            org_id uuid NOT NULL,
            asset_id uuid NOT NULL,
            competitor_name text NOT NULL,
            company text,
            moa text,
            stage text,
            notes text,
            created_at timestamp DEFAULT now()
        )
    """))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_competitive_intel_asset ON competitive_intel(asset_id)"))
    db.commit()


def _insert_competitor(db, org_id, asset_id, c: dict) -> None:
    import uuid as _uuid
    existing = db.execute(
        text("SELECT 1 FROM competitive_intel WHERE asset_id = :a AND competitor_name = :n"),
        {"a": str(asset_id), "n": c["name"]},
    ).first()
    if existing:
        return
    db.execute(
        text("""INSERT INTO competitive_intel (id, org_id, asset_id, competitor_name, company, moa, stage)
                VALUES (:id, :o, :a, :n, :c, :m, :s)"""),
        {"id": str(_uuid.uuid4()), "o": str(org_id), "a": str(asset_id), "n": c["name"],
         "c": c.get("company"), "m": c.get("moa"), "s": c.get("stage")},
    )


def run() -> None:
    from .seed import STANDARD_MILESTONES, _get_or_create  # reuse

    db = SessionLocal()
    try:
        _ensure_competitive_intel_table(db)

        org = db.query(Organization).filter(Organization.slug == "demo").first()
        if not org:
            print("Demo org missing — run `python -m app.seed` first.")
            return

        admin_user_id = db.execute(
            text("SELECT id FROM users WHERE org_id = :o AND default_role = 'global_admin' LIMIT 1"),
            {"o": str(org.id)},
        ).scalar()

        ws_by_name = {w.name: w for w in db.query(Workstream).all()}
        countries_by_code = {c.code: c for c in db.query(Country).all()}

        ensure_source(db)
        source_row = db.execute(text("SELECT id FROM market_intel_sources WHERE name = 'openFDA'")).scalar()

        # Anchor target date: Oveporexton lead asset, then space subsequent launches
        base_date = date(2026, 9, 1)

        asset_objs: dict[str, Asset] = {}
        next_code_num = 100  # start above existing L-001..L-005 to keep ordering tidy

        for asset_def in TAKEDA_ASSETS:
            asset, _ = _get_or_create(
                db, Asset,
                defaults={
                    "inn": asset_def["inn"],
                    "molecule_type": asset_def["molecule_type"],
                    "moa": asset_def["moa"],
                    "therapeutic_area": asset_def["therapeutic_area"],
                    "line_of_therapy": asset_def["line_of_therapy"],
                    "route": asset_def["route"],
                    "dosing": asset_def["dosing"],
                },
                org_id=org.id,
                brand_name=asset_def["brand_name"],
            )
            asset_objs[asset_def["brand_name"]] = asset

            # Competitive intel rows
            for comp in asset_def["competitors"]:
                _insert_competitor(db, org.id, asset.id, comp)

            # Pre-configure an openFDA connector with the asset's query
            existing_conn = db.query(IntegrationConnector).filter(
                IntegrationConnector.org_id == org.id,
                IntegrationConnector.kind == "openfda",
                IntegrationConnector.config["asset_query"].astext == asset_def["brand_name"],
            ).first()
            if not existing_conn:
                db.add(IntegrationConnector(
                    org_id=org.id,
                    kind="openfda",
                    config={"asset_query": asset_def["brand_name"], "limit": 25, "label": f"{asset_def['brand_name']} — FDA monitor"},
                    enabled=True,
                ))
            # ClinicalTrials.gov connector
            ct_conn = db.query(IntegrationConnector).filter(
                IntegrationConnector.org_id == org.id,
                IntegrationConnector.kind == "clinicaltrials_gov",
                IntegrationConnector.config["query"].astext == asset_def["brand_name"],
            ).first()
            if not ct_conn:
                db.add(IntegrationConnector(
                    org_id=org.id,
                    kind="clinicaltrials_gov",
                    config={"query": asset_def["brand_name"], "limit": 25, "trial_id": asset_def["trial_id"]},
                    enabled=True,
                ))

            # Create the 5 country launches for this asset
            for i, (ccy_code, ltype, lphase, offset, rag) in enumerate(COUNTRIES_FIVE):
                country = countries_by_code.get(ccy_code)
                if not country:
                    continue
                code = f"L-{next_code_num:03d}"
                next_code_num += 1

                # Avoid duplicate (asset, country) launches if rerun
                exists = db.query(Launch).filter(
                    Launch.org_id == org.id,
                    Launch.asset_id == asset.id,
                    Launch.country_id == country.id,
                ).first()
                if exists:
                    continue

                tgt = base_date + timedelta(days=offset + i * 7)
                reg = tgt - timedelta(days=90)
                launch = Launch(
                    org_id=org.id,
                    launch_code=code,
                    asset_id=asset.id,
                    country_id=country.id,
                    launch_type=ltype,
                    launch_phase=lphase,
                    target_launch_date=tgt,
                    reg_approval_date=reg,
                    hta_decision="Pending",
                    overall_rag=rag,
                    country_launch_lead_user_id=admin_user_id,
                    global_brand_lead_user_id=admin_user_id,
                )
                db.add(launch)
                db.flush()

                # Milestones
                for j, (mname, ws_name, weight, is_gate) in enumerate(STANDARD_MILESTONES):
                    db.add(Milestone(
                        launch_id=launch.id,
                        workstream_id=ws_by_name[ws_name].id,
                        name=mname,
                        target_date=reg + timedelta(days=j * 21),
                        status="Not Started",
                        weight=weight,
                        is_gate=is_gate,
                    ))

                # Forecast
                fin = FINANCIALS[asset_def["brand_name"]][ccy_code]
                y1p, y2p, y3p, y1pr, y2pr, y3pr, ccy = fin
                db.add(Forecast(
                    launch_id=launch.id,
                    currency=ccy,
                    source="bottom_up",
                    y1_patients=y1p, y2_patients=y2p, y3_patients=y3p,
                    y1_net_price=y1pr, y2_net_price=y2pr, y3_net_price=y3pr,
                ))

                # PRD with rich payload reflecting the real asset
                prd = PRD(launch_id=launch.id, current_version=1)
                db.add(prd)
                db.flush()
                db.add(PRDVersion(
                    prd_id=prd.id,
                    version=1,
                    is_baseline=True,
                    payload={
                        "identification": {
                            "launch_id": code,
                            "asset": asset_def["brand_name"],
                            "inn": asset_def["inn"],
                            "country": country.name,
                            "indication": asset_def["indication"],
                            "launch_type": ltype,
                        },
                        "executive_summary": {
                            "launch_vision": f"Establish {asset_def['brand_name']} as first-line therapy in {asset_def['indication']} in {country.name} within 12 months of FCS.",
                            "priority_1": "Premium reimbursement secured at par or above SoC",
                            "priority_2": f"{asset_def['molecule_type']} positioning vs {asset_def['competitors'][0]['name']}",
                            "priority_3": f"Y1 target: {y1p} patient starts",
                        },
                        "asset_overview": {
                            "molecule_type": asset_def["molecule_type"],
                            "moa": asset_def["moa"],
                            "line_of_therapy": asset_def["line_of_therapy"],
                            "route": asset_def["route"],
                            "dosing": asset_def["dosing"],
                            "trial_id": asset_def["trial_id"],
                        },
                        "competitive_frame": {
                            "primary_competitor": asset_def["competitors"][0]["name"],
                            "competitive_set": ", ".join(c["name"] for c in asset_def["competitors"]),
                        },
                    },
                ))

        # Sample portfolio-wide risks specific to Takeda assets
        rsk = db.query(Risk).filter(Risk.description.like("%TYK2 class label%")).first()
        if not rsk and "Zasocitinib" in asset_objs:
            r = Risk(
                org_id=org.id,
                scope_type="asset",
                scope_id=asset_objs["Zasocitinib"].id,
                category="Regulatory",
                description="TYK2 class label risk: FDA black-box for serious infections / malignancy following JAK class warning may apply to TYK2 too",
                likelihood="M", impact="H", score=6,
                mitigation="Pre-engage FDA on selectivity data; differentiate from JAK1/2 toxicity profile.",
                target_resolution_date=date(2026, 6, 1),
                status="Open",
            )
            db.add(r)
            db.flush()
            for ln in db.query(Launch).filter(Launch.asset_id == asset_objs["Zasocitinib"].id).all():
                db.add(RiskLaunchLink(risk_id=r.id, launch_id=ln.id))

        # Reference-pricing dependency: Germany G-BA decision anchors EU launches
        for brand in ["Oveporexton", "Rusfertide", "Zasocitinib"]:
            a = asset_objs.get(brand)
            if not a:
                continue
            deu = db.query(Launch).filter(Launch.asset_id == a.id, Launch.country_id == countries_by_code["DEU"].id).first()
            fra = db.query(Launch).filter(Launch.asset_id == a.id, Launch.country_id == countries_by_code["FRA"].id).first()
            gbr = db.query(Launch).filter(Launch.asset_id == a.id, Launch.country_id == countries_by_code["GBR"].id).first()
            if deu and fra:
                if not db.query(Dependency).filter(Dependency.source_id == deu.id, Dependency.target_id == fra.id).first():
                    db.add(Dependency(org_id=org.id, source_type="launch", source_id=deu.id,
                                      target_type="launch", target_id=fra.id,
                                      link_type="references_price",
                                      notes="Germany G-BA AMNOG outcome anchors French HAS price negotiation"))
            if deu and gbr:
                if not db.query(Dependency).filter(Dependency.source_id == deu.id, Dependency.target_id == gbr.id).first():
                    db.add(Dependency(org_id=org.id, source_type="launch", source_id=deu.id,
                                      target_type="launch", target_id=gbr.id,
                                      link_type="references_price",
                                      notes="Germany IRP basket impacts NICE benchmarking"))

        # Seed launch setup (assumptions, meetings, team members, activity tree)
        # for every Takeda launch so the new wizard-shaped views light up
        _seed_launch_setup(db, org.id, asset_objs, countries_by_code)

        db.commit()
        print(f"Takeda seed complete: 3 assets, {next_code_num - 100} country launches added.")
    finally:
        db.close()


# ----- Launch setup backfill (assumptions + meetings + team + activities) -----

_DEMO_TEAM_BY_COUNTRY = {
    "USA": [("Sarah Chen", "Country Launch Leader", True), ("David Park", "Market Access Lead", False),
            ("Lisa Wong", "Medical Affairs Lead", False), ("Mike Johnson", "Commercial Lead", False)],
    "DEU": [("Hans Müller", "Country Launch Leader", True), ("Ingrid Schmidt", "AMNOG Lead", False),
            ("Klaus Weber", "Medical Affairs Lead", False)],
    "GBR": [("Emma Williams", "Country Launch Leader", True), ("James Cooper", "NICE Lead", False),
            ("Sophie Brown", "Medical Affairs Lead", False)],
    "FRA": [("Pierre Dubois", "Country Launch Leader", True), ("Marie Lefèvre", "HAS Lead", False),
            ("Antoine Martin", "Medical Affairs Lead", False)],
    "JPN": [("Kato Koki", "Country Launch Leader", True), ("Yuki Tanaka", "PMDA Lead", False),
            ("Hiroshi Sato", "Medical Affairs Lead", False)],
}


def _seed_launch_setup(db, org_id, asset_objs, countries_by_code) -> None:
    from .data.launch_templates import TEMPLATES, get_template, flatten_for_seed
    import uuid as _uuid

    # Pick template per region
    def _pick_template(country_code: str) -> str:
        if country_code == "USA":
            return "global_launch_framework_v8"
        if country_code in ("DEU",):
            return "german_launch"
        if country_code == "JPN":
            return "japan_launch"
        if country_code in ("GBR", "FRA"):
            return "eucan_simplified"
        return "global_launch_framework_v8"

    for asset in asset_objs.values():
        launches = db.query(Launch).filter(Launch.org_id == org_id, Launch.asset_id == asset.id).all()
        for launch in launches:
            country = db.query(Country).filter(Country.id == launch.country_id).first()
            if not country:
                continue
            tmpl_key = _pick_template(country.code)
            tmpl = get_template(tmpl_key)

            # Skip if already seeded
            existing_setup = db.execute(
                text("SELECT 1 FROM launch_setup WHERE launch_id = :id"), {"id": launch.id}
            ).first()
            if existing_setup:
                continue

            tgt = launch.target_launch_date or (date.today() + timedelta(days=365))
            reg_sub = tgt - timedelta(days=545)
            reg_app = launch.reg_approval_date or (tgt - timedelta(days=90))
            price_sub = reg_app + timedelta(days=14)
            price_app = reg_app + timedelta(days=180)
            reim_sub = price_app + timedelta(days=30)
            reim_app = reim_sub + timedelta(days=120)
            trade = tgt - timedelta(days=14)
            p3 = reg_sub - timedelta(days=180)

            db.execute(text("""
                INSERT INTO launch_setup (
                    launch_id, template_key, franchise, brand, indication_label, region,
                    commercial_launch_date, regulatory_submission, regulatory_approval,
                    pricing_submission, pricing_approval, reimbursement_submission,
                    reimbursement_approval, trade_stock_available, phase3_results,
                    mrp_value, mrp_currency, mrp_year, cumulative_mrp
                ) VALUES (
                    :lid, :tk, :fr, :br, :ind, :rg,
                    :cld, :rs, :ra, :ps, :pa, :rms, :rma, :tsa, :p3,
                    :mv, :mc, :my, :cmrp
                )
                ON CONFLICT (launch_id) DO NOTHING
            """), {
                "lid": launch.id, "tk": tmpl_key,
                "fr": asset.therapeutic_area, "br": asset.brand_name,
                "ind": None, "rg": country.region,
                "cld": tgt, "rs": reg_sub, "ra": reg_app,
                "ps": price_sub, "pa": price_app,
                "rms": reim_sub, "rma": reim_app,
                "tsa": trade, "p3": p3,
                "mv": 250_000_000, "mc": country.currency_code or "USD",
                "my": tgt.year + 4, "cmrp": 1_200_000_000,
            })

            # Meetings — defaults from template
            for m in tmpl["meetings"]:
                db.execute(text("""
                    INSERT INTO launch_meetings (
                        id, launch_id, meeting_key, name, cadence,
                        day_of_month, offset_months_before_launch, recurring
                    ) VALUES (:id, :lid, :k, :n, :c, :dom, :off, :r)
                    ON CONFLICT (launch_id, meeting_key) DO NOTHING
                """), {
                    "id": _uuid.uuid4(), "lid": launch.id,
                    "k": m["key"], "n": m["name"], "c": m["cadence"],
                    "dom": m["default"] if m["config_field"] == "day_of_month" else None,
                    "off": m["default"] if m["config_field"] == "offset_months_before_launch" else None,
                    "r": m["cadence"] == "monthly",
                })

            # Team members — demo roster per country
            team = _DEMO_TEAM_BY_COUNTRY.get(country.code, [])
            for name, role, mgr in team:
                db.execute(text("""
                    INSERT INTO launch_team_members (
                        id, launch_id, full_name, role_label, country_code, is_manager, therapy_area
                    ) VALUES (:id, :lid, :fn, :rl, :cc, :mgr, :ta)
                """), {
                    "id": _uuid.uuid4(), "lid": launch.id, "fn": name, "rl": role,
                    "cc": country.code, "mgr": mgr, "ta": asset.therapeutic_area,
                })

            # Activity tree
            rows = flatten_for_seed(tmpl["groups"])
            id_by_ordinal: dict = {}
            for r in rows:
                new_id = _uuid.uuid4()
                id_by_ordinal[r["ordinal"]] = new_id
                pid = id_by_ordinal.get(r["parent_ordinal"]) if r["parent_ordinal"] else None
                # Auto-mark first group as in progress for visual feedback
                stat = "Complete" if r["ordinal"].startswith("1.1") else ("In Progress" if r["ordinal"].startswith("1") else "Not Started")
                start = reg_sub - timedelta(days=730) if r["level"] == 1 else None
                end = tgt + timedelta(days=30) if r["level"] == 1 else None
                db.execute(text("""
                    INSERT INTO launch_activities (
                        id, launch_id, parent_id, group_key, group_name, ordinal, level,
                        name, status, country_code, importance, manual_complete,
                        start_date, end_date, organisation, assigned_count
                    ) VALUES (
                        :id, :lid, :pid, :gk, :gn, :ord, :lv,
                        :nm, :st, :cc, :imp, false,
                        :sd, :ed, :org, 0
                    )
                    ON CONFLICT (launch_id, ordinal) DO NOTHING
                """), {
                    "id": new_id, "lid": launch.id, "pid": pid,
                    "gk": r["group_key"], "gn": r["group_name"],
                    "ord": r["ordinal"], "lv": r["level"],
                    "nm": r["name"], "st": stat,
                    "cc": "Global" if r["level"] <= 2 else country.code,
                    "imp": r["importance"], "sd": start, "ed": end,
                    "org": "Global" if r["level"] <= 2 else country.name,
                })


if __name__ == "__main__":
    run()
