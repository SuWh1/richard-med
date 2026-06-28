import { describe, expect, it } from "vitest";

import type { CompareRow } from "@/types";
import { ADVANTAGE, compareInsights } from "./compareInsights";

function row(over: Partial<CompareRow> & { clinic_id: number; price_kzt: number }): CompareRow {
  return {
    clinic_name: `Клиника ${over.clinic_id}`,
    branch_id: null,
    city: "Астана",
    address: null,
    duration_min: null,
    duration_max: null,
    parsed_at: "2026-06-28T00:00:00Z",
    age_days: 1,
    freshness: "fresh",
    source_url: "https://x.kz",
    is_cheapest: false,
    price_delta: 0,
    delta_pct: 0,
    price_rank: 1,
    ...over,
  };
}

describe("compareInsights", () => {
  it("should tag only the cheapest clinic with the low-price advantage", () => {
    const insights = compareInsights([
      row({ clinic_id: 1, price_kzt: 2000 }),
      row({ clinic_id: 2, price_kzt: 6600 }),
    ]);
    expect(insights[1]).toContain(ADVANTAGE.price);
    expect(insights[2]).not.toContain(ADVANTAGE.price);
  });

  it("should tag the freshest clinic when ages differ", () => {
    const insights = compareInsights([
      row({ clinic_id: 1, price_kzt: 2000, age_days: 10 }),
      row({ clinic_id: 2, price_kzt: 2500, age_days: 1 }),
    ]);
    expect(insights[2]).toContain(ADVANTAGE.fresh);
    expect(insights[1]).not.toContain(ADVANTAGE.fresh);
  });

  it("should tag the fastest clinic when durations differ", () => {
    const insights = compareInsights([
      row({ clinic_id: 1, price_kzt: 2000, duration_max: 3 }),
      row({ clinic_id: 2, price_kzt: 2500, duration_max: 1 }),
    ]);
    expect(insights[2]).toContain(ADVANTAGE.fast);
    expect(insights[1]).not.toContain(ADVANTAGE.fast);
  });

  it("should not tag speed when no clinic has a duration", () => {
    const insights = compareInsights([
      row({ clinic_id: 1, price_kzt: 2000 }),
      row({ clinic_id: 2, price_kzt: 2500 }),
    ]);
    expect(insights[1]).not.toContain(ADVANTAGE.fast);
    expect(insights[2]).not.toContain(ADVANTAGE.fast);
  });

  it("should not tag a winner when all values are equal", () => {
    const insights = compareInsights([
      row({ clinic_id: 1, price_kzt: 2000, age_days: 2 }),
      row({ clinic_id: 2, price_kzt: 2000, age_days: 2 }),
    ]);
    expect(insights[1]).toEqual([]);
    expect(insights[2]).toEqual([]);
  });

  it("should return an empty advantage list for a single clinic", () => {
    const insights = compareInsights([row({ clinic_id: 1, price_kzt: 2000 })]);
    expect(insights[1]).toEqual([]);
  });
});
