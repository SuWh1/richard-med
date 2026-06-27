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
  return { variant: "success", text: "Источник работает" };
}

const DOT: Record<StatusVariant, string> = {
  success: "bg-[#16A34A]",
  warning: "bg-[#D97706]",
  error: "bg-[#DC2626]",
  neutral: "bg-[#CBD5E1]",
};

interface SourceHealthCardProps {
  health: SourceHealth;
  busy: boolean;
  onRun: () => void;
}

export function SourceHealthCard({ health, busy, onRun }: SourceHealthCardProps) {
  const status = busy
    ? { variant: "neutral" as StatusVariant, text: "Парсинг…" }
    : statusOf(health);

  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 rounded-xl border bg-white p-5 shadow-sm transition",
        busy ? "border-primary/40 ring-1 ring-primary/20" : "border-border",
      )}
    >
      <div className="flex min-w-0 items-center gap-3">
        <span className={cn("h-2.5 w-2.5 shrink-0 rounded-full", DOT[status.variant])} />
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-foreground">
            {sourceLabel(health.source_name)}
          </div>
          <div className="text-xs text-muted-foreground">
            Последний запуск: {formatDateTime(health.last_run_at)}
          </div>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <div className="text-right">
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
          <div className="mt-1 text-right text-xs text-muted-foreground">
            Спарсено: {health.items_saved_last}
          </div>
        </div>
        <button
          type="button"
          onClick={onRun}
          disabled={busy}
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-border text-[#CBD5E1] transition-colors hover:bg-secondary hover:text-primary disabled:opacity-50"
          aria-label="Запустить парсер"
        >
          <RotateCw className={cn("h-3.5 w-3.5", busy && "animate-spin")} />
        </button>
      </div>
    </div>
  );
}
