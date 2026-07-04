export interface RiskIndex {
  index_date: string
  gfcri_value: number
  alert_level: string
  si_rates: number
  si_fx: number
  si_equity: number
  si_credit: number
  si_sentiment: number
  sub_index_details: Record<string, any> | null
  active_chains: Record<string, any> | null
  chain_details: Record<string, any> | null
  coherence_multiplier: number | null
  node_contributions: Record<string, any> | null
  divergence?: Record<string, any> | null
  undercurrent_boost?: number | null
  trade_spillover?: Record<string, any> | null
  trade_spillover_boost?: number | null
}

export interface DailyState {
  state_date: string
  graph_version: string
  current_regime: string
  node_values: Record<string, any>
  node_zscores: Record<string, any>
  anomalous_nodes: string[]
  active_paths: Record<string, any> | null
  inference_summary: Record<string, any> | null
  alert_level: string
  alert_details: Record<string, any> | null
}

export interface Report {
  report_date: string
  gfcri_value: number | null
  alert_level: string | null
  report_markdown: string
  report_metadata: Record<string, any> | null
  llm_narrative: string | null
  generation_time_ms: number | null
}

export interface GraphData {
  graph_id: string
  version: string
  node_count: number
  edge_count: number
  nodes: Record<string, any>
  edges: Record<string, any>
}

export interface InferenceResponse {
  inference_type: string
  source: string
  target: string
  result: Record<string, any>
  computation_time_ms: number
}

export interface AlertItem {
  level: string
  title: string
  detail: string
  affected_nodes: string[]
  chain_id: string | null
}

export interface SocialContent {
  date: string
  content: string
  content_type: string
}

export interface SubIndexNodeReceipt {
  node_id: string
  display_name: string
  current_value: number | null
  zscore: number | null
  anomaly_score: number | null
  abs_score: number | null
  source_tier: string
  data_source: string
  raw_formula: string
  known_limitations: string
}

export interface SubIndexReceipt {
  sub_index_id: string
  name: string
  score: number
  formula: string
  mean_stress: number
  mean_abs_stress: number
  transmission: number
  top_driver: string | null
  node_count: number
  source_tier_summary: Record<string, number>
  nodes: SubIndexNodeReceipt[]
  limitations: string[]
  config: Record<string, any> | null
}

export interface ModelFoundation {
  index_date: string
  sub_index_receipts: Record<string, SubIndexReceipt>
  data_dictionary: Record<string, Record<string, any>>
}

export interface InstitutionalRadarSource {
  id: string
  name: string
  tier: string
  url: string
  source_type: string
}

export interface InstitutionalRadarItem {
  id: string
  source: string
  source_id: string
  source_tier: string
  title: string
  summary: string
  url: string
  published_at: string | null
  risk_themes: string[]
  affected_nodes: string[]
  affected_chains: string[]
  risk_direction: string
  confidence: number
}

export interface InstitutionalThemeSummary {
  theme: string
  count: number
  sources: string[]
  affected_nodes: string[]
  affected_chains: string[]
}

export interface InstitutionalRadarError {
  source: string
  error: string
}

export interface InstitutionalRadar {
  generated_at: string
  source_count: number
  item_count: number
  sources: InstitutionalRadarSource[]
  items: InstitutionalRadarItem[]
  theme_summary: InstitutionalThemeSummary[]
  errors: InstitutionalRadarError[]
  methodology: string
}
