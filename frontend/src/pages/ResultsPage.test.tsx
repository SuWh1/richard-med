import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { CabinetDashboard, SearchResponse } from "@/types";
import {
  deleteCabinetService,
  fetchCabinet,
  fetchCities,
  fetchMapPins,
  fetchSearch,
  fetchSuggestions,
  recordCabinetSearch,
  saveCabinetService,
} from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useUserLocation } from "@/hooks/useUserLocation";
import { ResultsPage } from "./ResultsPage";

vi.mock("@/components/AppShell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/components/map/ClinicMap", () => ({
  ClinicMap: () => <div data-testid="map" />,
}));
vi.mock("@/lib/useAuth", () => ({ useAuth: vi.fn() }));
vi.mock("@/hooks/useUserLocation", () => ({ useUserLocation: vi.fn() }));
vi.mock("@/lib/api", () => ({
  deleteCabinetService: vi.fn(),
  fetchCabinet: vi.fn(),
  fetchCities: vi.fn(),
  fetchMapPins: vi.fn(),
  fetchSearch: vi.fn(),
  fetchSuggestions: vi.fn(),
  recordCabinetSearch: vi.fn(),
  saveCabinetService: vi.fn(),
}));

const resolved = {
  id: 10,
  name_ru: "Общий анализ крови",
  category: "лаборатория",
  clinic_id: null,
  clinic_name: null,
  specialty: null,
  score: 1,
  has_prices: true,
};

const card = {
  price_id: 1,
  service_id: 10,
  service_name: "Общий анализ крови",
  source_category: null,
  clinic_id: 5,
  clinic_name: "KDL Olymp",
  doctor_name: null,
  branch_id: 2,
  city: "Астана",
  address: "ул. Тест",
  lat: 51.1,
  lng: 71.4,
  price_kzt: 1880,
  duration_min: null,
  duration_max: null,
  parsed_at: "2026-06-28T08:00:00Z",
  age_days: 0,
  freshness: "fresh" as const,
  source_url: "https://example.kz",
  service_name_raw: null,
  content_hash: null,
  match_confidence: 1,
  match_method: "exact",
  rating: null,
  reviews_count: null,
  branch_count: 1,
};

const searchResponse: SearchResponse = {
  query: "ОАК",
  resolved_service: resolved,
  suggestions: [],
  cards: [card],
  count: 2,
};

const emptyCabinet: CabinetDashboard = {
  saved_services: [],
  recent_searches: [],
  notifications: [],
};

function renderResults(cabinet: CabinetDashboard = emptyCabinet) {
  vi.mocked(useAuth).mockReturnValue({
    user: { id: 1, email: "user@test.dev", name: null, role: "user" },
    isPending: false,
    isAuthenticated: true,
    isAdmin: false,
  });
  vi.mocked(useUserLocation).mockReturnValue({
    coords: null,
    status: "idle",
    permission: null,
    request: vi.fn(),
    requestOnce: vi.fn(),
  });
  vi.mocked(fetchCities).mockResolvedValue([{ name: "Астана", lat: 51.16, lng: 71.47 }]);
  vi.mocked(fetchSuggestions).mockResolvedValue([]);
  vi.mocked(fetchSearch).mockResolvedValue(searchResponse);
  vi.mocked(fetchMapPins).mockResolvedValue([]);
  vi.mocked(fetchCabinet).mockResolvedValue(cabinet);
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/search?q=%D0%9E%D0%90%D0%9A"]}>
        <Routes>
          <Route path="/search" element={<ResultsPage />} />
          <Route path="/login" element={<div>LOGIN</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("ResultsPage cabinet actions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(deleteCabinetService).mockResolvedValue(undefined);
    vi.mocked(recordCabinetSearch).mockResolvedValue({
      id: 1,
      q: "ОАК",
      city: "Астана",
      service_id: 10,
      service_name: "Общий анализ крови",
      result_count: 2,
      created_at: "2026-06-28T09:00:00Z",
    });
    vi.mocked(saveCabinetService).mockResolvedValue({
      id: 7,
      service_id: 10,
      service_name: "Общий анализ крови",
      category: "лаборатория",
      clinic_id: null,
      clinic_name: null,
      city: "Астана",
      notify_enabled: true,
      baseline_min_price: 1880,
      last_seen_min_price: 1880,
      current_min_price: 1880,
      clinic_count: 2,
      updated_at: "2026-06-28T09:00:00Z",
    });
  });

  it("should save the resolved service and record search history", async () => {
    renderResults();

    await waitFor(() =>
      expect(recordCabinetSearch).toHaveBeenCalledWith({
        q: "ОАК",
        city: "Астана",
        service_id: 10,
        result_count: 2,
      }),
    );
    await userEvent.click(await screen.findByTitle("Сохранить клинику"));

    expect(saveCabinetService).toHaveBeenCalledWith(10, "Астана", 5);
  });

  it("should remove an already saved clinic offer", async () => {
    renderResults({
      ...emptyCabinet,
      saved_services: [
        {
          id: 7,
          service_id: 10,
          service_name: "Общий анализ крови",
          category: "лаборатория",
          clinic_id: 5,
          clinic_name: "KDL Olymp",
          city: "Астана",
          notify_enabled: true,
          baseline_min_price: 1880,
          last_seen_min_price: 1880,
          current_min_price: 1880,
          clinic_count: 2,
          updated_at: "2026-06-28T09:00:00Z",
        },
      ],
    });

    await userEvent.click(await screen.findByTitle("В избранном"));

    expect(deleteCabinetService).toHaveBeenCalledWith(7);
  });
});
