# Competitive Landscape — Pharma Launch Management

LaunchAIQ sits in the **pharma-native launch cockpit** category. Most adjacent tools either (a) cover a slice of the launch workflow deeply but don't model the portfolio holistically (Veeva, Aktana, Within3, Komodo), or (b) are generic project tools without a pharma data model (Smartsheet, Monday, Asana). The dedicated launch-excellence suites (IQVIA, ZS, Trinity, Indegene) are consulting-led, six-figure-plus, and slow to deploy.

## Feature matrix

Legend: ● full · ◐ partial · ○ none / unknown.

| Capability | LaunchAIQ | IQVIA Launch Excellence | Veeva Vault RIM+PromoMats+CRM | ZS REVO / Launch Excellence | Trinity TGaS | Aktana | Within3 | Indegene LE | Komodo Sentinel | OptimizeRx | Smartsheet/Monday |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Portfolio hierarchy (Portfolio → Asset → Indication → Launch → Workstream → Task) | ● | ◐ | ○ | ◐ | ○ | ○ | ○ | ◐ | ○ | ○ | ○ |
| Asset × Country matrix view | ● | ● | ○ | ● | ● | ○ | ○ | ◐ | ○ | ○ | ◐ |
| PRD with versioning + field-level history | ● | ○ | ◐ (Vault docs) | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| Configurable milestone templates by launch type (NCE vs LE vs biosimilar) | ● | ◐ | ○ | ◐ | ◐ | ○ | ○ | ◐ | ○ | ○ | ◐ (templates, not pharma) |
| Stage gates with sign-off + approval workflow | ◐ (Phase 2) | ◐ | ● (Vault RIM) | ◐ | ○ | ○ | ○ | ◐ | ○ | ○ | ◐ |
| Auto-RAG rollup from task-level data | ● | ◐ | ○ | ● | ○ | ○ | ○ | ◐ | ○ | ○ | ○ |
| Typed cross-launch dependencies (blocks / informs / references_price / shares_supply) | ● | ○ | ○ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| Critical-path / downstream-impact walk | ● (recursive CTE) | ○ | ○ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ | ◐ (Gantt only) |
| IRP / reference-pricing simulator | ◐ (Phase 2) | ● | ○ | ◐ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ |
| What-if scenario cloning without overwriting baseline | ◐ (Phase 2 — model in place) | ◐ | ○ | ◐ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| Bottom-up + top-down forecast reconciliation | ◐ (Phase 2) | ● | ○ | ● | ◐ | ○ | ○ | ◐ | ○ | ○ | ○ |
| Versioned multi-currency FX assumptions | ◐ (Phase 2) | ● | ○ | ● | ○ | ○ | ○ | ◐ | ○ | ○ | ○ |
| Sensitivity / driver analysis | ◐ (Phase 2) | ● | ○ | ● | ◐ | ○ | ○ | ◐ | ○ | ○ | ○ |
| Variance alerts (actuals vs forecast) | ◐ (Phase 2) | ● | ○ | ● | ○ | ◐ | ○ | ◐ | ◐ | ○ | ○ |
| Risk register w/ portfolio-wide risk interdependencies | ● | ◐ | ○ | ◐ | ◐ | ○ | ○ | ◐ | ○ | ○ | ◐ |
| RACI by workstream + role | ● | ◐ | ○ | ◐ | ◐ | ○ | ○ | ◐ | ○ | ○ | ◐ |
| Leading + lagging KPI tracking with RAG | ● | ● | ◐ (CRM only) | ● | ◐ | ◐ | ○ | ◐ | ◐ | ◐ | ○ |
| Field-level RBAC (global owns positioning, country owns local adaptation) | ◐ (Phase 2 — schema in place) | ◐ | ◐ | ◐ | ○ | ○ | ○ | ◐ | ○ | ○ | ○ |
| Multi-tenant SaaS (org isolation by FK) | ● | ● | ● | ● | ◐ | ● | ● | ● | ● | ● | ● |
| Audit log of every write | ● | ● | ● | ● | ◐ | ◐ | ◐ | ● | ● | ◐ | ◐ |
| @mention / comments at the field level | ◐ (Phase 2) | ○ | ◐ | ○ | ○ | ○ | ● | ○ | ○ | ○ | ● |
| Veeva Vault RIM integration | ◐ (stub) | ◐ | ● (native) | ◐ | ○ | ◐ | ○ | ◐ | ○ | ◐ | ○ |
| Veeva PromoMats / MLR integration | ◐ (stub) | ◐ | ● | ◐ | ○ | ◐ | ○ | ◐ | ○ | ◐ | ○ |
| Veeva CRM / IQVIA OCE integration | ◐ (stub) | ● (OCE) | ● (CRM) | ◐ | ○ | ● | ○ | ◐ | ◐ | ● | ○ |
| SAP / ERP actuals + supply integration | ◐ (stub) | ◐ | ◐ | ◐ | ○ | ○ | ○ | ◐ | ○ | ○ | ○ |
| HR / Workday / SCIM org-structure sync | ◐ (stub) | ◐ | ◐ | ◐ | ○ | ○ | ○ | ◐ | ○ | ○ | ◐ |
| SAML / OIDC SSO | ◐ (Keycloak — Phase 2) | ● | ● | ● | ● | ● | ● | ● | ● | ● | ● |
| **Market intelligence — built-in free sources** | **●** (openFDA live; ClinicalTrials, DailyMed, NICE, G-BA, HAS, CADTH, PBAC, WHO GHO, CMS Open Payments, PubMed in roadmap) | ● (paid IQVIA datasets) | ○ | ◐ (paid datasets) | ◐ (advisory) | ○ | ○ | ◐ | ● (paid Komodo claims) | ◐ | ○ |
| Open-source friendly / self-hostable | ● | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ | ○ |
| Pricing tier | SMB-friendly | $$$$ (six-figure) | $$$ (per seat) | $$$$ | $$$ (advisory) | $$$ | $$ | $$$ | $$$$ | $$ | $ |

