import { AlertTriangle, Check, Clock } from "lucide-react";

import type { Freshness } from "@/types";
import { freshnessLabel } from "@/lib/format";

const STYLES: Record<Freshness, { className: string; Icon: typeof Check }> = {
  fresh: { className: "bg-[#DCFCE7] text-[#16A34A]", Icon: Check },
  recent: { className: "bg-[#F1F5F9] text-[#475569]", Icon: Clock },
  stale: { className: "bg-[#FEF3C7] text-[#D97706]", Icon: AlertTriangle },
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
