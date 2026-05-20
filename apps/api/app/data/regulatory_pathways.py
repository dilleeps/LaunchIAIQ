"""Curated regulatory pathway library — gate sequences, dependencies and
industry-benchmark timelines.

Sources: FDA PDUFA performance goals, EMA centralized procedure clock,
BsUFA III for biosimilars, industry analysis (Tufts CSDD, Deloitte). These
are *benchmarks* — actual launch timelines vary by therapy area and
sponsor experience.

Each pathway defines:
- gates       : ordered list of regulatory gate dicts
- depends     : DAG edges between gate keys (gate cannot start until all
                its predecessors are complete)
- duration_d  : (min, typical, max) days from the prior dependency
- description : what happens at this gate
- artefact    : the document/decision evidence regulators expect
- failure_mode: what a 'no-go' looks like and impact on launch date
"""
from __future__ import annotations

# Reusable gate definitions (kept short — the UI displays them in cards)

PATHWAYS: dict[str, dict] = {
    # ────────────────────────────────────────────────────────────────
    "us_nce_standard": {
        "name": "US NCE — Standard NDA (505(b)(1))",
        "regulator": "FDA",
        "typical_total_days": 1825,  # IND filing → first commercial sale (~5 yrs)
        "summary": (
            "New Chemical Entity, standard 10-month FDA review. Most common pathway for "
            "small-molecule and biologic NCEs without breakthrough or fast-track designation."
        ),
        "gates": [
            {"key": "ind",         "name": "IND acceptance",                 "duration_d": (30, 30, 30),   "depends": [],
             "description": "FDA's 30-day Investigational New Drug review window. Silence = acceptance.",
             "artefact": "FDA IND acknowledgement letter",
             "failure_mode": "Clinical hold — no human dosing until issues resolved"},

            {"key": "eop2",        "name": "End-of-Phase-2 meeting",         "duration_d": (270, 730, 1825),"depends": ["ind"],
             "description": "Type B meeting; aligns Phase 3 design — endpoints, comparator, stats plan.",
             "artefact": "FDA written meeting minutes",
             "failure_mode": "Misalignment forces Phase 3 redesign; can add 12-24 months"},

            {"key": "preNDA",      "name": "Pre-NDA meeting",                "duration_d": (60, 90, 180),  "depends": ["eop2"],
             "description": "Final alignment on submission contents before NDA filing.",
             "artefact": "Pre-NDA meeting minutes",
             "failure_mode": "Filing deficiencies → Refuse-to-File risk"},

            {"key": "nda_filing",  "name": "NDA filing",                     "duration_d": (30, 60, 120),  "depends": ["preNDA"],
             "description": "Submit the complete dossier. PDUFA clock starts.",
             "artefact": "FDA filing receipt + PDUFA action date",
             "failure_mode": "Refuse-to-File letter (~10% of NDAs) — re-submit later"},

            {"key": "day60",       "name": "Day-60 filing acceptance",       "duration_d": (60, 60, 60),   "depends": ["nda_filing"],
             "description": "FDA confirms the file is reviewable. PDUFA date set.",
             "artefact": "Day-60 acceptance letter with assigned PDUFA date",
             "failure_mode": "RTF — launch slips ≥ 12 months"},

            {"key": "midcycle",    "name": "Mid-cycle communication",        "duration_d": (60, 90, 120),  "depends": ["day60"],
             "description": "FDA shares major review issues identified so far.",
             "artefact": "FDA mid-cycle communication letter",
             "failure_mode": "Major safety/efficacy concerns surfaced — CRL risk"},

            {"key": "adcom",       "name": "Advisory Committee (if needed)", "duration_d": (180, 210, 270),"depends": ["day60"], "optional": True,
             "description": "Public expert vote. Mandatory for novel mechanisms, controversial drugs.",
             "artefact": "AdCom briefing book + transcript + vote tally",
             "failure_mode": "Negative vote → high CRL probability (FDA follows vote ~70% of time)"},

            {"key": "latecycle",   "name": "Late-cycle meeting",             "duration_d": (210, 240, 270),"depends": ["day60"],
             "description": "Last formal exchange before FDA action.",
             "artefact": "Late-cycle meeting minutes",
             "failure_mode": "Outstanding deficiencies → 3-month PDUFA extension"},

            {"key": "pdufa",       "name": "PDUFA action (approval)",        "duration_d": (300, 304, 360),"depends": ["day60"],
             "description": "FDA approval / CRL / withdrawal. 10-month standard review from Day-60.",
             "artefact": "Approval letter + final label",
             "failure_mode": "Complete Response Letter — 6-18 month resubmission cycle"},

            {"key": "dea",         "name": "DEA Schedule designation (if controlled)",
             "duration_d": (60, 90, 120), "depends": ["pdufa"], "optional": True,
             "description": "Sch II–V designation for controlled substances. Required before shipment.",
             "artefact": "DEA Final Rule in Federal Register",
             "failure_mode": "Schedule II vs IV impacts distribution + REMS feasibility"},

            {"key": "rems",        "name": "REMS approval (if required)",    "duration_d": (0, 90, 180),  "depends": ["pdufa"], "optional": True,
             "description": "Risk Evaluation and Mitigation Strategy — for serious risks.",
             "artefact": "Approved REMS document + ETASU",
             "failure_mode": "Restricts distribution channels; may force certified-prescriber network"},

            {"key": "label",       "name": "Label finalization",             "duration_d": (0, 7, 14),    "depends": ["pdufa"],
             "description": "Section-by-section negotiation with FDA on USPI wording.",
             "artefact": "Final approved USPI / label",
             "failure_mode": "Restrictive label wording → erodes commercial opportunity"},

            {"key": "fcs",         "name": "First Commercial Sale",          "duration_d": (0, 30, 90),   "depends": ["pdufa", "dea", "rems", "label"],
             "description": "Drug ships to wholesalers; first patient receives.",
             "artefact": "First-fill claim or wholesaler shipment record",
             "failure_mode": "n/a (launch event)"},
        ],
    },

    # ────────────────────────────────────────────────────────────────
    "us_nce_priority": {
        "name": "US NCE — Priority Review (6 months)",
        "regulator": "FDA",
        "typical_total_days": 1460,
        "summary": (
            "Same NDA pathway with FDA's 6-month review clock instead of 10. Granted for drugs "
            "addressing serious conditions with potential significant improvement."
        ),
        "gates": [
            # Same gates but compressed PDUFA timeline
            {"key": "ind",        "name": "IND acceptance",                  "duration_d": (30, 30, 30),    "depends": []},
            {"key": "eop2",       "name": "End-of-Phase-2 meeting",          "duration_d": (270, 730, 1825),"depends": ["ind"]},
            {"key": "btd",        "name": "Breakthrough / Fast Track designation",
             "duration_d": (30, 60, 90), "depends": ["ind"],
             "description": "FDA grants breakthrough or fast-track status; unlocks rolling review + intensive guidance."},
            {"key": "preNDA",     "name": "Pre-NDA meeting",                 "duration_d": (60, 90, 180),   "depends": ["eop2"]},
            {"key": "nda_filing", "name": "NDA filing (rolling)",            "duration_d": (30, 60, 120),   "depends": ["preNDA", "btd"]},
            {"key": "day60",      "name": "Day-60 filing acceptance",        "duration_d": (60, 60, 60),    "depends": ["nda_filing"]},
            {"key": "pdufa",      "name": "Priority PDUFA action (6 mo)",    "duration_d": (180, 184, 240), "depends": ["day60"],
             "description": "6-month review clock under Priority Review."},
            {"key": "label",      "name": "Label finalization",              "duration_d": (0, 7, 14),      "depends": ["pdufa"]},
            {"key": "fcs",        "name": "First Commercial Sale",           "duration_d": (0, 30, 90),     "depends": ["pdufa", "label"]},
        ],
    },

    # ────────────────────────────────────────────────────────────────
    "eu_centralised": {
        "name": "EU Centralised Procedure (EMA)",
        "regulator": "EMA / CHMP",
        "typical_total_days": 2190,
        "summary": (
            "Single EU-wide marketing authorization via EMA. Mandatory for biologics, oncology, "
            "rare diseases. 210-day CHMP clock + clock-stops for sponsor responses to Q's."
        ),
        "gates": [
            {"key": "sci_advice", "name": "Scientific Advice (SAWP)",        "duration_d": (180, 270, 365),  "depends": [],
             "description": "Pre-submission advice on protocol / dossier design."},
            {"key": "presub",     "name": "Pre-submission meeting",          "duration_d": (60, 90, 180),    "depends": ["sci_advice"]},
            {"key": "maa_filing", "name": "MAA submission",                  "duration_d": (30, 60, 120),    "depends": ["presub"]},
            {"key": "validation", "name": "MAA validation",                  "duration_d": (10, 14, 21),     "depends": ["maa_filing"],
             "description": "EMA confirms file is complete; CHMP clock starts."},
            {"key": "day120",     "name": "Day-120 List of Questions",       "duration_d": (120, 120, 120),  "depends": ["validation"],
             "description": "First CHMP review round — major Qs issued. Clock stops here."},
            {"key": "day180",     "name": "Day-180 List of Outstanding Issues","duration_d": (60, 60, 60),   "depends": ["day120"]},
            {"key": "chmp",       "name": "CHMP Opinion",                    "duration_d": (30, 30, 30),     "depends": ["day180"]},
            {"key": "ec_dec",     "name": "European Commission Decision",    "duration_d": (60, 67, 90),     "depends": ["chmp"],
             "description": "EC decision binding across all 27 EU member states + EEA."},
            {"key": "fcs",        "name": "First Commercial Sale (EU lead market)",
             "duration_d": (30, 90, 180), "depends": ["ec_dec"]},
        ],
    },

    # ────────────────────────────────────────────────────────────────
    "us_biosimilar_351k": {
        "name": "US Biosimilar (351(k) BLA)",
        "regulator": "FDA",
        "typical_total_days": 1460,
        "summary": (
            "Biosimilar BLA under BPCIA section 351(k). Requires totality-of-evidence "
            "analytical + clinical similarity. BsUFA review goals: 10-month standard."
        ),
        "gates": [
            {"key": "type2",      "name": "Type 2 Biosimilar meeting",       "duration_d": (90, 120, 180),   "depends": [],
             "description": "FDA alignment on totality-of-evidence package design."},
            {"key": "type4",      "name": "Type 4 (pre-submission) meeting", "duration_d": (60, 90, 120),    "depends": ["type2"]},
            {"key": "bla_filing", "name": "351(k) BLA filing",               "duration_d": (30, 60, 120),    "depends": ["type4"]},
            {"key": "day60",      "name": "Day-60 acceptance",               "duration_d": (60, 60, 60),     "depends": ["bla_filing"]},
            {"key": "interchange","name": "Interchangeability designation (optional)",
             "duration_d": (60, 90, 180), "depends": ["day60"], "optional": True,
             "description": "Allows pharmacy-level substitution without prescriber intervention."},
            {"key": "bsufa",      "name": "BsUFA approval",                  "duration_d": (240, 304, 360),  "depends": ["day60"]},
            {"key": "fcs",        "name": "First Commercial Sale",           "duration_d": (180, 365, 730),  "depends": ["bsufa"],
             "description": "Often delayed by patent litigation (BPCIA 180-day notice + IPR proceedings)."},
        ],
    },

    # ────────────────────────────────────────────────────────────────
    "us_line_extension": {
        "name": "US Line Extension (sNDA / 505(b)(2))",
        "regulator": "FDA",
        "typical_total_days": 730,
        "summary": (
            "New indication, new dose, new formulation or new route for an already-approved NCE. "
            "Bridging studies, not full Phase 3. 10-month standard sNDA review."
        ),
        "gates": [
            {"key": "preMeet",    "name": "Pre-sNDA meeting",                "duration_d": (60, 90, 120),    "depends": []},
            {"key": "snda",       "name": "sNDA submission",                 "duration_d": (30, 60, 90),     "depends": ["preMeet"]},
            {"key": "day60",      "name": "Day-60 acceptance",               "duration_d": (60, 60, 60),     "depends": ["snda"]},
            {"key": "pdufa",      "name": "PDUFA action",                    "duration_d": (180, 304, 360),  "depends": ["day60"]},
            {"key": "label",      "name": "Label update",                    "duration_d": (0, 7, 14),       "depends": ["pdufa"]},
            {"key": "fcs",        "name": "Launch of new indication / form", "duration_d": (0, 30, 90),      "depends": ["pdufa", "label"]},
        ],
    },
}


def list_pathways() -> list[dict]:
    return [
        {
            "key": key,
            "name": p["name"],
            "regulator": p["regulator"],
            "typical_total_days": p["typical_total_days"],
            "gate_count": len(p["gates"]),
            "summary": p["summary"],
        }
        for key, p in PATHWAYS.items()
    ]


def get_pathway(key: str) -> dict | None:
    p = PATHWAYS.get(key)
    if not p:
        return None
    return {"key": key, **p}
