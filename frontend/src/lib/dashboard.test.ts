import { describe, expect, it } from "vitest";

import type { SourceHealth } from "@/types";
import { summarizeHealth } from "./dashboard";

function health(overrides: Partial<SourceHealth>): SourceHealth {
  return {
    source_name: "kdl_olymp",
    last_run_at: null,
    last_success_at: null,
    last_status: "success",
    success_rate_7d: 1,
    runs_7d: 1,
    items_found_last: 0,
    items_saved_last: 0,
    active_prices: 0,
    stale_prices: 0,
    last_error: null,
    ...overrides,
  };
}

describe("summarizeHealth", () => {
  it("should count sources and sum active prices", () => {
    const kpis = summarizeHealth([
      health({ source_name: "a", active_prices: 100, stale_prices: 10 }),
      health({ source_name: "b", active_prices: 50, stale_prices: 5 }),
    ]);
    expect(kpis.sources).toBe(2);
    expect(kpis.activePrices).toBe(150);
    expect(kpis.stalePrices).toBe(15);
    expect(kpis.freshPrices).toBe(135);
  });

  it("should count only failed sources as errors", () => {
    const kpis = summarizeHealth([
      health({ source_name: "a", last_status: "success" }),
      health({ source_name: "b", last_status: "failed" }),
      health({ source_name: "c", last_status: "partial" }),
    ]);
    expect(kpis.errorSources).toBe(1);
  });

  it("should return zeros for an empty list", () => {
    const kpis = summarizeHealth([]);
    expect(kpis).toEqual({
      sources: 0,
      activePrices: 0,
      freshPrices: 0,
      stalePrices: 0,
      errorSources: 0,
    });
  });
});
