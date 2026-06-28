import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

import type { SortKey } from "@/types";

export interface SearchState {
  q: string;
  city: string;
  sort: SortKey;
  priceMin: string;
  priceMax: string;
  includeStale: boolean;
}

export const DEFAULT_CITY = "Астана";
const DEFAULT_SORT: SortKey = "best_value";
const SORTS: SortKey[] = ["best_value", "cheapest", "newest", "nearest"];

export function parseSearchState(params: URLSearchParams): SearchState {
  const sortParam = params.get("sort");
  return {
    q: params.get("q") ?? "",
    city: params.get("city") ?? DEFAULT_CITY,
    sort: sortParam && SORTS.includes(sortParam as SortKey) ? (sortParam as SortKey) : DEFAULT_SORT,
    priceMin: params.get("price_min") ?? "",
    priceMax: params.get("price_max") ?? "",
    includeStale: params.get("stale") === "1",
  };
}

export function buildSearchParams(state: SearchState): URLSearchParams {
  const sp = new URLSearchParams();
  if (state.q) sp.set("q", state.q);
  if (state.city && state.city !== DEFAULT_CITY) sp.set("city", state.city);
  if (state.sort !== DEFAULT_SORT) sp.set("sort", state.sort);
  if (state.priceMin) sp.set("price_min", state.priceMin);
  if (state.priceMax) sp.set("price_max", state.priceMax);
  if (state.includeStale) sp.set("stale", "1");
  return sp;
}

export function searchHref(state: Partial<SearchState> & { q: string }): string {
  const full: SearchState = {
    city: DEFAULT_CITY,
    sort: DEFAULT_SORT,
    priceMin: "",
    priceMax: "",
    includeStale: false,
    ...state,
  };
  const sp = buildSearchParams(full);
  return `/search?${sp.toString()}`;
}

export function useSearchState() {
  const [params, setParams] = useSearchParams();
  const state = useMemo(() => parseSearchState(params), [params]);

  const update = useCallback(
    (patch: Partial<SearchState>, opts: { replace?: boolean } = {}) => {
      const next = { ...parseSearchState(params), ...patch };
      setParams(buildSearchParams(next), { replace: opts.replace ?? true });
    },
    [params, setParams],
  );

  return { state, update };
}
