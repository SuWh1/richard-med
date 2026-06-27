import { type ReactNode } from "react";

import type { SearchState } from "@/hooks/useSearchState";
import { DEFAULT_CITY } from "@/hooks/useSearchState";
import type { SortKey } from "@/types";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { FiltersSheet } from "./FiltersSheet";

const SORT_LABELS: { key: SortKey; label: string }[] = [
  { key: "best_value", label: "Оптимальные" },
  { key: "cheapest", label: "Сначала дешёвые" },
];

function clinicWord(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return "клиника";
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return "клиники";
  return "клиник";
}

interface ResultsControlsBarProps {
  searchBar: ReactNode;
  state: SearchState;
  cities: string[];
  onPatch: (patch: Partial<SearchState>) => void;
  onReset: () => void;
  count: number;
}

export function ResultsControlsBar({
  searchBar,
  state,
  cities,
  onPatch,
  onReset,
  count,
}: ResultsControlsBarProps) {
  const activeFilters =
    (state.city !== DEFAULT_CITY ? 1 : 0) +
    (state.priceMin || state.priceMax ? 1 : 0) +
    (state.includeStale ? 1 : 0);

  return (
    <div className="sticky top-0 z-40 border-b border-border bg-inset">
      <div className="mx-auto w-full max-w-[1400px] px-4 py-2.5">
        <div className="min-w-0">{searchBar}</div>

        <div className="mt-2 flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
          <span className="shrink-0 text-sm text-muted-foreground">
            <span className="font-semibold text-foreground">{count}</span>{" "}
            {clinicWord(count)}
          </span>

          <div className="flex shrink-0 items-center gap-2">
            <Select
              value={state.sort}
              onValueChange={(v) => onPatch({ sort: v as SortKey })}
            >
              <SelectTrigger size="sm" className="w-auto gap-1.5">
                <SelectValue />
              </SelectTrigger>
              <SelectContent align="end">
                {SORT_LABELS.map((opt) => (
                  <SelectItem key={opt.key} value={opt.key}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
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
    </div>
  );
}
