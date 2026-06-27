import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import type { CategoryStat, ServicePriceStat } from "@/types";
import { fetchAnalyticsOverview, fetchPriceStats } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { PriceRangeBar } from "@/components/PriceRangeBar";

const CITIES = ["", "Астана", "Алматы"];
const CATEGORIES = ["", "лаборатория", "приём врача", "диагностика", "процедура"];

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
    <div className="mx-auto max-w-4xl px-4 py-8">
      <header className="mb-6 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Аналитика цен</h1>
          <p className="text-sm text-slate-500">
            Диапазоны цен по услугам и категориям на основе собранных данных
          </p>
        </div>
        <Link to="/" className="shrink-0 text-sm font-medium text-sky-700 hover:underline">
          ← К поиску
        </Link>
      </header>

      <div className="mb-6 flex flex-wrap gap-3">
        <Select label="Город" value={city} onChange={setCity} options={CITIES} allLabel="Все города" />
        <Select
          label="Категория"
          value={category}
          onChange={setCategory}
          options={CATEGORIES}
          allLabel="Все категории"
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
          <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
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
        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
          По услугам — диапазон между клиниками
        </h2>
        {statsQuery.isLoading && <p className="text-sm text-slate-400">Загрузка…</p>}
        {statsQuery.isError && (
          <p className="text-sm text-rose-600">Не удалось загрузить аналитику.</p>
        )}
        {statsQuery.isSuccess && stats.length === 0 && (
          <p className="text-sm text-slate-500">Нет данных по выбранным фильтрам.</p>
        )}
        <div className="space-y-3">
          {stats.map((s) => (
            <ServiceStatRow key={s.service_id} stat={s} />
          ))}
        </div>
      </section>

      <footer className="mt-10 border-t border-slate-100 pt-4 text-xs text-slate-400">
        Средние значения рассчитаны по одной услуге между клиниками. Устаревшие цены
        (старше 30 дней) исключены. Информация носит справочный характер.
      </footer>
    </div>
  );
}

function Select({
  label,
  value,
  onChange,
  options,
  allLabel,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  allLabel: string;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900"
      >
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt === "" ? allLabel : opt}
          </option>
        ))}
      </select>
    </label>
  );
}

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-2xl font-bold tracking-tight text-slate-900">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

function CategoryCard({ stat }: { stat: CategoryStat }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-baseline justify-between">
        <span className="text-sm font-semibold text-slate-900">{stat.category}</span>
        <span className="text-xs text-slate-400">{stat.service_count} услуг</span>
      </div>
      <div className="mt-1 text-sm text-slate-600">
        {formatPrice(stat.min_kzt)} – {formatPrice(stat.max_kzt)}
      </div>
      <div className="text-xs text-slate-400">медиана {formatPrice(stat.median_kzt)}</div>
    </div>
  );
}

function ServiceStatRow({ stat }: { stat: ServicePriceStat }) {
  const multi = stat.clinic_count > 1;
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-base font-semibold text-slate-900">{stat.service_name}</span>
        <span className="text-xs text-slate-400">
          {stat.clinic_count} {multi ? "клиник" : "клиника"}
        </span>
      </div>
      <div className="mt-1 flex items-baseline gap-3">
        <span className="text-2xl font-bold tracking-tight text-slate-900">
          {formatPrice(stat.avg_kzt)}
        </span>
        <span className="text-xs text-slate-400">в среднем</span>
        {multi && stat.spread_pct > 0 && (
          <span className="text-xs font-medium text-amber-600">
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
        <p className="mt-2 text-xs text-slate-400">Одна клиника — диапазон недоступен</p>
      )}
    </article>
  );
}
