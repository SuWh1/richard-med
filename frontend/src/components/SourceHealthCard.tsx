import type { SourceHealth } from "@/types";
import { formatDateTime, sourceLabel } from "@/lib/format";
import { RunStatusBadge } from "@/components/RunStatusBadge";

export function SourceHealthCard({
  health,
  busy,
  runningSince,
  onRun,
}: {
  health: SourceHealth;
  busy: boolean;
  runningSince: string | null;
  onRun: () => void;
}) {
  const ratePct = Math.round(health.success_rate_7d * 100);
  const elapsed = runningSince
    ? Math.max(0, Math.floor((Date.now() - new Date(runningSince).getTime()) / 1000))
    : null;

  return (
    <div
      className={`rounded-xl border bg-white p-4 shadow-sm transition ${
        busy ? "border-sky-300 ring-1 ring-sky-200" : "border-slate-200"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-900">{sourceLabel(health.source_name)}</h3>
          <p className="mt-0.5 text-xs text-slate-500">
            Последний запуск: {formatDateTime(health.last_run_at)}
          </p>
        </div>
        {busy ? (
          <RunStatusBadge status="running" />
        ) : health.last_status ? (
          <RunStatusBadge status={health.last_status} />
        ) : null}
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <Stat label="Активных цен" value={health.active_prices} />
        <Stat label="Успех (7 дн)" value={health.runs_7d ? `${ratePct}%` : "—"} />
        <Stat
          label="Найдено / сохранено"
          value={`${health.items_found_last} / ${health.items_saved_last}`}
        />
        <Stat label="Устаревших" value={health.stale_prices} warn={health.stale_prices > 0} />
      </dl>

      {health.last_error && !busy ? (
        <p
          className="mt-3 truncate rounded-md bg-rose-50 px-2 py-1 text-xs text-rose-700"
          title={health.last_error}
        >
          {health.last_error}
        </p>
      ) : null}

      {busy ? (
        <div className="mt-3">
          <div className="mb-1 flex items-center justify-between text-xs text-sky-700">
            <span>Идёт парсинг…</span>
            <span>{elapsed !== null ? `${elapsed} с` : "запуск"}</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-sky-100">
            <div className="h-full w-1/3 animate-pulse rounded-full bg-sky-500" />
          </div>
        </div>
      ) : null}

      <button
        onClick={onRun}
        disabled={busy}
        className="mt-4 w-full rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Парсинг…" : "Запустить парсер"}
      </button>
    </div>
  );
}

function Stat({ label, value, warn }: { label: string; value: string | number; warn?: boolean }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className={`font-semibold ${warn ? "text-amber-700" : "text-slate-900"}`}>{value}</dd>
    </div>
  );
}
