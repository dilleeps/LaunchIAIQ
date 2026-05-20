"""Launch framework templates — match Takeda's LaunchPad system.

Each template defines:
- name      : human-readable label
- scope     : Global / Region / Country
- meetings  : default Launch Management Meeting cadence
- groups    : ordered milestone groups (Product / Market / Takeda preparation)
              each with a tree of activities (level 1 → level 2 → level 3)
- assumptions_fields : which Key Launch Assumption dates the template surfaces
"""
from __future__ import annotations


# ----- Reusable milestone group tree (Takeda Global Launch Framework V8) -----

_GLOBAL_V8_GROUPS = [
    {
        "key": "product_prep",
        "name": "Product preparation",
        "phase": "Product",
        "activities": [
            {
                "id": "1", "name": "Brand Strategy", "importance": "Critical",
                "children": [
                    {"id": "1.1", "name": "Patient Journey Excellence", "importance": "Critical", "children": [
                        {"id": "1.1.1", "name": "Landscaping: qualitative assessment of disease", "importance": "Critical"},
                        {"id": "1.1.2", "name": "Assess unmet need / Standard of Care at each step", "importance": "Critical", "children": [
                            {"id": "1.1.2.1", "name": "Preliminary assessment of unmet need / SoC", "importance": "Critical"},
                            {"id": "1.1.2.2", "name": "Retrieve and validate unmet patient needs", "importance": "Critical"},
                            {"id": "1.1.2.3", "name": "Identify Patient Market Value Drivers", "importance": "Critical"},
                            {"id": "1.1.2.4", "name": "Retrieve and validate unmet physician needs", "importance": "Critical"},
                            {"id": "1.1.2.5", "name": "Understand key market dynamics for patients", "importance": "Critical"},
                        ]},
                    ]},
                    {"id": "1.2", "name": "Brand Positioning", "importance": "Critical", "children": [
                        {"id": "1.2.1", "name": "Develop brand positioning statement", "importance": "Critical"},
                        {"id": "1.2.2", "name": "Test positioning with HCPs / patients", "importance": "High"},
                    ]},
                    {"id": "1.3", "name": "Brand Identity & Naming", "importance": "High"},
                ],
            },
            {
                "id": "2", "name": "Messaging and Materials", "importance": "Critical",
                "children": [
                    {"id": "2.1", "name": "Core Messaging Platform"},
                    {"id": "2.2", "name": "Promotional Material Development"},
                    {"id": "2.3", "name": "Disease State Education"},
                    {"id": "2.4", "name": "Branded Campaign", "children": [
                        {"id": "2.4.1", "name": "HCP campaign assets"},
                        {"id": "2.4.2", "name": "Patient campaign assets"},
                    ]},
                ],
            },
            {
                "id": "3", "name": "Access Strategy / Value Dossier / Pricing", "importance": "Critical",
                "children": [
                    {"id": "3.1", "name": "Global Value Dossier (GVD)"},
                    {"id": "3.2", "name": "Pricing Strategy & Reference Pricing Analysis"},
                    {"id": "3.3", "name": "Health Economic Model"},
                    {"id": "3.4", "name": "Payer Value Proposition"},
                ],
            },
            {
                "id": "4", "name": "Regulatory Strategy", "importance": "Critical",
                "children": [
                    {"id": "4.1", "name": "Target Product Profile (TPP) finalization"},
                    {"id": "4.2", "name": "Submission Plan"},
                    {"id": "4.3", "name": "Label Strategy & Negotiation"},
                ],
            },
        ],
    },
    {
        "key": "market_prep",
        "name": "Market preparation",
        "phase": "Market",
        "activities": [
            {
                "id": "5", "name": "Payers / Government Relations", "importance": "Critical",
                "children": [
                    {"id": "5.1", "name": "HTA Engagement Plan"},
                    {"id": "5.2", "name": "Payer Advisory Boards"},
                    {"id": "5.3", "name": "Government Affairs"},
                ],
            },
            {
                "id": "6", "name": "KOL & CoE Engagement", "importance": "Critical",
                "children": [
                    {"id": "6.1", "name": "KOL mapping & tiering"},
                    {"id": "6.2", "name": "Advisory Boards"},
                    {"id": "6.3", "name": "Centers of Excellence identification"},
                ],
            },
            {
                "id": "7", "name": "Patient Strategy / Advocacy / Services", "importance": "High",
                "children": [
                    {"id": "7.1", "name": "Patient Advocacy partnerships"},
                    {"id": "7.2", "name": "Patient Support Program design"},
                    {"id": "7.3", "name": "Hub services & co-pay"},
                ],
            },
        ],
    },
    {
        "key": "takeda_prep",
        "name": "Takeda preparation",
        "phase": "Internal",
        "activities": [
            {
                "id": "8", "name": "Early Access", "importance": "High",
                "children": [
                    {"id": "8.1", "name": "Expanded Access Program"},
                    {"id": "8.2", "name": "Named Patient / Compassionate Use"},
                ],
            },
            {
                "id": "9", "name": "Market Sizing / Forecasting", "importance": "Critical",
                "children": [
                    {"id": "9.1", "name": "Epidemiology refresh"},
                    {"id": "9.2", "name": "Bottom-up forecast"},
                    {"id": "9.3", "name": "Top-down forecast reconciliation"},
                ],
            },
            {
                "id": "10", "name": "Customer Facing Excellence", "importance": "Critical",
                "children": [
                    {"id": "10.1", "name": "Field force sizing & deployment"},
                    {"id": "10.2", "name": "Training curriculum"},
                    {"id": "10.3", "name": "Incentive compensation plan"},
                ],
            },
            {"id": "11", "name": "Resourcing", "importance": "High"},
            {"id": "12", "name": "Launch Preparedness Indicators (LPI)", "importance": "Critical"},
            {"id": "13", "name": "Global Manufacturing & Supply (GMS)", "importance": "Critical", "children": [
                {"id": "13.1", "name": "API supply readiness"},
                {"id": "13.2", "name": "Trade pack development"},
                {"id": "13.3", "name": "Launch inventory build"},
            ]},
        ],
    },
]


