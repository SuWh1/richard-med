import {
  Activity,
  AlertTriangle,
  BarChart2,
  CheckCircle2,
  Database,
} from "lucide-react";

import type { DashboardKpis } from "@/lib/dashboard";

function cards(k: DashboardKpis) {
  return [
    { label: "Источники", value: k.sources, Icon: Database, color: "text-primary", bg: "bg-accent" },
    { label: "Активные цены", value: k.activePrices, Icon: BarChart2, color: "text-primary", bg: "bg-accent" },
    { label: "Свежие цены", value: k.freshPrices, Icon: CheckCircle2, color: "text-success", bg: "bg-success-soft" },
    { label: "Устаревшие", value: k.stalePrices, Icon: Activity, color: "text-warning", bg: "bg-warning-soft" },
    { label: "Ошибки", value: k.errorSources, Icon: AlertTriangle, color: "text-danger", bg: "bg-danger-soft" },
  ];
}

export function Kpis({ kpis }: { kpis: DashboardKpis }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      {cards(kpis).map((c) => (
        <div key={c.label} className="rounded-xl border border-border bg-white p-5 shadow-sm">
          <div className={`mb-3 flex h-9 w-9 items-center justify-center rounded-xl ${c.bg}`}>
            <c.Icon className={`h-5 w-5 ${c.color}`} />
          </div>
          <div className={`mb-0.5 text-2xl font-bold ${c.color}`}>{c.value}</div>
          <div className="text-sm text-muted-foreground">{c.label}</div>
        </div>
      ))}
    </div>
  );
}
