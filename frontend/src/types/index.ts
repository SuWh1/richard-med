export type Freshness = "fresh" | "recent" | "stale";

export type SortKey = "best_value" | "cheapest" | "newest";

export interface Suggestion {
  id: number;
  name_ru: string;
  category: string;
  score: number;
  has_prices: boolean;
}

export interface PriceCard {
  price_id: number;
  service_id: number;
  service_name: string;
  clinic_id: number;
  clinic_name: string;
  branch_id: number | null;
  city: string | null;
  address: string | null;
  lat: number | null;
  lng: number | null;
  price_kzt: number;
  duration_min: number | null;
  duration_max: number | null;
  parsed_at: string;
  age_days: number;
  freshness: Freshness;
  source_url: string;
  service_name_raw: string | null;
  content_hash: string | null;
  match_confidence: number;
  match_method: string | null;
}

export interface SearchResponse {
  query: string;
  resolved_service: Suggestion | null;
  suggestions: Suggestion[];
  cards: PriceCard[];
  count: number;
}

export interface SearchParams {
  q: string;
  city?: string;
  sort?: SortKey;
  include_stale?: boolean;
  price_min?: number;
  price_max?: number;
}

export type RunStatus = "running" | "success" | "partial" | "failed";

export interface SourceHealth {
  source_name: string;
  last_run_at: string | null;
  last_success_at: string | null;
  last_status: RunStatus | null;
  success_rate_7d: number;
  runs_7d: number;
  items_found_last: number;
  items_saved_last: number;
  active_prices: number;
  stale_prices: number;
  last_error: string | null;
}

export interface ParseRunSummary {
  id: number;
  source_name: string;
  city: string | null;
  status: RunStatus;
  started_at: string;
  finished_at: string | null;
  duration_sec: number | null;
  items_found: number;
  items_saved: number;
  has_errors: boolean;
}

export interface ParsedPriceSample {
  service_name: string;
  service_name_raw: string | null;
  clinic_name: string;
  city: string | null;
  price_kzt: number;
  match_confidence: number;
  match_method: string | null;
  age_days: number;
  freshness: Freshness;
  source_url: string;
}

export interface ParseRunDetail {
  run: ParseRunSummary;
  errors: string[];
  unmatched_count: number;
  unmatched_samples: string[];
  price_samples: ParsedPriceSample[];
}

export interface RunTrigger {
  accepted: boolean;
  source_names: string[];
  city: string;
  message: string;
}
