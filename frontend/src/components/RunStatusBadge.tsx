import type { RunStatus } from "@/types";

const STYLES: Record<RunStatus, string> = {
  success: "bg-emerald-100 text-emerald-800",
  partial: "bg-amber-100 text-amber-800",
  running: "bg-sky-100 text-sky-800",
  failed: "bg-rose-100 text-rose-800",
};

const LABELS: Record<RunStatus, string> = {
  success: "Успешно",
  partial: "С ошибками",
  running: "Выполняется",
  failed: "Сбой",
};

export function RunStatusBadge({ status }: { status: RunStatus }) {
  const style = STYLES[status] ?? "bg-slate-100 text-slate-600";
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      {LABELS[status] ?? status}
    </span>
  );
}