_EUCAN_GROUPS = [
    {
        "key": "product_prep", "name": "Product preparation", "phase": "Product",
        "activities": [
            {"id": "1", "name": "EU Brand Plan adaptation", "importance": "Critical"},
            {"id": "2", "name": "Local promotional materials (MLR-cleared)", "importance": "Critical"},
            {"id": "3", "name": "EU Value Dossier + cost-effectiveness model", "importance": "Critical"},
            {"id": "4", "name": "Regulatory: EMA Centralised Procedure milestones", "importance": "Critical"},
        ],
    },
    {
        "key": "market_prep", "name": "Market preparation", "phase": "Market",
        "activities": [
            {"id": "5", "name": "HTA submissions (NICE, G-BA, HAS, AIFA)", "importance": "Critical"},
            {"id": "6", "name": "EU KOL & treatment guideline engagement", "importance": "Critical"},
            {"id": "7", "name": "Patient organizations (Europe)", "importance": "High"},
        ],
    },
    {
        "key": "takeda_prep", "name": "Takeda preparation", "phase": "Internal",
        "activities": [
            {"id": "8", "name": "Named Patient programs (pre-approval)", "importance": "High"},
            {"id": "9", "name": "EU forecast & in-country pricing", "importance": "Critical"},
            {"id": "10", "name": "Field force build", "importance": "High"},
            {"id": "11", "name": "EU supply allocation", "importance": "Critical"},
        ],
    },
]


