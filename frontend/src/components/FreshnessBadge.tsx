import type { Freshness } from "@/types";
import { freshnessLabel } from "@/lib/format";

const STYLES: Record<Freshness, string> = {
  fresh: "bg-emerald-100 text-emerald-800",
  recent: "bg-slate-100 text-slate-600",
  stale: "bg-amber-100 text-amber-800",
};

export function FreshnessBadge({
  freshness,
  ageDays,
}: {
  freshness: Freshness;
  ageDays: number;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STYLES[freshness]}`}
    >
      {freshnessLabel(freshness, ageDays)}
    </span>
  );
}
