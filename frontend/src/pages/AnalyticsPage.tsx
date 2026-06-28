import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Building2, TrendingDown } from "lucide-react";

import type { CategoryStat, ServicePriceStat } from "@/types";
import { fetchAnalyticsOverview, fetchPriceStats } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PriceRangeBar } from "@/components/PriceRangeBar";
import { AppShell } from "@/components/AppShell";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/components/ui/utils";

const ALL = "all";
const CITY_OPTIONS = ["Астана", "Алматы"];
const CATEGORY_OPTIONS = ["лаборатория", "приём врача", "диагностика", "процедура"];

function plural(n: number, [one, few, many]: [string, string, string]): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
}

const pluralClinics = (n: number) => plural(n, ["клиника", "клиники", "клиник"]);

/** How much the cheapest clinic saves versus the typical (median) price — the
 *  actionable, outlier-proof framing of price dispersion. */
function savingsPct(stat: ServicePriceStat): number {
  if (stat.median_kzt <= 0 || stat.min_kzt >= stat.median_kzt) return 0;
  return Math.round(((stat.median_kzt - stat.min_kzt) / stat.median_kzt) * 100);
}

export function AnalyticsPage() {
  const [city, setCity] = useState("");
  const [category, setCategory] = useState("");

  const overviewQuery = useQuery({
    queryKey: ["analytics-overview", city],
    queryFn: () => fetchAnalyticsOverview({ city: city || undefined }),
  });

  // Unfiltered, so the city dropdown lists every city with data (the filtered
  // overview returns only the selected city).
  const cityListQuery = useQuery({
    queryKey: ["analytics-city-list"],
    queryFn: () => fetchAnalyticsOverview({}),
  });
  const cityOptions = (cityListQuery.data?.cities ?? [])
    .map((c) => c.city)
    .sort((a, b) => a.localeCompare(b, "ru"));

  const statsQuery = useQuery({
    queryKey: ["analytics-stats", city, category],
    queryFn: () =>
      fetchPriceStats({
        city: city || undefined,
        category: category || undefined,
        limit: 40,
      }),
  });

  const overview = overviewQuery.data;
  const stats = statsQuery.data ?? [];
  const topSaving = stats.reduce((m, s) => Math.max(m, savingsPct(s)), 0);

  return (
    <AppShell breadcrumb={[{ label: "Поиск", href: "/search" }, { label: "Аналитика цен" }]}>
      <div className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6 lg:py-10">
        <header className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold tracking-tight text-foreground sm:text-[28px]">
              Аналитика цен
            </h1>
            <p className="mt-2 max-w-[60ch] text-[15px] leading-relaxed text-muted-foreground text-pretty">
              Сравните, сколько стоит одна и та же услуга в разных клиниках — и где выгода
              от сравнения цен наибольшая.
            </p>
          </div>
          <div className="flex flex-wrap gap-2.5">
            <FilterSelect
              value={city || ALL}
              onChange={(v) => setCity(v === ALL ? "" : v)}
              allLabel="Все города"
              options={cityOptions.length ? cityOptions : CITY_OPTIONS}
            />
            <FilterSelect
              value={category || ALL}
              onChange={(v) => setCategory(v === ALL ? "" : v)}
              allLabel="Все категории"
              options={CATEGORY_OPTIONS}
            />
          </div>
        </header>

        {overview && (
          <SummaryStrip
            services={overview.total_services}
            cities={overview.cities.length}
            categories={overview.categories.length}
            topSaving={topSaving}
          />
        )}

        {overview && overview.categories.length > 0 && (
          <section className="mt-10 space-y-3" aria-label="Сравнение категорий">
            <SectionHeading title="Сравнение категорий" />
            <CategoryCompare categories={overview.categories} />
          </section>
        )}

        <section className="mt-10 space-y-3" aria-label="Услуги">
          <SectionHeading
            title="Цены по услугам"
            hint="Полоса показывает разброс между клиниками: слева дешевле, справа дороже."
          />

          {statsQuery.isLoading && (
            <div className="grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(320px,1fr))]">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="rounded-2xl border border-border bg-card p-5 shadow-sm">
                  <Skeleton className="mb-3 h-4 w-40" />
                  <Skeleton className="mb-4 h-7 w-28" />
                  <Skeleton className="h-2.5 w-full rounded-full" />
                </div>
              ))}
            </div>
          )}
          {statsQuery.isError && (
            <p className="text-sm text-destructive">Не удалось загрузить аналитику.</p>
          )}
          {statsQuery.isSuccess && stats.length === 0 && (
            <p className="text-sm text-muted-foreground">Нет данных по выбранным фильтрам.</p>
          )}

          <div className="grid gap-4 [grid-template-columns:repeat(auto-fill,minmax(320px,1fr))]">
            {stats.map((s) => (
              <ServiceStatCard key={s.service_id} stat={s} />
            ))}
          </div>
        </section>

        <footer className="mt-12 border-t border-border pt-4 text-xs text-muted-foreground">
          «Типичная цена» — медиана по клиникам; устаревшие цены (старше 30 дней) исключены.
          Информация носит справочный характер.
        </footer>
      </div>
    </AppShell>
  );
}

