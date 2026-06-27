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
  content_hash: "abc",
  match_confidence: 0.94,
  match_method: "alias",
};

function renderCard(overrides: Partial<Parameters<typeof ClinicCard>[0]> = {}) {
  return render(
    <ClinicCard
      card={card}
      isCheapest={false}
      isHighlighted={false}
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
        onHover={() => {}}
        onPassport={() => {}}
      />,
    );
    expect(screen.queryByText("Лучшая цена")).not.toBeInTheDocument();
  });

  it("should call onPassport when the source button is clicked", async () => {
    const onPassport = vi.fn();
    renderCard({ onPassport });
    await userEvent.click(screen.getByRole("button", { name: "Источник цены" }));
    expect(onPassport).toHaveBeenCalledOnce();
  });
});
