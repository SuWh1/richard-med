import type { SourceHealth } from "@/types";

export interface DashboardKpis {
  sources: number;
  activePrices: number;
  freshPrices: number;
  stalePrices: number;
  errorSources: number;
}

export function summarizeHealth(health: SourceHealth[]): DashboardKpis {
  const activePrices = health.reduce((sum, h) => sum + h.active_prices, 0);
  const stalePrices = health.reduce((sum, h) => sum + h.stale_prices, 0);
  return {
    sources: health.length,
    activePrices,
    stalePrices,
    freshPrices: activePrices - stalePrices,
    errorSources: health.filter((h) => h.last_status === "failed").length,
  };
}
