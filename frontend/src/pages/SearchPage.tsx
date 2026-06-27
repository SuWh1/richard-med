import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import type { PriceCard as PriceCardData, SortKey, Suggestion } from "@/types";
import { fetchSearch, fetchSuggestions } from "@/lib/api";
import { useDebounce } from "@/hooks/useDebounce";
import { SearchBar } from "@/components/SearchBar";
import { SortControls } from "@/components/SortControls";
import { PriceCard } from "@/components/PriceCard";
import { PricePassport } from "@/components/PricePassport";

export function SearchPage() {
  const [input, setInput] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [sort, setSort] = useState<SortKey>("best_value");
  const [includeStale, setIncludeStale] = useState(false);
  const [passport, setPassport] = useState<PriceCardData | null>(null);

  const debounced = useDebounce(input, 250);

  const suggestionsQuery = useQuery({
    queryKey: ["suggestions", debounced],
    queryFn: () => fetchSuggestions(debounced),
    enabled: debounced.trim().length >= 2,
  });

  const searchQuery = useQuery({
    queryKey: ["search", submitted, sort, includeStale],
    queryFn: () => fetchSearch({ q: submitted, sort, include_stale: includeStale }),
    enabled: submitted.trim().length >= 2,
  });

  const cards = searchQuery.data?.cards ?? [];
  const cheapestPrice = useMemo(
    () => (cards.length ? Math.min(...cards.map((c) => c.price_kzt)) : null),
    [cards],
  );

  const runSearch = (q: string) => {
    setInput(q);
    setSubmitted(q);
  };

  const pickSuggestion = (s: Suggestion) => runSearch(s.name_ru);

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <header className="mb-6 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Richard Med</h1>
          <p className="text-sm text-slate-500">
            Сравните реальные цены на медицинские услуги в Казахстане
          </p>
        </div>
        <Link
          to="/dashboard"
          className="shrink-0 text-sm font-medium text-sky-700 hover:underline"
        >
          Источники данных →
        </Link>
      </header>

      <SearchBar
        value={input}
        onChange={setInput}
        onSubmit={() => runSearch(input)}
        suggestions={suggestionsQuery.data ?? []}
        onPick={pickSuggestion}
      />

      {submitted.length >= 2 && (
        <div className="mt-6 space-y-4">
          {searchQuery.data?.resolved_service && (
            <div className="flex items-baseline justify-between">
              <h2 className="text-lg font-semibold text-slate-900">
                {searchQuery.data.resolved_service.name_ru}
              </h2>
              <span className="text-sm text-slate-500">
                {searchQuery.data.count} предложений
              </span>
            </div>
          )}

          {cards.length > 0 && (
            <SortControls
              sort={sort}
              onChange={setSort}
              includeStale={includeStale}
              onToggleStale={setIncludeStale}
            />
          )}

          {searchQuery.isLoading && (
            <p className="text-sm text-slate-400">Загрузка…</p>
          )}
          {searchQuery.isError && (
            <p className="text-sm text-rose-600">
              Не удалось загрузить цены. Попробуйте ещё раз.
            </p>
          )}
          {searchQuery.isSuccess && cards.length === 0 && (
            <p className="text-sm text-slate-500">
              По запросу «{submitted}» цены не найдены. Попробуйте уточнить услугу.
            </p>
          )}

          <div className="space-y-3">
            {cards.map((card) => (
              <PriceCard
                key={card.price_id}
                card={card}
                isCheapest={card.price_kzt === cheapestPrice}
                onOpenPassport={() => setPassport(card)}
              />
            ))}
          </div>
        </div>
      )}

      <footer className="mt-10 border-t border-slate-100 pt-4 text-xs text-slate-400">
        Информация о ценах носит справочный характер. Перед лечением обратитесь к
        врачу.
      </footer>

      {passport && (
        <PricePassport card={passport} onClose={() => setPassport(null)} />
      )}
    </div>
  );
}
