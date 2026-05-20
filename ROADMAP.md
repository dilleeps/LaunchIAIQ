# LaunchAIQ Roadmap

## Phase 1 — MVP scaffold (this PR) ✓

**Auth & RBAC**
- JWT login, org register, `/auth/me`
- Roles: `global_admin`, `global_brand_lead`, `country_launch_lead`, `medical`, `market_access`, `finance`, `viewer`
- Role assignments table for granular scopes (portfolio / asset / launch / workstream)
- Audit log table

**Core data model**
- Organization → Portfolio → Asset → Indication → Launch → Workstream → Task hierarchy
- PRD with `current_version` + `prd_versions` JSONB payloads + `prd_field_history` diff log
- Milestones from configurable `milestone_templates` (per launch_type)
- Typed `dependencies` (blocks / informs / references_price / shares_supply / shares_evidence)
- Risks with `risk_launch_links` many-to-many
- Forecasts (bottom-up / top-down sources), KPIs, RACI entries
- Recursive-CTE downstream walk for any launch

**UI**
- Portfolio Overview (4 stat cards + launch cards)
- Asset × Country Matrix (RAG cells)
- Milestone Tracker (next 90 days, gates marked)
- Launch Detail (7 tabs: PRD / Milestones / Risks / KPIs / Forecast / Market Pulse / Dependencies)
- Admin (integration connectors)

**Integrations**
- `BaseConnector` framework + `integration_connectors` + `external_records`
- **openFDA — live** (drug labels, recalls)
- Stubs for ClinicalTrials.gov, DailyMed, Veeva Vault RIM, Veeva PromoMats, Veeva CRM, IQVIA OCE, SAP S/4, Workday, Keycloak SSO
- APScheduler nightly job

**Auto-RAG**
- `compute_rag()` derives Green/Amber/Red from milestone weighted % complete + gate blockers + linked high-risk count

## Phase 2 — Collaboration & access depth

- **Keycloak SSO** (SAML / OIDC) — Okta, Azure AD, Ping
- **Field-level permissions**: global owns positioning, country owns local adaptation, enforced server-side
- **Stage-gate sign-off** workflow (named role approvals, decision docs)
- **PRD field comments + @mentions**
- **Dependencies graph view** (react-flow + dagre)
- **Gantt timeline** (frappe-gantt)
- **Scenario clone + side-by-side compare** (model already in place via `scenarios` + `scenario_overrides`)
- **IRP simulator** — change one country's price, cascade across `reference_pricing_links`
- HTA connectors: EMA EPAR, NICE, G-BA/IQWiG, HAS, CADTH, PBAC
- PubMed + WHO GHO + ClinicalTrials.gov live ingestion

## Phase 3 — Enterprise integrations

- Veeva Vault RIM connector (regulatory submission/approval status)
- Veeva PromoMats connector (MLR/PRC status)
- Veeva CRM connector (HCP engagement metrics)
- SAP S/4HANA connector (actuals + supply)
- **Variance alert engine**: actuals vs forecast monthly, auto-flag breaches
- **Versioned FX assumptions** + multi-currency rollups
- **Sensitivity analysis** on price / penetration / persistence / compliance

## Phase 4 — Polish & AI

- IQVIA OCE connector (Veeva CRM alternative)
- Workday / SCIM provisioning
- AI features: auto-summarize risks, suggest mitigations from historical launches, draft PRD sections
- Mobile companion
- White-label theming
- SOC 2 controls (already audit-logging; needs encryption-at-rest + DR runbook)
