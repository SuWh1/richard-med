import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

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

const ALL = "all";
const CITY_OPTIONS = ["Астана", "Алматы"];
const CATEGORY_OPTIONS = ["лаборатория", "приём врача", "диагностика", "процедура"];

export function AnalyticsPage() {
  const [city, setCity] = useState("");
  const [category, setCategory] = useState("");

  const overviewQuery = useQuery({
    queryKey: ["analytics-overview", city],
    queryFn: () => fetchAnalyticsOverview({ city: city || undefined }),
  });

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

  return (
    <AppShell breadcrumb={[{ label: "Аналитика цен" }]} city={city || "Все города"}>
      <div className="mx-auto max-w-4xl px-4 py-8">
      <header className="mb-6">
        <h1 className="text-xl font-semibold text-foreground">Аналитика цен</h1>
        <p className="text-sm text-muted-foreground">
          Диапазоны цен по услугам и категориям на основе собранных данных
        </p>
      </header>

      <div className="mb-6 flex flex-wrap gap-3">
        <FilterSelect
          value={city || ALL}
          onChange={(v) => setCity(v === ALL ? "" : v)}
          allLabel="Все города"
          options={CITY_OPTIONS}
        />
        <FilterSelect
          value={category || ALL}
          onChange={(v) => setCategory(v === ALL ? "" : v)}
          allLabel="Все категории"
          options={CATEGORY_OPTIONS}
        />
      </div>

      {overview && (
        <section className="mb-8 grid gap-3 sm:grid-cols-3">
          <KpiCard label="Цен в базе" value={overview.total_prices.toLocaleString("ru-RU")} />
          <KpiCard label="Услуг с ценами" value={overview.total_services.toLocaleString("ru-RU")} />
          <KpiCard label="Городов" value={String(overview.cities.length)} />
        </section>
      )}

      {overview && overview.categories.length > 0 && (
        <section className="mb-8">
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted-foreground">
            По категориям
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {overview.categories.map((c) => (
              <CategoryCard key={c.category} stat={c} />
            ))}
          </div>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-muted-foreground">
          По услугам · диапазон между клиниками
        </h2>
        {statsQuery.isLoading && <p className="text-sm text-muted-foreground">Загрузка…</p>}
        {statsQuery.isError && (
          <p className="text-sm text-destructive">Не удалось загрузить аналитику.</p>
        )}
        {statsQuery.isSuccess && stats.length === 0 && (
          <p className="text-sm text-muted-foreground">Нет данных по выбранным фильтрам.</p>
        )}
        <div className="space-y-3">
          {stats.map((s) => (
            <ServiceStatRow key={s.service_id} stat={s} />
          ))}
        </div>
      </section>

      <footer className="mt-10 border-t border-border pt-4 text-xs text-muted-foreground">
        Средние значения рассчитаны по одной услуге между клиниками. Устаревшие цены
        (старше 30 дней) исключены. Информация носит справочный характер.
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
      <SelectTrigger className="h-9 w-[170px]">
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

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
      <div className="text-2xl font-bold tracking-tight text-foreground">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

function CategoryCard({ stat }: { stat: CategoryStat }) {
  return (
    <div className="rounded-xl border border-border bg-white p-4 shadow-sm">
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-semibold text-foreground">{stat.category}</span>
        <span className="text-xs text-muted-foreground">{stat.service_count} услуг</span>
      </div>
      <div className="mt-1 text-sm text-secondary-foreground">
        {formatPrice(stat.min_kzt)} – {formatPrice(stat.max_kzt)}
      </div>
      <div className="text-xs text-muted-foreground">медиана {formatPrice(stat.median_kzt)}</div>
    </div>
  );
}

function ServiceStatRow({ stat }: { stat: ServicePriceStat }) {
  const multi = stat.clinic_count > 1;
  return (
    <article className="rounded-xl border border-border bg-white p-5 shadow-sm">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-base font-semibold text-foreground">{stat.service_name}</span>
        <span className="text-xs text-muted-foreground">
          {stat.clinic_count} {multi ? "клиник" : "клиника"}
        </span>
      </div>
      <div className="mt-1 flex items-baseline gap-3">
        <span className="text-2xl font-bold tracking-tight text-foreground">
          {formatPrice(stat.avg_kzt)}
        </span>
        <span className="text-xs text-muted-foreground">в среднем</span>
        {multi && stat.spread_pct > 0 && (
          <span className="text-xs font-medium text-warning">
            разброс {Math.round(stat.spread_pct)}%
          </span>
        )}
      </div>
      {multi ? (
        <div className="mt-3">
          <PriceRangeBar
            min={stat.min_kzt}
            max={stat.max_kzt}
            avg={stat.avg_kzt}
            median={stat.median_kzt}
          />
        </div>
      ) : (
        <p className="mt-2 text-xs text-muted-foreground">
          Одна клиника · диапазон недоступен
        </p>
      )}
    </article>
  );
}
