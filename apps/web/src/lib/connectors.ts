/** Per-connector configuration schema. Drives the dynamic settings form. */
import { z } from "zod";

export interface ConnectorFieldSpec {
  key: string;
  label: string;
  type: "text" | "password" | "number" | "url" | "select";
  placeholder?: string;
  required?: boolean;
  helper?: string;
  options?: string[];
  default?: string | number;
}

export interface ConnectorSchema {
  kind: string;
  category: "market_intel" | "regulatory" | "promotional" | "crm" | "erp" | "hr" | "auth";
  description: string;
  fields: ConnectorFieldSpec[];
  zod: z.ZodTypeAny;
}

const z_openfda = z.object({
  asset_query: z.string().optional(),
  limit: z.coerce.number().int().positive().max(100).default(25),
  api_key: z.string().optional(),
});

const z_simple_query = z.object({
  query: z.string().optional(),
  limit: z.coerce.number().int().positive().max(100).default(25),
});

const z_oauth2 = z.object({
  base_url: z.string().url("Must be a valid URL"),
  client_id: z.string().min(1, "Required"),
  client_secret: z.string().min(1, "Required"),
  scope: z.string().optional(),
});

const z_salesforce = z.object({
  instance_url: z.string().url("Must be a valid Salesforce instance URL"),
  client_id: z.string().min(1, "Required"),
  client_secret: z.string().min(1, "Required"),
  username: z.string().email("Must be a valid email"),
  security_token: z.string().min(1, "Required"),
});

const z_sap = z.object({
  base_url: z.string().url(),
  service_user: z.string().min(1),
  service_password: z.string().min(1),
  variance_threshold_pct: z.coerce.number().min(0).max(100).default(10),
});

const z_keycloak = z.object({
  realm_url: z.string().url("Must be a valid realm URL e.g. https://idp.example.com/realms/launchiq"),
  client_id: z.string().min(1),
  client_secret: z.string().min(1),
  protocol: z.enum(["saml", "oidc"]).default("oidc"),
});

const z_workday = z.object({
  tenant_url: z.string().url(),
  integration_user: z.string().min(1),
  integration_password: z.string().min(1),
  sync_org_chart: z.coerce.boolean().default(true),
});

