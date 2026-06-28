import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { CabinetDashboard } from "@/types";
import {
  deleteCabinetService,
  fetchCabinet,
  markCabinetServiceSeen,
  toggleCabinetService,
} from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { CabinetPage } from "./CabinetPage";

vi.mock("@/components/AppShell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));
vi.mock("@/lib/useAuth", () => ({ useAuth: vi.fn() }));
vi.mock("@/lib/api", () => ({
  deleteCabinetService: vi.fn(),
  fetchCabinet: vi.fn(),
  markCabinetServiceSeen: vi.fn(),
  toggleCabinetService: vi.fn(),
}));

const dashboard: CabinetDashboard = {
  saved_services: [
    {
      id: 7,
      service_id: 10,
      service_name: "Общий анализ крови",
      category: "лаборатория",
      clinic_id: null,
      clinic_name: null,
      city: "Астана",
      notify_enabled: true,
      baseline_min_price: 5000,
      last_seen_min_price: 5000,
      current_min_price: 4500,
      clinic_count: 3,
      updated_at: "2026-06-28T09:00:00Z",
    },
  ],
  recent_searches: [
    {
      id: 4,
      q: "ОАК",
      city: "Астана",
      service_id: 10,
      service_name: "Общий анализ крови",
      result_count: 3,
      created_at: "2026-06-28T09:05:00Z",
    },
  ],
  notifications: [
    {
      watch_id: 7,
      service_id: 10,
      service_name: "Общий анализ крови",
      city: "Астана",
      previous_min_price: 5000,
      current_min_price: 4500,
      delta_kzt: -500,
      delta_pct: -10,
    },
  ],
};

function renderPage(data: CabinetDashboard = dashboard) {
  vi.mocked(useAuth).mockReturnValue({
    user: { id: 1, email: "user@test.dev", name: "Dauren", role: "user" },
    isPending: false,
    isAuthenticated: true,
    isAdmin: false,
  });
  vi.mocked(fetchCabinet).mockResolvedValue(data);
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <CabinetPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CabinetPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(deleteCabinetService).mockResolvedValue(undefined);
    vi.mocked(markCabinetServiceSeen).mockResolvedValue(dashboard.saved_services[0]);
    vi.mocked(toggleCabinetService).mockResolvedValue(dashboard.saved_services[0]);
  });

  it("should render saved services, notifications and search history", async () => {
    renderPage();

    expect(await screen.findAllByText("Общий анализ крови")).toHaveLength(3);
    expect(screen.getAllByText(/5\s000 ₸/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/4\s500 ₸/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/3\s*клиник/).length).toBeGreaterThan(0);
  });

  it("should show empty states when the user has no cabinet activity", async () => {
    renderPage({ saved_services: [], recent_searches: [], notifications: [] });

    expect(await screen.findByText(/Найдите услугу и нажмите/)).toBeInTheDocument();
    expect(screen.getByText(/Здесь появятся ваши последние запросы/)).toBeInTheDocument();
    expect(screen.getByText(/Сохраняйте услуги из поиска/)).toBeInTheDocument();
  });

  it("should link saved services and history back to search", async () => {
    renderPage();

    const links = await screen.findAllByRole("link", { name: "Общий анализ крови" });
    expect(links[0]).toHaveAttribute(
      "href",
      "/search?q=%D0%9E%D0%B1%D1%89%D0%B8%D0%B9+%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7+%D0%BA%D1%80%D0%BE%D0%B2%D0%B8",
    );
  });

  it("should call cabinet mutations from dashboard actions", async () => {
    renderPage();

    await userEvent.click(await screen.findByRole("button", { name: "Удалить сохранённую услугу" }));
    expect(deleteCabinetService).toHaveBeenCalledWith(7);

    await userEvent.click(screen.getByRole("button", { name: "Отключить уведомления" }));
    expect(toggleCabinetService).toHaveBeenCalledWith(7, false);

    await userEvent.click(screen.getByRole("button", { name: "Отметить просмотренным" }));
    await waitFor(() => expect(markCabinetServiceSeen).toHaveBeenCalledWith(7));
  });
});
