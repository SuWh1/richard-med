import { Link, useLocation, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Clock, ExternalLink, Star } from "lucide-react";

import type { ClinicInsight, CompareRow } from "@/types";
import { fetchCompare, fetchCompareInsight } from "@/lib/api";
import { formatRating } from "@/lib/rating";
import { Skeleton } from "@/components/ui/skeleton";
import { parseClinicIds } from "@/lib/compare";
import { ADVANTAGE, compareInsights } from "@/lib/compareInsights";
import { sourceViewUrl } from "@/lib/sourceUrl";
import { type SearchContext, searchCrumb } from "@/lib/breadcrumb";
import { formatPrice } from "@/lib/format";
import { cn } from "@/components/ui/utils";
import { ClinicAvatar } from "@/components/ClinicAvatar";
import { FreshBadge } from "@/components/FreshBadge";
import { AppShell } from "@/components/AppShell";

function durationLabel(min: number | null, max: number | null): string {
  if (min == null && max == null) return "";
  if (min != null && max != null && min !== max) return `${min}–${max} дн.`;
  return `${max ?? min} дн.`;
}

function savings(rows: CompareRow[]): number {
  if (rows.length < 2) return 0;
  const prices = rows.map((r) => r.price_kzt);
  return Math.max(...prices) - Math.min(...prices);
}

interface AttributeRowProps {
  label: string;
  value: React.ReactNode;
  best?: boolean;
}

function AttributeRow({ label, value, best = false }: AttributeRowProps) {
  return (
    <div className="flex items-center justify-between gap-3 border-t border-secondary py-2.5 text-sm">
      <span className="text-muted-foreground">{label}</span>
      <span
        className={cn(
          "flex items-center gap-1 text-right font-medium",
          best ? "text-success" : "text-foreground",
        )}
      >
        {best && <CheckCircle2 className="h-3.5 w-3.5" />}
        {value}
      </span>
    </div>
  );
}

function ClinicColumn({
  row,
  serviceName,
  advantages,
  freshest,
  fastest,
  ai,
  aiLoading,
  aiError,
  isAiPick,
}: {
  row: CompareRow;
  serviceName: string;
  advantages: string[];
  freshest: boolean;
  fastest: boolean;
  ai?: ClinicInsight;
  aiLoading: boolean;
  aiError: boolean;
  isAiPick: boolean;
}) {
  const hasDuration = row.duration_min != null || row.duration_max != null;
  const sourceHref = sourceViewUrl(row.source_url, row.city, serviceName);
  return (
    <div
      className={cn(
        "flex flex-col rounded-2xl border bg-white p-5 shadow-sm transition-shadow",
        row.is_cheapest
          ? "border-success ring-1 ring-success/30"
          : "border-border",
      )}
    >
      <div className="mb-4 flex h-5 items-center">
        {row.is_cheapest && (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-success">
            <Star className="h-3.5 w-3.5 fill-success" /> Оптимальный выбор
          </span>
        )}
      </div>

      <div className="flex items-center gap-3">
        <ClinicAvatar name={row.clinic_name} />
        <div className="min-w-0">
          <div className="truncate font-semibold text-foreground">{row.clinic_name}</div>
          <div className="truncate text-xs text-muted-foreground">
            {row.city ?? row.address ?? ""}
          </div>
        </div>
      </div>

      <div className="mt-4">
        <div
          className={cn(
            "text-3xl font-bold leading-none",
            row.is_cheapest ? "text-success" : "text-foreground",
          )}
        >
          {formatPrice(row.price_kzt)}
        </div>
        <div className="mt-2 text-sm">
          {row.is_cheapest ? (
            <span className="font-semibold text-success">Лучшая цена</span>
          ) : (
            <span className="font-semibold text-danger">
              +{formatPrice(row.price_delta)}
              <span className="ml-1 font-normal text-muted-foreground">
                дороже на {row.delta_pct}%
              </span>
            </span>
          )}
        </div>
      </div>

      <div className="mt-4">
        <AttributeRow
          label="Свежесть"
          best={freshest}
          value={<FreshBadge freshness={row.freshness} ageDays={row.age_days} />}
        />
        <AttributeRow
          label="Срок"
          best={fastest && hasDuration}
          value={
            hasDuration ? (
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {durationLabel(row.duration_min, row.duration_max)}
              </span>
            ) : null
          }
        />
      </div>

      {advantages.length > 0 && (
        <div className="mt-4 space-y-1.5">
          {advantages.map((a) => (
            <div
              key={a}
              className="flex items-center gap-1.5 rounded-lg bg-success-soft px-2.5 py-1.5 text-[12px] font-medium text-success"
            >
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0" /> {a}
            </div>
          ))}
        </div>
      )}

      <div
        className={cn(
          "mt-4 rounded-xl border px-3 py-2.5",
          isAiPick ? "border-success/40 bg-success-soft/40" : "border-border bg-accent/15",
        )}
      >
        <div className="mb-1.5 flex flex-wrap items-center gap-x-2 gap-y-1">
          <span className="text-[11px] font-semibold text-primary">Отзывы (ИИ)</span>
          {ai?.rating != null && (
            <span className="flex items-center gap-0.5 text-[11px] font-semibold text-foreground">
              <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
              {formatRating(ai.rating)}
            </span>
          )}
          {isAiPick && (
            <span className="rounded-full bg-success px-1.5 py-0.5 text-[10px] font-medium text-white">
              Выбор ИИ
            </span>
          )}
        </div>
        {aiLoading ? (
          <div className="space-y-1.5 py-0.5">
            <Skeleton className="h-2.5 w-full" />
            <Skeleton className="h-2.5 w-4/5" />
          </div>
        ) : ai && ai.rating == null && !ai.reviews_count ? (
          <p className="text-[12px] text-faintest">Отзывов пока нет</p>
        ) : ai?.summary ? (
          <p className="text-[12px] leading-relaxed text-muted-foreground">{ai.summary}</p>
        ) : (
          <p className="text-[12px] text-faintest">
            {aiError ? "ИИ недоступен" : "Отзывов пока нет"}
          </p>
        )}
      </div>

      <div className="mt-4 flex items-center gap-3 border-t border-secondary pt-4 text-sm">
        <Link
          to={`/clinics/${row.clinic_id}`}
          className="font-medium text-primary hover:underline"
        >
          Подробнее
        </Link>
        <a
          href={sourceHref}
          target="_blank"
          rel="noreferrer"
          className="ml-auto inline-flex items-center gap-1 text-muted-foreground hover:text-foreground"
        >
          Источник <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    </div>
  );
}

