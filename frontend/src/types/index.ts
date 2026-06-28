export type Freshness = "fresh" | "recent" | "stale";

export type SortKey = "best_value" | "cheapest" | "newest" | "nearest";

export type City = "Астана" | "Алматы" | "Караганда" | "Актобе";

export type ServiceCategory = "лаборатория" | "приём врача" | "диагностика" | "процедура";

// User-facing categories (the quarantine "прочее" is hidden from search).
export const USER_CATEGORIES: ServiceCategory[] = [
  "лаборатория",
  "приём врача",
  "диагностика",
  "процедура",
];

export interface CityInfo {
  name: string;
  lat: number;
  lng: number;
}

export interface Suggestion {
  id: number;
  name_ru: string;
  category: string;
  specialty: string | null;
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
  doctor_id?: number | null;
  doctor_avatar?: string | null;
  doctor_experience?: number | null;
  doctor_rating?: number | null;
  doctor_reviews?: number | null;
  qualification?: string | null;
  district?: string | null;
  branch_id: number | null;
  city: string | null;
  address: string | null;
  lat: number | null;
  lng: number | null;
  price_kzt: number;
  base_price_kzt?: number | null;
  discount_percent?: number | null;
  duration_min: number | null;
  duration_max: number | null;
  parsed_at: string;
  age_days: number;
  freshness: Freshness;
  source_url: string;
  service_name_raw: string | null;
  source_category: string | null;
  content_hash: string | null;
  match_confidence: number;
  match_method: string | null;
  rating: number | null;
  reviews_count: number | null;
  branch_count: number;
}

export interface DoctorDetailItem {
  detail_type: string;
  detail_type_id: number | null;
  info: string;
  year: string | null;
}

export interface DoctorReview {
  id: number;
  score: number | null;
  text: string | null;
  text_ru: string | null;
  service_name: string | null;
  client_name: string | null;
  waiting_time: number | null;
  clinic_reply: string | null;
  source: string | null;
  created_at: string | null;
}

export interface DoctorReviewPage {
  total: number;
  items: DoctorReview[];
}

export interface DoctorProfile {
  id: number;
  doq_id: number;
  slug: string | null;
  name: string;
  avatar_url: string | null;
  experience_years: number | null;
  rating: number | null;
  review_count: number | null;
  gender: string | null;
  languages: string[] | null;
  photos: string[] | null;
  details: DoctorDetailItem[];
  prices: PriceCard[];
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

export interface BranchInfo {
  id: number;
  city: string | null;
  address: string | null;
  lat: number | null;
  lng: number | null;
  phone: string | null;
  working_hours: string | null;
  rating: number | null;
  reviews_count: number | null;
}

export interface ClinicDetail {
  id: number;
  name: string;
  website_url: string | null;
  source_name: string;
  rating: number | null;
  reviews_count: number;
  branches: BranchInfo[];
}

export interface ClinicReview {
  id: number;
  author: string | null;
  rating: number | null;
  text: string | null;
  official_answer: string | null;
  review_date: string | null;
  source: string;
  branch_id: number;
  city: string | null;
}

export interface ClinicServiceRow {
  service_id: number;
  service_name: string;
  category: string;
  price_kzt: number;
  parsed_at: string;
  age_days: number;
  freshness: Freshness;
  source_url: string;
  city: string | null;
  branch_id: number | null;
}

export interface CompareRow {
  clinic_id: number;
  clinic_name: string;
  branch_id: number | null;
  city: string | null;
  address: string | null;
  price_kzt: number;
  duration_min: number | null;
  duration_max: number | null;
  parsed_at: string;
  age_days: number;
  freshness: Freshness;
  source_url: string;
  is_cheapest: boolean;
  price_delta: number;
  delta_pct: number;
  price_rank: number;
}

export interface CompareResult {
  service_id: number;
  service_name: string;
  rows: CompareRow[];
}

export interface ClinicInsight {
  clinic_id: number;
  clinic_name: string;
  rating: number | null;
  reviews_count: number | null;
  summary: string;
}

export interface CompareInsight {
  available: boolean;
  service_name: string;
  clinics: ClinicInsight[];
  verdict: string | null;
  best_clinic_id: number | null;
  reason: string | null;
}

export interface SearchParams {
  q: string;
  city?: string;
  category?: string;
  sort?: SortKey;
  include_stale?: boolean;
  price_min?: number;
  price_max?: number;
  lat?: number;
  lng?: number;
}

export interface SavedServiceWatch {
  id: number;
  service_id: number;
  service_name: string;
  category: string;
  clinic_id: number | null;
  clinic_name: string | null;
  city: string;
  notify_enabled: boolean;
  baseline_min_price: number | null;
  last_seen_min_price: number | null;
  current_min_price: number | null;
  clinic_count: number;
  updated_at: string;
}

export interface SearchHistoryItem {
  id: number;
  q: string;
  city: string;
  service_id: number | null;
  service_name: string | null;
  result_count: number;
  created_at: string;
}

export interface PriceNotification {
  watch_id: number;
  service_id: number;
  service_name: string;
  city: string;
  previous_min_price: number;
  current_min_price: number;
  delta_kzt: number;
  delta_pct: number;
}

export interface CabinetDashboard {
  saved_services: SavedServiceWatch[];
  recent_searches: SearchHistoryItem[];
  notifications: PriceNotification[];
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

export interface CatalogServiceRow {
  id: number;
  name_ru: string;
  category: string;
  origin: "catalog" | "auto";
  alias_count: number;
  price_count: number;
}

export interface CatalogPage {
  total: number;
  items: CatalogServiceRow[];
}

export interface CatalogParams {
  q?: string;
  category?: string;
  limit?: number;
  offset?: number;
}

export interface UnmatchedRow {
  id: number;
  raw_name: string;
  suggested_name: string | null;
  suggested_category: string | null;
  confidence: number;
  status: string;
}

export interface UnmatchedPage {
  total: number;
  items: UnmatchedRow[];
}

export interface UnmatchedParams {
  status?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface SourcePublic {
  name: string;
  display_name: string;
  kind: string;
  description: string;
  website: string;
  clinics: number;
  prices: number;
  cities: number;
  last_parsed_at: string | null;
  freshness: Freshness | null;
}

export interface ClinicSummary {
  id: number;
  name: string;
  source_name: string;
  website_url: string | null;
  rating: number | null;
  reviews_count: number;
  branches_count: number;
  active_services_count: number;
  cities: string[];
}

export interface ClinicListPage {
  total: number;
  items: ClinicSummary[];
}

export interface ClinicListParams {
  q?: string;
  city?: string;
  source?: string;
  sort?: "name" | "rating" | "services";
  limit?: number;
  offset?: number;
}

export interface ClinicServicesPage {
  total: number;
  items: ClinicServiceRow[];
}

export interface ClinicServicesParams {
  q?: string;
  category?: string;
  include_stale?: boolean;
  limit?: number;
  offset?: number;
}
