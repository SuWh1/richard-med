import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { PriceCard as PriceCardData } from "@/types";
import { ClinicCard } from "./ClinicCard";

const card: PriceCardData = {
  price_id: 1,
  service_id: 10,
  service_name: "Общий анализ крови (ОАК)",
  clinic_id: 5,
  clinic_name: "KDL Olymp",
  doctor_name: null,
  branch_id: 2,
  city: "Астана",
  address: "Тұран 43/3",
  lat: 51.1,
  lng: 71.4,
  price_kzt: 1880,
  duration_min: 1,
  duration_max: 1,
  parsed_at: "2026-06-27T08:00:00Z",
  age_days: 0,
  freshness: "fresh",
  source_url: "https://kdlolymp.kz/pricelist/astana",
  service_name_raw: "ОАК без СОЭ",
  source_category: "Гематология",
  content_hash: "abc",
  match_confidence: 0.94,
  match_method: "alias",
  rating: 4.9,
  reviews_count: 155,
  branch_count: 1,
};

function renderCard(overrides: Partial<Parameters<typeof ClinicCard>[0]> = {}) {
  return render(
    <ClinicCard
      card={card}
      isCheapest={false}
      isHighlighted={false}
      median={null}
      onHover={() => {}}
      onPassport={() => {}}
      {...overrides}
    />,
  );
}

describe("ClinicCard", () => {
  it("should render the clinic name and formatted price", () => {
    renderCard();
    expect(screen.getByText("KDL Olymp")).toBeInTheDocument();
    expect(screen.getByText(/1\s880 ₸/)).toBeInTheDocument();
  });

  it("should show the best-price badge only when cheapest", () => {
    const { rerender } = renderCard({ isCheapest: true });
    expect(screen.getByText("Лучшая цена")).toBeInTheDocument();
    rerender(
      <ClinicCard
        card={card}
        isCheapest={false}
        isHighlighted={false}
        median={null}
        onHover={() => {}}
        onPassport={() => {}}
      />,
    );
    expect(screen.queryByText("Лучшая цена")).not.toBeInTheDocument();
  });

  it("should show a below-median badge when cheaper than the median", () => {
    renderCard({ median: 2700 });
    expect(screen.getByText(/% ниже среднего/)).toBeInTheDocument();
  });

  it("should not show a below-median badge when at or above the median", () => {
    renderCard({ median: 1880 });
    expect(screen.queryByText(/ниже среднего/)).not.toBeInTheDocument();
  });

  it("should call onPassport when the source button is clicked", async () => {
    const onPassport = vi.fn();
    renderCard({ onPassport });
    await userEvent.click(screen.getByRole("button", { name: "Источник цены" }));
    expect(onPassport).toHaveBeenCalledOnce();
  });

  it("should render a freshness badge", () => {
    renderCard();
    expect(screen.getByText("Обновлено сегодня")).toBeInTheDocument();
  });

  it("should not render the service duration chip", () => {
    renderCard();
    expect(screen.queryByText(/дн\.$/)).not.toBeInTheDocument();
  });

  it("should render the 2GIS rating when present", () => {
    renderCard();
    expect(screen.getByLabelText(/Рейтинг 2ГИС 4\.9/)).toBeInTheDocument();
    expect(screen.getByText(/155/)).toBeInTheDocument();
  });

  it("should not render a rating when the card has none", () => {
    renderCard({ card: { ...card, rating: null, reviews_count: null } });
    expect(screen.queryByLabelText(/Рейтинг 2ГИС/)).not.toBeInTheDocument();
  });

  it("should show a points-in-city badge for multi-branch clinics", () => {
    renderCard({ card: { ...card, branch_count: 78 } });
    expect(screen.getByText(/78 точек в городе/)).toBeInTheDocument();
  });

  it("should not show a points badge for a single-branch clinic", () => {
    renderCard({ card: { ...card, branch_count: 1 } });
    expect(screen.queryByText(/точ.* в городе/)).not.toBeInTheDocument();
  });

  it("should expand the points list and zoom on hover", async () => {
    const onPointHover = vi.fn();
    const points = [
      { branchId: 11, address: "ул. Первая, 1", lat: 43.2, lng: 76.9, distanceKm: 0.5 },
      { branchId: 12, address: "ул. Вторая, 2", lat: 43.3, lng: 76.95, distanceKm: 2.1 },
    ];
    renderCard({ card: { ...card, branch_count: 2 }, points, onPointHover });

    await userEvent.click(screen.getByText(/2 точки в городе/));
    const row = screen.getByText("ул. Вторая, 2");
    await userEvent.hover(row);

    expect(onPointHover).toHaveBeenCalledWith(12);
  });

  it("should not render a compare button when onCompare is absent", () => {
    renderCard();
    expect(screen.queryByText(/Сравнить|В сравнении/)).not.toBeInTheDocument();
  });

  it("should call onCompare when the compare button is clicked", async () => {
    const onCompare = vi.fn();
    renderCard({ onCompare });
    await userEvent.click(screen.getByRole("button", { name: /Сравнить/ }));
    expect(onCompare).toHaveBeenCalledOnce();
  });

  it("should show the selected label when inCompare is true", () => {
    renderCard({ onCompare: () => {}, inCompare: true });
    expect(screen.getByText("В сравнении")).toBeInTheDocument();
  });

  it("should build a 2GIS directions link from the card coordinates", () => {
    renderCard();
    const route = screen.getByRole("link", { name: /Маршрут/ });
    expect(route).toHaveAttribute(
      "href",
      "https://2gis.kz/astana/directions/points/|71.4,51.1?m=71.4,51.1/16",
    );
  });

  it("should include the user origin in the 2GIS route when known", () => {
    renderCard({ userCoords: { lat: 51.2, lng: 71.5 } });
    const route = screen.getByRole("link", { name: /Маршрут/ });
    expect(route).toHaveAttribute(
      "href",
      "https://2gis.kz/astana/directions/points/71.5,51.2|71.4,51.1",
    );
  });

  it("should render a distance chip when distanceKm is provided", () => {
    renderCard({ distanceKm: 2.4 });
    expect(screen.getByText("2.4 км")).toBeInTheDocument();
  });

  it("should not render a distance chip when distanceKm is null", () => {
    renderCard({ distanceKm: null });
    expect(screen.queryByText(/км$/)).not.toBeInTheDocument();
  });
});
