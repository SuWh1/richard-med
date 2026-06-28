import type {
  AnalyticsOverview,
  AnalyticsParams,
  CabinetDashboard,
  CatalogPage,
  CatalogParams,
  CityInfo,
  ClinicDetail,
  ClinicListPage,
  ClinicListParams,
  ClinicReview,
  ClinicServicesPage,
  ClinicServicesParams,
  CompareInsight,
  CompareResult,
  DoctorProfile,
  DoctorReviewPage,
  MapPin,
  ParseRunDetail,
  ParseRunSummary,
  PriceCard,
  RunTrigger,
  SearchParams,
  SearchResponse,
  SavedServiceWatch,
  ServicePriceStat,
  SearchHistoryItem,
  SourcePublic,
  SourceHealth,
  Suggestion,
  UnmatchedPage,
  UnmatchedParams,
} from "@/types";

import { authHeader } from "./auth-client";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001/api/v1";

// ngrok's free tier serves an HTML interstitial to browser requests; this header
// skips it so fetch() gets JSON, not the warning page. No-op for non-ngrok hosts.
const NGROK_HEADERS: Record<string, string> = BASE_URL.includes("ngrok")
  ? { "ngrok-skip-browser-warning": "true" }
  : {};

async function getJson<T>(path: string, params: Record<string, unknown>): Promise<T> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  }
  // Admin and cabinet endpoints are JWT-protected on the backend.
  const auth =
    path.startsWith("/admin") || path.startsWith("/cabinet") ? authHeader() : {};
  const headers = { ...NGROK_HEADERS, ...auth };
  const response = await fetch(`${BASE_URL}${path}?${query.toString()}`, { headers });
  if (!response.ok) {
    throw new Error(`Запрос не выполнен (${response.status})`);
  }
  return response.json() as Promise<T>;
}

async function sendJson<T>(
  method: "POST" | "PATCH" | "DELETE",
  path: string,
  body?: unknown,
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      "content-type": "application/json",
      ...NGROK_HEADERS,
      ...authHeader(),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`Запрос не выполнен (${response.status})`);
  }
  return (response.status === 204 ? undefined : response.json()) as Promise<T>;
}

export function fetchSuggestions(q: string, category?: string): Promise<Suggestion[]> {
  return getJson<Suggestion[]>("/services", { q, limit: 8, category });
}

export function fetchCities(): Promise<CityInfo[]> {
  return getJson<CityInfo[]>("/search/cities", {});
}

export function fetchSearch(params: SearchParams): Promise<SearchResponse> {
  return getJson<SearchResponse>("/search", { ...params });
}

export function fetchCabinet(): Promise<CabinetDashboard> {
  return getJson<CabinetDashboard>("/cabinet", {});
}

export function saveCabinetService(
  serviceId: number,
  city: string,
  clinicId: number | null = null,
  notifyEnabled = true,
): Promise<SavedServiceWatch> {
  return sendJson("POST", "/cabinet/saved-services", {
    service_id: serviceId,
    clinic_id: clinicId,
    city,
    notify_enabled: notifyEnabled,
  });
}

export function toggleCabinetService(
  watchId: number,
  notifyEnabled: boolean,
): Promise<SavedServiceWatch> {
  return sendJson("PATCH", "/cabinet/saved-services/" + watchId, {
    notify_enabled: notifyEnabled,
  });
}

export function markCabinetServiceSeen(watchId: number): Promise<SavedServiceWatch> {
  return sendJson("POST", `/cabinet/saved-services/${watchId}/mark-seen`);
}

export function deleteCabinetService(watchId: number): Promise<void> {
  return sendJson<void>("DELETE", `/cabinet/saved-services/${watchId}`);
}

export function recordCabinetSearch(params: {
  q: string;
  city: string;
  service_id?: number | null;
  result_count: number;
}): Promise<SearchHistoryItem> {
  return sendJson("POST", "/cabinet/search-history", params);
}

