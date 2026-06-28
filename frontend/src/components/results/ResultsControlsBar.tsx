import { type ReactNode } from "react";
import { Building2 } from "lucide-react";

import type { SearchState } from "@/hooks/useSearchState";
import { DEFAULT_CITY } from "@/hooks/useSearchState";
import { pointWord } from "@/lib/rating";
import { FiltersSheet } from "./FiltersSheet";

function clinicWord(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return "клиника";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return "клиники";
  return "клиник";
}

interface ResultsControlsBarProps {
  searchBar: ReactNode;
  action?: ReactNode;
  state: SearchState;
  cities: string[];
  onPatch: (patch: Partial<SearchState>) => void;
  onReset: () => void;
  count: number;
  pointsCount?: number;
}

export function ResultsControlsBar({
  searchBar,
  action,
  state,
  cities,
  onPatch,
  onReset,
  count,
  pointsCount = 0,
}: ResultsControlsBarProps) {
  const activeFilters =
    (state.city !== DEFAULT_CITY ? 1 : 0) +
    (state.sort !== "best_value" ? 1 : 0) +
    (state.priceMin || state.priceMax ? 1 : 0) +
    (state.includeStale ? 1 : 0);

  return (
    <div className="sticky top-0 z-40 border-b border-border bg-inset">
      <div className="mx-auto w-full max-w-[1400px] px-4 py-2.5">
        <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-center">
          <div className="min-w-0 flex-1">{searchBar}</div>
          {action && <div className="shrink-0">{action}</div>}
        </div>

        <div className="mt-2 flex items-center justify-between gap-2">
          <span className="flex min-w-0 items-center gap-2 truncate text-sm text-muted-foreground">
            <span>
              <span className="font-semibold text-foreground">{count}</span>{" "}
              {clinicWord(count)}
            </span>
            {pointsCount > count && (
              <span className="flex items-center gap-1 rounded-full bg-secondary px-2 py-0.5 text-[11px] text-muted-foreground">
                <Building2 className="h-3 w-3" />
                <span className="font-medium text-foreground">{pointsCount}</span>{" "}
                {pointWord(pointsCount)}
              </span>
            )}
          </span>

          <FiltersSheet
            state={state}
            cities={cities}
            onPatch={onPatch}
            onReset={onReset}
            activeCount={activeFilters}
          />
        </div>
      </div>
    </div>
  );
}
