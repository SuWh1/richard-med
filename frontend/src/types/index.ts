export type Freshness = "fresh" | "recent" | "stale";

export type SortKey = "best_value" | "cheapest" | "newest";

export type City = "Астана" | "Алматы" | "Караганда" | "Актобе";

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
  doctor_name: string | null;
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

export interface MapPin {
  price_id: number;
  clinic_id: number;
  clinic_name: string;
  branch_id: number;
  city: string | null;
  address: string | null;
  lat: number;
  lng: number;
  price_kzt: number;
  parsed_at: string;
  age_days: number;
  freshness: Freshness;
  source_url: string;
  is_cheapest: boolean;
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

export interface ServicePriceStat {
  service_id: number;
  service_name: string;
  category: string;
  city: string | null;
  clinic_count: number;
  price_count: number;
  min_kzt: number;
  max_kzt: number;
  avg_kzt: number;
  median_kzt: number;
  spread_pct: number;
  freshest_parsed_at: string;
}

export interface CategoryStat {
  category: string;
  service_count: number;
  price_count: number;
  min_kzt: number;
  max_kzt: number;
  median_kzt: number;
}

export interface CityCoverage {
  city: string;
  price_count: number;
  service_count: number;
}

export interface AnalyticsOverview {
  city: string | null;
  total_prices: number;
  total_services: number;
  categories: CategoryStat[];
  cities: CityCoverage[];
}

export interface AnalyticsParams {
  city?: string;
  category?: string;
  include_stale?: boolean;
  limit?: number;
}
