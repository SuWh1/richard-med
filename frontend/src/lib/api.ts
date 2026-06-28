import type {
  AnalyticsOverview,
  AnalyticsParams,
  CatalogPage,
  CatalogParams,
  CityInfo,
  ClinicDetail,
  ClinicServiceRow,
  CompareResult,
  MapPin,
  ParseRunDetail,
  ParseRunSummary,
  PriceCard,
  RunTrigger,
  SearchParams,
  SearchResponse,
  ServicePriceStat,
  SourceHealth,
  Suggestion,
  UnmatchedPage,
  UnmatchedParams,
} from "@/types";

import { authHeader } from "./auth-client";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001/api/v1";

async function getJson<T>(path: string, params: Record<string, unknown>): Promise<T> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, String(value));
    }
  }
  // Admin endpoints are JWT-protected on the backend.
  const headers = path.startsWith("/admin") ? await authHeader() : undefined;
  const response = await fetch(`${BASE_URL}${path}?${query.toString()}`, { headers });
  if (!response.ok) {
    throw new Error(`Запрос не выполнен (${response.status})`);
  }
  return response.json() as Promise<T>;
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

export function fetchClinic(clinicId: number): Promise<ClinicDetail> {
  return getJson<ClinicDetail>(`/clinics/${clinicId}`, {});
}

export function fetchClinicServices(clinicId: number): Promise<ClinicServiceRow[]> {
  return getJson<ClinicServiceRow[]>(`/clinics/${clinicId}/services`, {});
}

export function fetchCompare(
  serviceId: number,
  clinicIds: number[],
): Promise<CompareResult> {
  return getJson<CompareResult>("/search/compare", {
    service_id: serviceId,
    clinic_ids: clinicIds.join(","),
  });
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
    headers: await authHeader(),
  });
  if (!response.ok) {
    throw new Error(`Не удалось запустить парсер (${response.status})`);
  }
  return response.json() as Promise<RunTrigger>;
}