_GEM_COUNTRY_GROUPS = [
    {
        "key": "product_prep", "name": "Product preparation", "phase": "Product",
        "activities": [
            {"id": "1", "name": "Local brand adaptation"},
            {"id": "2", "name": "Materials translation & MLR"},
            {"id": "3", "name": "Local pricing dossier"},
            {"id": "4", "name": "Local regulatory submission"},
        ],
    },
    {
        "key": "market_prep", "name": "Market preparation", "phase": "Market",
        "activities": [
            {"id": "5", "name": "Local payer engagement"},
            {"id": "6", "name": "Local KOL plan"},
            {"id": "7", "name": "Patient programs"},
        ],
    },
    {
        "key": "takeda_prep", "name": "Takeda preparation", "phase": "Internal",
        "activities": [
            {"id": "8", "name": "Country forecast"},
            {"id": "9", "name": "Field readiness"},
            {"id": "10", "name": "Local supply"},
        ],
    },
]


_STANDARD_ASSUMPTIONS = [
    "commercial_launch_date",
    "regulatory_submission",
    "regulatory_approval",
    "pricing_submission",
    "pricing_approval",
    "reimbursement_submission",
    "reimbursement_approval",
    "trade_stock_available",
    "phase3_results",
]

_DEFAULT_MEETINGS = [
    {"key": "ccft",       "name": "CCFT (Country Cross-Functional Team)",  "cadence": "monthly", "config_field": "day_of_month", "default": 15},
    {"key": "checkpoint", "name": "Country Checkpoint Review L-18M",        "cadence": "milestone", "config_field": "offset_months_before_launch", "default": 18},
    {"key": "gps1",       "name": "GPS Checkpoint Review 1",                "cadence": "milestone", "config_field": "offset_months_before_launch", "default": 24},
    {"key": "gps2",       "name": "GPS Checkpoint Review 2",                "cadence": "milestone", "config_field": "offset_months_before_launch", "default": 18},
    {"key": "gps3",       "name": "GPS Checkpoint Review 3",                "cadence": "milestone", "config_field": "offset_months_before_launch", "default": 12},
    {"key": "gps4",       "name": "GPS Checkpoint Review 4",                "cadence": "milestone", "config_field": "offset_months_before_launch", "default": 6},
    {"key": "law",        "name": "Launch Activation Workshop (LAW)",       "cadence": "milestone", "config_field": "offset_months_before_launch", "default": 9},
]