export function fetchFeatured(limit = 6): Promise<PriceCard[]> {
  return getJson<PriceCard[]>("/search/featured", { limit });
}

export function fetchMapPins(
  serviceId: number,
  city?: string,
  bbox?: string,
): Promise<MapPin[]> {
  return getJson<MapPin[]>("/search/map", { service_id: serviceId, city, bbox });
}

export function fetchClinics(params: ClinicListParams = {}): Promise<ClinicListPage> {
  return getJson<ClinicListPage>("/clinics", { ...params });
}

export function fetchClinic(clinicId: number): Promise<ClinicDetail> {
  return getJson<ClinicDetail>(`/clinics/${clinicId}`, {});
}

export function fetchClinicServices(
  clinicId: number,
  params: ClinicServicesParams = {},
): Promise<ClinicServicesPage> {
  return getJson<ClinicServicesPage>(`/clinics/${clinicId}/services`, { ...params });
}

export function fetchClinicReviews(
  clinicId: number,
  limit = 20,
  offset = 0,
): Promise<ClinicReview[]> {
  return getJson<ClinicReview[]>(`/clinics/${clinicId}/reviews`, { limit, offset });
}

export function fetchDoctor(doctorId: number): Promise<DoctorProfile> {
  return getJson<DoctorProfile>(`/doctors/${doctorId}`, {});
}

export function fetchDoctorReviews(
  doctorId: number,
  limit = 20,
  offset = 0,
): Promise<DoctorReviewPage> {
  return getJson<DoctorReviewPage>(`/doctors/${doctorId}/reviews`, { limit, offset });
}

export function fetchCompare(
  serviceId: number,
  clinicIds: number[],
  city?: string | null,
): Promise<CompareResult> {
  return getJson<CompareResult>("/search/compare", {
    service_id: serviceId,
    clinic_ids: clinicIds.join(","),
    city,
  });
}

export function fetchCompareInsight(
  serviceId: number,
  clinicIds: number[],
): Promise<CompareInsight> {
  return getJson<CompareInsight>("/search/compare/insight", {
    service_id: serviceId,
    clinic_ids: clinicIds.join(","),
  });
}

export function fetchSources(): Promise<SourcePublic[]> {
  return getJson<SourcePublic[]>("/sources", {});
}

export function fetchPriceStats(params: AnalyticsParams = {}): Promise<ServicePriceStat[]> {
  return getJson<ServicePriceStat[]>("/analytics/price-stats", { ...params });
}

export function fetchAnalyticsOverview(
  params: Pick<AnalyticsParams, "city" | "include_stale"> = {},
): Promise<AnalyticsOverview> {
  return getJson<AnalyticsOverview>("/analytics/overview", { ...params });
}

export function fetchSourceHealth(): Promise<SourceHealth[]> {
  return getJson<SourceHealth[]>("/admin/source-health", {});
}

export function fetchCatalogServices(params: CatalogParams = {}): Promise<CatalogPage> {
  return getJson<CatalogPage>("/admin/services", { ...params });
}

export function fetchUnmatched(params: UnmatchedParams = {}): Promise<UnmatchedPage> {
  return getJson<UnmatchedPage>("/admin/unmatched", { ...params });
}

export function fetchParseRuns(limit = 20): Promise<ParseRunSummary[]> {
  return getJson<ParseRunSummary[]>("/admin/parse-runs", { limit });
}

export function fetchRunDetail(runId: number): Promise<ParseRunDetail> {
  return getJson<ParseRunDetail>(`/admin/parse-runs/${runId}`, {});
}

export async function triggerRun(source: string | null, city: string): Promise<RunTrigger> {
  const query = new URLSearchParams({ city });
  if (source) query.set("source", source);
  const response = await fetch(`${BASE_URL}/admin/parsers/run?${query.toString()}`, {
    method: "POST",
    headers: { ...NGROK_HEADERS, ...authHeader() },
  });
  if (!response.ok) {
    throw new Error(`Не удалось запустить парсер (${response.status})`);
  }
  return response.json() as Promise<RunTrigger>;
}
