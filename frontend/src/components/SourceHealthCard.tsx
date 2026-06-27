import type { SourceHealth } from "@/types";
import { formatDateTime, sourceLabel } from "@/lib/format";
import { RunStatusBadge } from "@/components/RunStatusBadge";

export function SourceHealthCard({
  health,
  running,
  onRun,
}: {
  health: SourceHealth;
  running: boolean;
  onRun: () => void;
}) {
  const ratePct = Math.round(health.success_rate_7d * 100);
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-900">{sourceLabel(health.source_name)}</h3>
          <p className="mt-0.5 text-xs text-slate-500">
            Последний запуск: {formatDateTime(health.last_run_at)}
          </p>
        </div>
        {health.last_status ? <RunStatusBadge status={health.last_status} /> : null}
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
        <Stat label="Активных цен" value={health.active_prices} />
        <Stat
          label="Успех (7 дн)"
          value={health.runs_7d ? `${ratePct}%` : "—"}
        />
        <Stat label="Найдено / сохранено" value={`${health.items_found_last} / ${health.items_saved_last}`} />
        <Stat
          label="Устаревших"
          value={health.stale_prices}
          warn={health.stale_prices > 0}
        />
      </dl>

      {health.last_error ? (
        <p className="mt-3 truncate rounded-md bg-rose-50 px-2 py-1 text-xs text-rose-700" title={health.last_error}>
          {health.last_error}
        </p>
      ) : null}

      <button
        onClick={onRun}
        disabled={running}
        className="mt-4 w-full rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-700 disabled:opacity-50"
      >
        {running ? "Запуск…" : "Запустить парсер"}
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