## Free market-intelligence sources wired (or scheduled)

| Source | What it provides | API | Phase |
|---|---|---|---|
| **openFDA** | FDA approvals, labels, recalls, adverse events, NDC | `api.fda.gov` REST | **1 (live)** |
| ClinicalTrials.gov | Trial registry, sponsors, endpoints | `clinicaltrials.gov/api/v2` | 1 (stub) |
| DailyMed (NIH) | Structured product labels | `dailymed.nlm.nih.gov` | 1 (stub) |
| EMA EPAR | EU approvals | dataset CSVs | 2 |
| NICE (UK HTA) | Appraisal outcomes | `api.nice.org.uk` | 2 |
| G-BA / IQWiG (Germany HTA) | Benefit assessments | RSS | 2 |
| HAS (France HTA) | Transparency Commission opinions | Open data | 2 |
| CADTH (Canada HTA) | Reimbursement reviews | Open data | 2 |
| PBAC (Australia HTA) | Public summary documents | scrape | 2 |
| WHO GHO | Global health indicators / burden | `ghoapi.azureedge.net` | 2 |
| CMS Open Payments | US HCP industry payments | `openpaymentsdata.cms.gov` | 2 |
| NIH RePORTER | Funded research | REST | 2 |
| PubMed E-utilities | Literature | `eutils.ncbi.nlm.nih.gov` | 2 |
| WHO ICTRP | Global trial meta-search | weekly XML | 2 |
| RxNorm / NDC directory | Drug normalization | REST | 2 |

Paid alternatives (GlobalData, Evaluate Pharma, Cortellis, IQVIA MIDAS) deliberately **out of scope** — the value of LaunchAIQ is precisely that the free sources cover the regulatory + HTA + trial spine of competitive intelligence without a six-figure data licence.

## Positioning summary

- **vs. IQVIA / ZS:** comparable launch-tracking depth at SMB pricing, deploys in days not quarters, no consulting tie-in.
- **vs. Veeva stack:** Veeva is the system of record for regulatory documents and field activity, **not** a portfolio launch cockpit. LaunchAIQ integrates with Veeva (Phase 2) rather than competing.
- **vs. Smartsheet/Monday:** pharma data model out of the box — milestone templates for NCE/LE/biosimilar, HTA-aware Asset × Country grid, typed dependencies, RACI tied to workstreams.
- **vs. paid intel platforms (Komodo, Definitive, IQVIA MIDAS):** complementary. LaunchAIQ aggregates **free public** regulatory/HTA/trial intelligence and surfaces it inline on the launch where it's actionable.
