import { AlertTriangle, Check, Clock } from "lucide-react";

import type { Freshness } from "@/types";
import { freshnessLabel } from "@/lib/format";

const STYLES: Record<Freshness, { className: string; Icon: typeof Check }> = {
  fresh: { className: "bg-success-soft text-success", Icon: Check },
  recent: { className: "bg-secondary text-secondary-foreground", Icon: Clock },
  stale: { className: "bg-warning-soft text-warning", Icon: AlertTriangle },
};

interface FreshBadgeProps {
  freshness: Freshness;
  ageDays: number;
}

export function FreshBadge({ freshness, ageDays }: FreshBadgeProps) {
  const { className, Icon } = STYLES[freshness];
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${className}`}
    >
      <Icon className="h-3 w-3" /> {freshnessLabel(freshness, ageDays)}
    </span>
  );
}
