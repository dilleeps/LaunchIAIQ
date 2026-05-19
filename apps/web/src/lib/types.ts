export interface User {
  id: string;
  org_id: string;
  email: string;
  full_name: string;
  default_role: string;
}

export interface Asset {
  id: string;
  brand_name: string;
  inn?: string | null;
  therapeutic_area?: string | null;
  molecule_type?: string | null;
  moa?: string | null;
}

export interface Country {
  id: string;
  code: string;
  name: string;
  region?: string | null;
  currency_code?: string | null;
  hta_body?: string | null;
}

export interface Launch {
  id: string;
  launch_code: string;
  asset: Asset;
  country: Country;
  launch_type?: string | null;
  launch_phase?: string | null;
  target_launch_date?: string | null;
  reg_approval_date?: string | null;
  hta_decision?: string | null;
  overall_rag: "Green" | "Amber" | "Red";
  status: string;
  notes?: string | null;
}

export interface Milestone {
  id: string;
  launch_id: string;
  name: string;
  target_date?: string | null;
  actual_date?: string | null;
  status: string;
  weight: number;
  is_gate: boolean;
  notes?: string | null;
}

export interface Risk {
  id: string;
  scope_type: string;
  scope_id?: string | null;
  category?: string | null;
  description: string;
  likelihood: string;
  impact: string;
  score: number;
  mitigation?: string | null;
  status: string;
}

export interface Forecast {
  id: string;
  launch_id: string;
  currency: string;
  source: string;
  y1_patients?: number | null;
  y2_patients?: number | null;
  y3_patients?: number | null;
  y1_net_price?: number | null;
  y2_net_price?: number | null;
  y3_net_price?: number | null;
  y1_share?: number | null;
  y2_share?: number | null;
  y3_share?: number | null;
  version: number;
  is_current: boolean;
}

export interface KPI {
  id: string;
  launch_id: string;
  category: string;
  name: string;
  unit?: string | null;
  target?: number | null;
  l_minus_30?: number | null;
  l_plus_30?: number | null;
  l_plus_60?: number | null;
  l_plus_90?: number | null;
  l_plus_180?: number | null;
  l_plus_365?: number | null;
  rag?: string | null;
}

export interface OverviewStat {
  on_track_count: number;
  total_launches: number;
  peak_revenue: number;
  peak_revenue_currency: string;
  high_risks_open: number;
  next_milestone?: {
    name: string;
    target_date?: string | null;
    launch_code?: string | null;
    asset_brand?: string | null;
  } | null;
}

export interface MatrixCell {
  launch_id: string;
  launch_code: string;
  rag: "Green" | "Amber" | "Red";
  milestones_complete_pct: number;
}

export interface MatrixRow {
  asset_id: string;
  brand_name: string;
  cells: Record<string, MatrixCell>;
}

export interface PRD {
  id: string;
  launch_id: string;
  current_version: number;
  payload: Record<string, any>;
}

export interface MarketIntel {
  id: string;
  source_id: string;
  country_code?: string | null;
  asset_match?: string | null;
  therapeutic_area?: string | null;
  record_type: string;
  title: string;
  url?: string | null;
  occurred_at?: string | null;
}

export interface DependencyEdge {
  source_type: string;
  source_id: string;
  target_type: string;
  target_id: string;
  link_type: string;
  depth: number;
}
