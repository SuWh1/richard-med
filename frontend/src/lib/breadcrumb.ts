import type { Crumb } from "@/components/AppShell";
import { searchHref } from "@/hooks/useSearchState";

export interface SearchContext {
  q?: string;
  city?: string;
  label?: string;
}

/** The originating-search step, so a deeper page can link back to its results.
 * Labelled with the resolved service name when known, falling back to the typed query. */
export function searchCrumb(ctx: SearchContext | null | undefined): Crumb[] {
  const q = ctx?.q?.trim();
  if (!q || q.length < 2) return [];
  const label = ctx?.label?.trim() || q;
  return [{ label, href: searchHref({ q, city: ctx?.city }) }];
}