function FilterSelect({
  value,
  onChange,
  allLabel,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  allLabel: string;
  options: string[];
}) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="h-9 w-[150px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>{allLabel}</SelectItem>
        {options.map((opt) => (
          <SelectItem key={opt} value={opt}>
            {opt}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function SummaryStrip({
  services,
  cities,
  categories,
  topSaving,
}: {
  services: number;
  cities: number;
  categories: number;
  topSaving: number;
}) {
  return (
    <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-xl border border-border bg-card px-5 py-3.5 text-sm shadow-sm">
      <Stat value={services.toLocaleString("ru-RU")} label="услуг с ценами" />
      <span className="hidden h-5 w-px bg-border sm:block" />
      <Stat value={String(cities)} label={plural(cities, ["город", "города", "городов"])} />
      <span className="hidden h-5 w-px bg-border sm:block" />
      <Stat
        value={String(categories)}
        label={plural(categories, ["категория", "категории", "категорий"])}
      />
      {topSaving > 0 && (
        <>
          <span className="hidden h-5 w-px bg-border sm:block" />
          <span className="inline-flex items-center gap-1.5 font-medium text-success">
            <TrendingDown className="h-4 w-4" />
            экономия до {topSaving}% при сравнении
          </span>
        </>
      )}
    </div>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <span className="inline-flex items-baseline gap-1.5">
      <span className="text-base font-semibold tabular-nums text-foreground">{value}</span>
      <span className="text-muted-foreground">{label}</span>
    </span>
  );
}

function CategoryCompare({ categories }: { categories: CategoryStat[] }) {
  const maxMedian = Math.max(...categories.map((c) => c.median_kzt), 1);
  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
      <ul className="divide-y divide-border">
        {categories.map((c) => (
          <li
            key={c.category}
            className="grid grid-cols-1 gap-x-4 gap-y-2 px-5 py-3.5 sm:grid-cols-[160px_minmax(0,1fr)_auto] sm:items-center"
          >
            <div className="min-w-0">
              <div className="truncate font-medium text-foreground">{c.category}</div>
              <div className="text-xs text-muted-foreground">{c.service_count} услуг</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full rounded-full bg-primary/70"
                  style={{ width: `${Math.max((c.median_kzt / maxMedian) * 100, 4)}%` }}
                />
              </div>
              <span className="w-24 shrink-0 text-right text-sm font-semibold tabular-nums text-foreground">
                {formatPrice(c.median_kzt)}
              </span>
            </div>
            <div className="text-xs text-muted-foreground sm:text-right">
              {formatPrice(c.min_kzt)} – {formatPrice(c.max_kzt)}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ServiceStatCard({ stat }: { stat: ServicePriceStat }) {
  const multi = stat.clinic_count > 1;
  const saving = savingsPct(stat);

  return (
    <article className="flex flex-col rounded-2xl border border-border bg-card p-5 shadow-sm transition-shadow hover:shadow-md">
      <div className="mb-3 flex items-start justify-between gap-3">
        <h3 className="line-clamp-2 font-semibold leading-snug text-foreground [overflow-wrap:anywhere]">
          {stat.service_name}
        </h3>
        <span className="inline-flex shrink-0 items-center gap-1 text-xs text-muted-foreground">
          <Building2 className="h-3.5 w-3.5" />
          {stat.clinic_count} {pluralClinics(stat.clinic_count)}
        </span>
      </div>

      <div className="flex items-end justify-between gap-2">
        <div>
          <div className="text-2xl font-bold tracking-tight tabular-nums text-foreground">
            {formatPrice(stat.median_kzt)}
          </div>
          <div className="text-xs text-muted-foreground">типичная цена</div>
        </div>
        {multi && saving > 0 && (
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold",
              "bg-success-soft text-success",
            )}
            title="Самая дешёвая клиника дешевле типичной цены на столько"
          >
            <TrendingDown className="h-3.5 w-3.5" /> выгода до {saving}%
          </span>
        )}
      </div>

      {multi ? (
        <div className="mt-4">
          <PriceRangeBar
            min={stat.min_kzt}
            max={stat.max_kzt}
            avg={stat.avg_kzt}
            median={stat.median_kzt}
          />
        </div>
      ) : (
        <p className="mt-3 text-xs text-muted-foreground">
          Одна клиника — сравнение недоступно.
        </p>
      )}
    </article>
  );
}

function SectionHeading({ title, hint }: { title: string; hint?: string }) {
  return (
    <div>
      <h2 className="text-base font-semibold text-foreground">{title}</h2>
      {hint && <p className="mt-0.5 text-xs text-muted-foreground">{hint}</p>}
    </div>
  );
}
