import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import type { PriceCard as PriceCardData, SortKey, Suggestion } from "@/types";
import { fetchFeatured, fetchSearch, fetchSuggestions } from "@/lib/api";
import { useDebounce } from "@/hooks/useDebounce";
import { SearchBar } from "@/components/SearchBar";
import { SortControls } from "@/components/SortControls";
import { PriceCard } from "@/components/PriceCard";
import { PricePassport } from "@/components/PricePassport";
import { ClinicMap } from "@/components/map/ClinicMap";

export function SearchPage() {
  const [input, setInput] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [sort, setSort] = useState<SortKey>("best_value");
  const [includeStale, setIncludeStale] = useState(false);
  const [passport, setPassport] = useState<PriceCardData | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mobileView, setMobileView] = useState<"list" | "map">("list");

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

  const isSearching = submitted.trim().length >= 2;

  const featuredQuery = useQuery({
    queryKey: ["featured"],
    queryFn: () => fetchFeatured(6),
    enabled: !isSearching,
  });

  const cards = searchQuery.data?.cards ?? [];
  const cheapestPrice = useMemo(
    () => (cards.length ? Math.min(...cards.map((c) => c.price_kzt)) : null),
    [cards],
  );
  const hasMap = useMemo(
    () => cards.some((c) => c.lat !== null && c.lng !== null),
    [cards],
  );

  const runSearch = (q: string) => {
    setInput(q);
    setSubmitted(q);
  };

  const pickSuggestion = (s: Suggestion) => runSearch(s.name_ru);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-6 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Richard Med</h1>
          <p className="text-sm text-slate-500">
            Сравните реальные цены на медицинские услуги в Казахстане
          </p>
        </div>
        <nav className="flex shrink-0 gap-4 text-sm font-medium text-sky-700">
          <Link to="/analytics" className="hover:underline">
            Аналитика
          </Link>
          <Link to="/dashboard" className="hover:underline">
            Источники данных →
          </Link>
        </nav>
      </header>

      <SearchBar
        value={input}
        onChange={setInput}
        onSubmit={() => runSearch(input)}
        suggestions={suggestionsQuery.data ?? []}
        onPick={pickSuggestion}
      />

      {!isSearching && (
        <div className="mt-8 space-y-4">
          <h2 className="text-sm font-medium uppercase tracking-wide text-slate-400">
            Примеры услуг
          </h2>
          <div className="space-y-3">
            {(featuredQuery.data ?? []).map((card) => (
              <PriceCard
                key={card.price_id}
                card={card}
                isCheapest={false}
                onOpenPassport={() => setPassport(card)}
              />
            ))}
          </div>
        </div>
      )}

      {isSearching && (
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

          {cards.length > 0 && hasMap && (
            <div className="flex gap-2 lg:hidden">
              {(["list", "map"] as const).map((view) => (
                <button
                  key={view}
                  type="button"
                  onClick={() => setMobileView(view)}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                    mobileView === view
                      ? "bg-teal-600 text-white"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {view === "list" ? "Список" : "Карта"}
                </button>
              ))}
            </div>
          )}

          <div className={`grid gap-6 ${hasMap ? "lg:grid-cols-2" : ""}`}>
            <div
              className={`space-y-3 ${
                hasMap && mobileView === "map" ? "hidden lg:block" : ""
              }`}
            >
              {cards.map((card) => (
                <div
                  key={card.price_id}
                  onMouseEnter={() => setSelectedId(card.price_id)}
                  className={`rounded-xl transition ${
                    selectedId === card.price_id ? "ring-2 ring-teal-500/60" : ""
                  }`}
                >
                  <PriceCard
                    card={card}
                    isCheapest={card.price_kzt === cheapestPrice}
                    onOpenPassport={() => setPassport(card)}
                  />
                </div>
              ))}
            </div>

            {hasMap && (
              <div className={mobileView === "list" ? "hidden lg:block" : ""}>
                <div className="sticky top-4 h-[60vh] lg:h-[72vh]">
                  <ClinicMap
                    cards={cards}
                    cheapestPrice={cheapestPrice}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                  />
                </div>
              </div>
            )}
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
