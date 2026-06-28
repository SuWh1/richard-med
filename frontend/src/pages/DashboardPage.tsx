import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Zap } from "lucide-react";

import type { ParseRunSummary, ParsedPriceSample } from "@/types";
import {
  fetchCities,
  fetchParseRuns,
  fetchRunDetail,
  fetchSourceHealth,
  triggerRun,
} from "@/lib/api";
import {
  formatDateTime,
  formatDuration,
  formatPrice,
  sourceLabel,
} from "@/lib/format";
import { summarizeHealth } from "@/lib/dashboard";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Kpis } from "@/components/Kpis";
import { RunStatusBadge } from "@/components/RunStatusBadge";
import { SourceHealthCard } from "@/components/SourceHealthCard";
import { FreshBadge } from "@/components/FreshBadge";
import { AnimatedList } from "@/components/AnimatedList";
import { AppShell } from "@/components/AppShell";
import { Skeleton } from "@/components/ui/skeleton";
import { ServicesTable } from "@/components/ServicesTable";
import { UnmatchedQueue } from "@/components/UnmatchedQueue";

const FALLBACK_CITIES = ["Астана", "Алматы"];
const ALL_CITIES = "__all__"; // backend sentinel: run every supported city

export function DashboardPage() {
  const queryClient = useQueryClient();
  const [city, setCity] = useState(FALLBACK_CITIES[0]);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);

  const citiesQuery = useQuery({ queryKey: ["cities"], queryFn: fetchCities });
  const cityNames = citiesQuery.data?.length
    ? citiesQuery.data.map((c) => c.name)
    : FALLBACK_CITIES;
  // Sources the user just triggered, before a "running" row appears in the data.
  const [triggeredAt, setTriggeredAt] = useState<Record<string, number>>({});
  const [, forceTick] = useState(0);
  const busyRef = useRef(false);

  const healthQuery = useQuery({
    queryKey: ["source-health"],
    queryFn: fetchSourceHealth,
    refetchInterval: () => (busyRef.current ? 2000 : false),
  });
  const runsQuery = useQuery({
    queryKey: ["parse-runs"],
    queryFn: () => fetchParseRuns(20),
    refetchInterval: () => (busyRef.current ? 2000 : false),
  });

  const runs = useMemo(() => runsQuery.data ?? [], [runsQuery.data]);

  // Open the most recent run by default so the detail panel is never empty.
  useEffect(() => {
    if (selectedRun == null && runs.length > 0) setSelectedRun(runs[0].id);
  }, [runs, selectedRun]);

  // Latest run per source (runs come newest-first) → which sources are mid-parse.
  const latestBySource = useMemo(() => {
    const map = new Map<string, ParseRunSummary>();
    for (const r of runs) if (!map.has(r.source_name)) map.set(r.source_name, r);
    return map;
  }, [runs]);

  const runningSources = useMemo(
    () =>
      new Set(
        [...latestBySource.values()]
          .filter((r) => r.status === "running")
          .map((r) => r.source_name),
      ),
    [latestBySource],
  );

  // Hand off from the optimistic flag to data once our triggered run shows up.
  useEffect(() => {
    setTriggeredAt((prev) => {
      let changed = false;
      const next = { ...prev };
      for (const [source, at] of Object.entries(prev)) {
        const latest = latestBySource.get(source);
        if (latest && new Date(latest.started_at).getTime() >= at - 1000) {
          delete next[source];
          changed = true;
        }
      }
      return changed ? next : prev;
    });
  }, [latestBySource]);

  const isBusy = (source: string) =>
    triggeredAt[source] !== undefined || runningSources.has(source);
  const anyBusy = (healthQuery.data ?? []).some((h) => isBusy(h.source_name));
  busyRef.current = anyBusy;

  // Tick once a second while parsing so elapsed timers advance.
  useEffect(() => {
    if (!anyBusy) return;
    const id = setInterval(() => forceTick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, [anyBusy]);

  const runMutation = useMutation({
    mutationFn: (source: string | null) => triggerRun(source, city),
    onMutate: (source) => {
      const sources = source ? [source] : (healthQuery.data ?? []).map((h) => h.source_name);
      const stamp = Date.now();
      setTriggeredAt((prev) => ({
        ...prev,
        ...Object.fromEntries(sources.map((s) => [s, stamp])),
      }));
    },
    onError: (_e, source) => {
      const sources = source ? [source] : (healthQuery.data ?? []).map((h) => h.source_name);
      setTriggeredAt((prev) => {
        const next = { ...prev };
        for (const s of sources) delete next[s];
        return next;
      });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["parse-runs"] });
      queryClient.invalidateQueries({ queryKey: ["source-health"] });
    },
  });

  return (
    <AppShell
      breadcrumb={[{ label: "Кабинет", href: "/cabinet" }, { label: "Source Health" }]}
    >
      <div className="mx-auto w-full max-w-[1400px] px-4 py-8 lg:px-6">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Source Health Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Управление парсерами и мониторинг источников
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={city} onValueChange={setCity} disabled={anyBusy}>
            <SelectTrigger className="h-9 w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_CITIES}>Все города</SelectItem>
              {cityNames.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <button
            onClick={() => runMutation.mutate(null)}
            disabled={anyBusy}
            className="flex min-h-[36px] items-center gap-2 rounded-xl bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary-hover disabled:opacity-50"
          >
            <Zap className="h-4 w-4" /> {anyBusy ? "Идёт парсинг…" : "Запустить все"}
          </button>
        </div>
      </header>

      <div className="mb-6">
        <Kpis kpis={summarizeHealth(healthQuery.data ?? [])} />
      </div>

      {runMutation.isError ? (
        <p className="mb-4 rounded-lg bg-danger-soft px-3 py-2 text-sm text-danger">
          {(runMutation.error as Error).message}
        </p>
      ) : null}

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Источники данных
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {healthQuery.data?.map((health) => (
            <SourceHealthCard
              key={health.source_name}
              health={health}
              busy={isBusy(health.source_name)}
              onRun={() => runMutation.mutate(health.source_name)}
            />
          ))}
          {healthQuery.isLoading &&
            Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="space-y-4 rounded-2xl border border-border bg-white p-5 shadow-sm"
              >
                <Skeleton className="h-4 w-32" />
                <div className="flex items-center gap-4">
                  <Skeleton className="h-16 w-16 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                </div>
                <Skeleton className="h-8 w-full" />
              </div>
            ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted-foreground">
          Запуски парсера
        </h2>
        <div className="grid gap-6 lg:grid-cols-2">
          <RunHistory runs={runs} selectedRun={selectedRun} onSelect={setSelectedRun} />
          <RunDetailPanel runId={selectedRun} />
        </div>
      </section>

      <section className="mt-8">
        <ServicesTable busy={anyBusy} />
      </section>

      <section className="mt-8">
        <UnmatchedQueue busy={anyBusy} />
      </section>
      </div>
    </AppShell>
  );
}

function RunHistory({
  runs,
  selectedRun,
  onSelect,
}: {
  runs: ParseRunSummary[];
  selectedRun: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <div className="rounded-2xl border border-border bg-white shadow-sm">
      <h2 className="border-b border-secondary px-4 py-3 font-semibold text-foreground">
        История запусков
      </h2>
      {runs.length === 0 ? (
        <p className="px-4 py-6 text-sm text-muted-foreground">Запусков пока нет.</p>
      ) : (
        <AnimatedList className="divide-y divide-secondary">
          {runs.map((run) => (
          <button
            key={run.id}
            onClick={() => onSelect(run.id)}
            className={`flex w-full items-center justify-between gap-3 px-4 py-3 text-left text-sm transition hover:bg-secondary/50 ${
              selectedRun === run.id ? "bg-secondary/50" : ""
            }`}
          >
            <div>
              <div className="font-medium text-foreground">
                {sourceLabel(run.source_name)}
                <span className="ml-2 text-xs text-faintest">{run.city}</span>
              </div>
              <div className="text-xs text-muted-foreground">{formatDateTime(run.started_at)}</div>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground">
                {run.items_saved}/{run.items_found}
              </span>
              <RunStatusBadge status={run.status} />
            </div>
          </button>
          ))}
        </AnimatedList>
      )}
    </div>
  );
}

function RunDetailPanel({ runId }: { runId: number | null }) {
  const detailQuery = useQuery({
    queryKey: ["run-detail", runId],
    queryFn: () => fetchRunDetail(runId as number),
    enabled: runId !== null,
  });

  if (runId === null) {
    return (
      <div className="flex items-center justify-center rounded-2xl border border-dashed border-border p-8 text-sm text-faintest">
        Выберите запуск, чтобы увидеть детали
      </div>
    );
  }
  if (detailQuery.isLoading || !detailQuery.data) {
    return (
      <div className="rounded-2xl border border-border bg-white p-8 text-sm text-muted-foreground">
        Загрузка…
      </div>
    );
  }

  const { run, errors, unmatched_count, unmatched_samples, price_samples } = detailQuery.data;

  return (
    <div className="rounded-2xl border border-border bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-secondary px-4 py-3">
        <h2 className="font-semibold text-foreground">
          {sourceLabel(run.source_name)} · {run.city}
        </h2>
        <RunStatusBadge status={run.status} />
      </div>

      <dl className="grid grid-cols-3 gap-2 px-4 py-3 text-sm">
        <Metric label="Найдено" value={run.items_found} />
        <Metric label="Сохранено" value={run.items_saved} />
        <Metric label="Не сопоставлено" value={unmatched_count} warn={unmatched_count > 0} />
        <Metric label="Длительность" value={formatDuration(run.duration_sec)} />
        <Metric label="Начало" value={formatDateTime(run.started_at)} />
        <Metric label="Конец" value={formatDateTime(run.finished_at)} />
      </dl>

      {errors.length > 0 ? (
        <div className="border-t border-secondary px-4 py-3">
          <h3 className="mb-1 text-xs font-semibold uppercase tracking-wide text-danger">Ошибки</h3>
          <ul className="space-y-1 text-xs text-danger">
            {errors.map((e, i) => (
              <li key={i} className="truncate" title={e}>
                {e}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {price_samples.length > 0 ? (
        <div className="border-t border-secondary px-4 py-3">
          <h3 className="mb-2 text-xs font-semibold uppercase text-muted-foreground">
            Что распарсено (примеры)
          </h3>
          <ul className="space-y-2">
            {price_samples.map((p, i) => (
              <PriceSampleRow key={i} sample={p} />
            ))}
          </ul>
        </div>
      ) : null}

      {unmatched_samples.length > 0 ? (
        <div className="border-t border-secondary px-4 py-3">
          <h3 className="mb-1 text-xs font-semibold uppercase text-warning">
            Очередь на сопоставление
          </h3>
          <ul className="space-y-1 text-xs text-muted-foreground">
            {unmatched_samples.map((name, i) => (
              <li key={i} className="truncate" title={name}>
                {name}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function PriceSampleRow({ sample }: { sample: ParsedPriceSample }) {
  return (
    <li className="flex items-center justify-between gap-3 text-sm">
      <div className="min-w-0">
        <div className="truncate font-medium text-foreground" title={sample.service_name}>
          {sample.service_name}
        </div>
        <div className="truncate text-xs text-muted-foreground" title={sample.service_name_raw ?? ""}>
          {sample.clinic_name}
          {sample.service_name_raw ? ` · ${sample.service_name_raw}` : ""}
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className="text-xs text-faintest" title="Уверенность сопоставления">
          {Math.round(sample.match_confidence * 100)}%
        </span>
        <FreshBadge freshness={sample.freshness} ageDays={sample.age_days} />
        <span className="font-semibold text-foreground">{formatPrice(sample.price_kzt)}</span>
      </div>
    </li>
  );
}

function Metric({ label, value, warn }: { label: string; value: string | number; warn?: boolean }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className={`font-semibold ${warn ? "text-warning" : "text-foreground"}`}>{value}</dd>
    </div>
  );
}