TEMPLATES: dict[str, dict] = {
    "global_launch_framework_v8": {
        "name": "Global Launch Framework V8",
        "scope": "Global",
        "regulator_hint": "FDA / EMA",
        "summary": "Full global launch framework — 3 phases × 13 activity streams. Default for NCEs across all major markets.",
        "groups": _GLOBAL_V8_GROUPS,
        "meetings": _DEFAULT_MEETINGS,
        "assumptions_fields": _STANDARD_ASSUMPTIONS,
    },
    "eucan_simplified": {
        "name": "EUCAN Simplified Framework",
        "scope": "Region",
        "regulator_hint": "EMA / Health Canada",
        "summary": "Streamlined EU + Canada framework focused on HTA-heavy markets.",
        "groups": _EUCAN_GROUPS,
        "meetings": _DEFAULT_MEETINGS,
        "assumptions_fields": _STANDARD_ASSUMPTIONS,
    },
    "gem_country": {
        "name": "GEM Country Launch Framework",
        "scope": "Country",
        "regulator_hint": "Local NRA",
        "summary": "Growth & Emerging Markets country-level framework. Lighter weight; local adaptation focus.",
        "groups": _GEM_COUNTRY_GROUPS,
        "meetings": [m for m in _DEFAULT_MEETINGS if m["key"] in ("ccft", "checkpoint", "law")],
        "assumptions_fields": _STANDARD_ASSUMPTIONS,
    },
    "german_launch": {
        "name": "German Launch Template",
        "scope": "Country",
        "regulator_hint": "BfArM / G-BA",
        "summary": "Germany-specific framework. AMNOG dossier + G-BA early benefit assessment baked in.",
        "groups": _GEM_COUNTRY_GROUPS,
        "meetings": _DEFAULT_MEETINGS,
        "assumptions_fields": _STANDARD_ASSUMPTIONS + ["amnog_dossier_submission", "gba_decision"],
    },
    "japan_launch": {
        "name": "Japan Launch Framework",
        "scope": "Country",
        "regulator_hint": "PMDA / Chuikyo",
        "summary": "Japan-specific framework with PMDA + NHI price listing milestones.",
        "groups": _GEM_COUNTRY_GROUPS,
        "meetings": _DEFAULT_MEETINGS,
        "assumptions_fields": _STANDARD_ASSUMPTIONS + ["nhi_price_listing"],
    },
    "korea_launch": {
        "name": "Korea Launch Framework",
        "scope": "Country",
        "regulator_hint": "MFDS / HIRA",
        "summary": "Korea-specific framework with MFDS approval and HIRA reimbursement.",
        "groups": _GEM_COUNTRY_GROUPS,
        "meetings": _DEFAULT_MEETINGS,
        "assumptions_fields": _STANDARD_ASSUMPTIONS,
    },
    "global_diagnostic": {
        "name": "Global Diagnostic Framework",
        "scope": "Global",
        "regulator_hint": "FDA CDRH / IVDR",
        "summary": "Companion / complementary diagnostic launch framework.",
        "groups": _GEM_COUNTRY_GROUPS,
        "meetings": _DEFAULT_MEETINGS,
        "assumptions_fields": _STANDARD_ASSUMPTIONS,
    },
    "global_device_v2": {
        "name": "Global Device Template V2",
        "scope": "Global",
        "regulator_hint": "FDA CDRH / MDR",
        "summary": "Drug-device combo and medical device launch framework.",
        "groups": _GEM_COUNTRY_GROUPS,
        "meetings": _DEFAULT_MEETINGS,
        "assumptions_fields": _STANDARD_ASSUMPTIONS,
    },
    "global_standalone_diagnostic": {
        "name": "Global Standalone Diagnostic Framework",
        "scope": "Global",
        "regulator_hint": "FDA CDRH / IVDR",
        "summary": "Standalone IVD/diagnostic launch (no paired therapeutic).",
        "groups": _GEM_COUNTRY_GROUPS,
        "meetings": _DEFAULT_MEETINGS,
        "assumptions_fields": _STANDARD_ASSUMPTIONS,
    },
}


def list_templates() -> list[dict]:
    return [
        {
            "key": k,
            "name": t["name"],
            "scope": t["scope"],
            "regulator_hint": t["regulator_hint"],
            "summary": t["summary"],
            "group_count": len(t["groups"]),
            "activity_count": _count_activities(t["groups"]),
            "meeting_count": len(t["meetings"]),
        }
        for k, t in TEMPLATES.items()
    ]


def get_template(key: str) -> dict | None:
    t = TEMPLATES.get(key)
    if not t:
        return None
    return {"key": key, **t}


def _count_activities(groups: list[dict]) -> int:
    n = 0
    for g in groups:
        for a in g.get("activities", []):
            n += 1 + _count_children(a)
    return n


def _count_children(a: dict) -> int:
    kids = a.get("children", [])
    return len(kids) + sum(_count_children(k) for k in kids)


def flatten_for_seed(groups: list[dict]) -> list[dict]:
    """Flatten the nested tree into rows suitable for DB insertion.

    Each row: {ordinal, group_key, group_name, level, parent_ordinal, name, importance}
    where ordinal matches the displayed ID ("1", "1.1", "1.1.2", ...).
    """
    rows: list[dict] = []
    for g in groups:
        for a in g.get("activities", []):
            _flatten(rows, a, group_key=g["key"], group_name=g["name"], parent_ordinal=None, level=1)
    return rows


def _flatten(rows: list[dict], node: dict, *, group_key: str, group_name: str, parent_ordinal: str | None, level: int):
    rows.append({
        "ordinal": node["id"],
        "group_key": group_key,
        "group_name": group_name,
        "level": level,
        "parent_ordinal": parent_ordinal,
        "name": node["name"],
        "importance": node.get("importance", "Standard"),
    })
    for child in node.get("children", []):
        _flatten(rows, child, group_key=group_key, group_name=group_name, parent_ordinal=node["id"], level=level + 1)