export function ComparePage() {
  const [params] = useSearchParams();
  const fromSearch = useLocation().state as SearchContext | null;
  const serviceId = Number(params.get("service_id"));
  const clinicIds = parseClinicIds(params.get("clinic_ids"));
  const city = params.get("city");
  const enabled = Number.isInteger(serviceId) && serviceId > 0 && clinicIds.length > 0;

  const compareQuery = useQuery({
    queryKey: ["compare", serviceId, clinicIds.join(","), city],
    queryFn: () => fetchCompare(serviceId, clinicIds, city),
    enabled,
  });

  const insightQuery = useQuery({
    queryKey: ["compare-insight", serviceId, clinicIds.join(",")],
    queryFn: () => fetchCompareInsight(serviceId, clinicIds),
    enabled,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    retry: 1,
  });

  const data = compareQuery.data;
  const rows = data?.rows ?? [];
  const diff = savings(rows);
  const insights = compareInsights(rows);
  const wide = rows.length >= 3;

  const insight = insightQuery.data;
  const aiByClinic = new Map<number, ClinicInsight>(
    (insight?.clinics ?? []).map((c) => [c.clinic_id, c]),
  );
  // Skeleton until the query truly settles, so the empty state never flashes first.
  const aiLoading = enabled && !insightQuery.isSuccess && !insightQuery.isError;
  const aiError = insightQuery.isError;

  return (
    <AppShell
      breadcrumb={[
        { label: "Поиск", href: "/search" },
        ...searchCrumb(fromSearch),
        { label: "Сравнение" },
      ]}
    >
      <div className="mx-auto w-full max-w-[1400px] px-4 py-6 lg:px-6">
        {!enabled && (
          <p className="text-sm text-muted-foreground">
            Выберите услугу и клиники для сравнения.
          </p>
        )}

        {compareQuery.isLoading && (
          <div className="space-y-4">
            <Skeleton className="h-7 w-64" />
            <div className="mx-auto grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-2">
              {Array.from({ length: 2 }).map((_, i) => (
                <div
                  key={i}
                  className="space-y-3 rounded-2xl border border-border bg-card p-5 shadow-sm"
                >
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-9 w-32" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              ))}
            </div>
          </div>
        )}

        {data && rows.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Нет активных цен для выбранных клиник.
          </p>
        )}

        {data && rows.length > 0 && (
          <>
            <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
              <div>
                <h1 className="text-xl font-semibold text-foreground">
                  Сравнение клиник
                </h1>
                <p className="mt-0.5 text-sm text-muted-foreground">
                  {data.service_name}
                </p>
              </div>
              {diff > 0 && (
                <div className="rounded-xl bg-success-soft px-4 py-2 text-sm font-semibold text-success">
                  Экономия до {formatPrice(diff)}
                </div>
              )}
            </div>

            <div
              className={cn(
                "mx-auto grid w-full grid-cols-1 gap-4 sm:grid-cols-2",
                wide ? "max-w-5xl lg:grid-cols-3" : "max-w-3xl",
              )}
            >
              {rows.map((row) => (
                <ClinicColumn
                  key={row.clinic_id}
                  row={row}
                  serviceName={data.service_name}
                  advantages={insights[row.clinic_id] ?? []}
                  freshest={(insights[row.clinic_id] ?? []).includes(ADVANTAGE.fresh)}
                  fastest={(insights[row.clinic_id] ?? []).includes(ADVANTAGE.fast)}
                  ai={aiByClinic.get(row.clinic_id)}
                  aiLoading={aiLoading}
                  aiError={aiError}
                  isAiPick={insight?.best_clinic_id === row.clinic_id}
                />
              ))}
            </div>

            <div className="mt-6 flex justify-end">
              <Link
                to="/"
                className="rounded-xl border border-border px-5 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-white"
              >
                ← Назад к поиску
              </Link>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