export const CONNECTOR_SCHEMAS: Record<string, ConnectorSchema> = {
  openfda: {
    kind: "openfda",
    category: "market_intel",
    description: "FDA drug approvals, labels, recalls, adverse events. Free public API; key optional.",
    zod: z_openfda,
    fields: [
      { key: "asset_query", label: "Asset query (brand or INN)", type: "text", placeholder: "e.g. Mekinist (leave blank for broad pull)" },
      { key: "limit", label: "Records per sync", type: "number", default: 25 },
      { key: "api_key", label: "API key (optional, raises rate limit)", type: "password" },
    ],
  },
  clinicaltrials_gov: {
    kind: "clinicaltrials_gov",
    category: "market_intel",
    description: "ClinicalTrials.gov trial registry — sponsors, endpoints, status. Free API, no auth.",
    zod: z_simple_query,
    fields: [
      { key: "query", label: "Search term", type: "text", placeholder: "e.g. NSCLC" },
      { key: "limit", label: "Records per sync", type: "number", default: 25 },
    ],
  },
  dailymed: {
    kind: "dailymed",
    category: "market_intel",
    description: "DailyMed (NIH) structured product labels. Free API.",
    zod: z_simple_query,
    fields: [
      { key: "query", label: "Drug name", type: "text", placeholder: "e.g. tirzepatide" },
      { key: "limit", label: "Records per sync", type: "number", default: 25 },
    ],
  },
  who_gho: {
    kind: "who_gho",
    category: "market_intel",
    description: "WHO Global Health Observatory indicators (prevalence, burden of disease). Free API.",
    zod: z_simple_query,
    fields: [
      { key: "query", label: "Indicator code or keyword", type: "text", placeholder: "e.g. CHL_01" },
      { key: "limit", label: "Records per sync", type: "number", default: 25 },
    ],
  },
  cms_open_payments: {
    kind: "cms_open_payments",
    category: "market_intel",
    description: "US HCP industry payments. Free CMS open data.",
    zod: z_simple_query,
    fields: [
      { key: "query", label: "Manufacturer name", type: "text", placeholder: "e.g. Eli Lilly" },
      { key: "limit", label: "Records per sync", type: "number", default: 25 },
    ],
  },
  veeva_vault_rim: {
    kind: "veeva_vault_rim",
    category: "regulatory",
    description: "Veeva Vault RIM — regulatory submissions, approvals, label deltas.",
    zod: z_oauth2,
    fields: [
      { key: "base_url", label: "Vault base URL", type: "url", placeholder: "https://myvault.veevavault.com", required: true },
      { key: "client_id", label: "OAuth client ID", type: "text", required: true },
      { key: "client_secret", label: "OAuth client secret", type: "password", required: true },
      { key: "scope", label: "Scopes", type: "text", placeholder: "vault.read submissions.read" },
    ],
  },
  veeva_promomats: {
    kind: "veeva_promomats",
    category: "promotional",
    description: "Veeva Vault PromoMats — MLR/PRC material approval status.",
    zod: z_oauth2,
    fields: [
      { key: "base_url", label: "PromoMats base URL", type: "url", required: true },
      { key: "client_id", label: "OAuth client ID", type: "text", required: true },
      { key: "client_secret", label: "OAuth client secret", type: "password", required: true },
    ],
  },
  veeva_crm: {
    kind: "veeva_crm",
    category: "crm",
    description: "Veeva CRM — HCP calls, samples, engagement on Salesforce platform.",
    zod: z_salesforce,
    fields: [
      { key: "instance_url", label: "Salesforce instance URL", type: "url", placeholder: "https://yourorg.my.salesforce.com", required: true },
      { key: "client_id", label: "Consumer key", type: "text", required: true },
      { key: "client_secret", label: "Consumer secret", type: "password", required: true },
      { key: "username", label: "Integration user", type: "text", required: true },
      { key: "security_token", label: "Security token", type: "password", required: true },
    ],
  },
  iqvia_oce: {
    kind: "iqvia_oce",
    category: "crm",
    description: "IQVIA OCE Personal — HCP engagement (alternative to Veeva CRM).",
    zod: z_oauth2,
    fields: [
      { key: "base_url", label: "OCE base URL", type: "url", required: true },
      { key: "client_id", label: "Client ID", type: "text", required: true },
      { key: "client_secret", label: "Client secret", type: "password", required: true },
    ],
  },
  sap_s4: {
    kind: "sap_s4",
    category: "erp",
    description: "SAP S/4HANA — actuals (net sales, patients) + supply on-hand. Drives variance alerts.",
    zod: z_sap,
    fields: [
      { key: "base_url", label: "Gateway base URL", type: "url", placeholder: "https://sapgw.example.com/sap/opu/odata/sap/", required: true },
      { key: "service_user", label: "Service user", type: "text", required: true },
      { key: "service_password", label: "Service password", type: "password", required: true },
      { key: "variance_threshold_pct", label: "Variance alert threshold (%)", type: "number", default: 10 },
    ],
  },
  workday: {
    kind: "workday",
    category: "hr",
    description: "Workday — org structure, role assignments, RACI source of truth.",
    zod: z_workday,
    fields: [
      { key: "tenant_url", label: "Tenant URL", type: "url", required: true },
      { key: "integration_user", label: "Integration user", type: "text", required: true },
      { key: "integration_password", label: "Integration password", type: "password", required: true },
      { key: "sync_org_chart", label: "Sync org chart on each run", type: "select", options: ["true", "false"], default: "true" },
    ],
  },
  keycloak_sso: {
    kind: "keycloak_sso",
    category: "auth",
    description: "Keycloak SAML/OIDC SSO broker. Federate Okta, Azure AD, Ping or any IdP.",
    zod: z_keycloak,
    fields: [
      { key: "realm_url", label: "Realm URL", type: "url", placeholder: "https://idp.example.com/realms/launchiq", required: true },
      { key: "client_id", label: "Client ID", type: "text", required: true },
      { key: "client_secret", label: "Client secret", type: "password", required: true },
      { key: "protocol", label: "Protocol", type: "select", options: ["oidc", "saml"], default: "oidc" },
    ],
  },
};

export function getSchema(kind: string): ConnectorSchema | undefined {
  return CONNECTOR_SCHEMAS[kind];
}

export const CATEGORY_LABEL: Record<ConnectorSchema["category"], string> = {
  market_intel: "Market intelligence",
  regulatory: "Regulatory",
  promotional: "Promotional / MLR",
  crm: "CRM / Field engagement",
  erp: "ERP / Financials",
  hr: "HR / Identity",
  auth: "SSO / Authentication",
};
