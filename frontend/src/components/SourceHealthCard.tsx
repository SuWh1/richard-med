import { AlertTriangle, Check, RotateCw } from "lucide-react";

import type { SourceHealth } from "@/types";
import { formatDateTime, sourceLabel } from "@/lib/format";
import { cn } from "@/components/ui/utils";
import { StatusBadge, type StatusVariant } from "@/components/StatusBadge";

function statusOf(health: SourceHealth): { variant: StatusVariant; text: string } {
  if (health.last_status === "failed" || health.last_error) {
    return { variant: "error", text: "Есть ошибки" };
  }
  if (health.active_prices === 0 || health.active_prices - health.stale_prices <= 0) {
    return { variant: "warning", text: "Нет свежих данных" };
  }
  return { variant: "success", text: "Работает" };
}

const DOT: Record<StatusVariant, string> = {
  success: "bg-success",
  warning: "bg-warning",
  error: "bg-danger",
  neutral: "bg-faintest",
};

const RING: Record<StatusVariant, string> = {
  success: "text-success",
  warning: "text-warning",
  error: "text-danger",
  neutral: "text-primary",
};

function Ring({ value, className }: { value: number; className: string }) {
  const r = 26;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - Math.max(0, Math.min(1, value)));
  return (
    <svg viewBox="0 0 64 64" className="h-16 w-16 -rotate-90">
      <circle cx="32" cy="32" r={r} fill="none" strokeWidth="6" className="stroke-secondary" />
      <circle
        cx="32"
        cy="32"
        r={r}
        fill="none"
        strokeWidth="6"
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        className={cn("stroke-current transition-[stroke-dashoffset] duration-500", className)}
      />
    </svg>
  );
}

function Stat({
  value,
  label,
  tone,
}: {
  value: string | number;
  label: string;
  tone?: "success";
}) {
  return (
    <div>
      <div
        className={cn(
          "text-lg font-bold leading-none",
          tone === "success" ? "text-success" : "text-foreground",
        )}
      >
        {value}
      </div>
      <div className="mt-0.5 text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
    </div>
  );
}

interface SourceHealthCardProps {
  health: SourceHealth;
  busy: boolean;
  onRun: () => void;
}

export function SourceHealthCard({ health, busy, onRun }: SourceHealthCardProps) {
  const status = busy
    ? { variant: "neutral" as StatusVariant, text: "Парсинг…" }
    : statusOf(health);
  const fresh = health.active_prices - health.stale_prices;
  const lastRun = formatDateTime(health.last_run_at) || "ещё не запускался";

  return (
    <div
      className={cn(
        "flex flex-col rounded-2xl border bg-white p-5 shadow-sm transition-all",
        busy ? "border-primary/40 ring-1 ring-primary/20" : "border-border hover:shadow-md",
      )}
    >
      <div className="flex items-center gap-2.5">
        <span className={cn("h-2.5 w-2.5 shrink-0 rounded-full", DOT[status.variant])} />
        <span className="min-w-0 flex-1 truncate font-semibold text-foreground">
          {sourceLabel(health.source_name)}
        </span>
        <StatusBadge variant={status.variant}>
          {status.variant === "success" ? (
            <Check className="h-3 w-3" />
          ) : status.variant === "neutral" ? (
            <RotateCw className="h-3 w-3 animate-spin" />
          ) : (
            <AlertTriangle className="h-3 w-3" />
          )}
          {status.text}
        </StatusBadge>
      </div>

      <div className="mt-4 flex items-center gap-4">
        <div className="relative shrink-0">
          <Ring value={health.success_rate_7d} className={RING[status.variant]} />
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-sm font-bold text-foreground">
              {Math.round(health.success_rate_7d * 100)}%
            </span>
            <span className="text-[9px] uppercase tracking-wide text-muted-foreground">
              успех
            </span>
          </div>
        </div>
        <div className="grid flex-1 grid-cols-2 gap-x-3 gap-y-3">
          <Stat value={health.active_prices.toLocaleString("ru-RU")} label="активных цен" />
          <Stat value={fresh.toLocaleString("ru-RU")} label="свежих" tone="success" />
          <Stat value={health.items_saved_last.toLocaleString("ru-RU")} label="в последнем" />
          <Stat value={health.runs_7d} label="запусков · 7д" />
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between gap-2 border-t border-secondary pt-3">
        <span className="min-w-0 truncate text-xs text-muted-foreground">
          Запуск: {lastRun}
        </span>
        <button
          type="button"
          onClick={onRun}
          disabled={busy}
          className="flex shrink-0 items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:border-primary/30 hover:bg-secondary hover:text-primary disabled:opacity-50"
        >
          <RotateCw className={cn("h-3.5 w-3.5", busy && "animate-spin")} /> Запустить
        </button>
      </div>

      {health.last_error && (
        <p className="mt-2 truncate text-[11px] text-danger" title={health.last_error}>
          {health.last_error}
        </p>
      )}
    </div>
  );
}
