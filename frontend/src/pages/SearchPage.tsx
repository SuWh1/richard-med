import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import type { City, PriceCard as PriceCardData, SortKey, Suggestion } from "@/types";
import { fetchSearch, fetchSuggestions } from "@/lib/api";
import { useDebounce } from "@/hooks/useDebounce";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { HomeHero } from "@/components/HomeHero";
import { SearchBar } from "@/components/SearchBar";
import { SortControls } from "@/components/SortControls";
import { ClinicCard } from "@/components/ClinicCard";
import { PricePassport } from "@/components/PricePassport";
import { ClinicMap } from "@/components/map/ClinicMap";

export function SearchPage() {
  const [city, setCity] = useState<City>("Астана");
  const [input, setInput] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [sort, setSort] = useState<SortKey>("best_value");
  const [includeStale, setIncludeStale] = useState(false);
  const [passport, setPassport] = useState<PriceCardData | null>(null);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mobileView, setMobileView] = useState<"list" | "map">("list");

  const debounced = useDebounce(input, 250);
  const isSearching = submitted.trim().length >= 2;

  const suggestionsQuery = useQuery({
    queryKey: ["suggestions", debounced],
    queryFn: () => fetchSuggestions(debounced),
    enabled: debounced.trim().length >= 2,
  });

  const searchQuery = useQuery({
    queryKey: ["search", submitted, city, sort, includeStale],
    queryFn: () => fetchSearch({ q: submitted, city, sort, include_stale: includeStale }),
    enabled: isSearching,
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
    setSelectedId(null);
  };
  const pickSuggestion = (s: Suggestion) => runSearch(s.name_ru);

  const searchBar = (
    <SearchBar
      value={input}
      onChange={setInput}
      onSubmit={() => runSearch(input)}
      suggestions={suggestionsQuery.data ?? []}
      onPick={pickSuggestion}
    />
  );

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header city={city} onCityChange={setCity} />

      {!isSearching ? (
        <HomeHero city={city} searchBar={searchBar} onPickPopular={runSearch} />
      ) : (
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
          <div className="mb-6">{searchBar}</div>

          {searchQuery.data?.resolved_service && (
            <div className="mb-4 flex items-baseline justify-between">
              <h2 className="text-lg font-semibold text-foreground">
                {searchQuery.data.resolved_service.name_ru}
              </h2>
              <span className="text-sm text-muted-foreground">
                {searchQuery.data.count} предложений
              </span>
            </div>
          )}

          {cards.length > 0 && (
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <SortControls
                sort={sort}
                onChange={setSort}
                includeStale={includeStale}
                onToggleStale={setIncludeStale}
              />
              {hasMap && (
                <div className="flex gap-2 lg:hidden">
                  {(["list", "map"] as const).map((view) => (
                    <button
                      key={view}
                      type="button"
                      onClick={() => setMobileView(view)}
                      className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
                        mobileView === view
                          ? "bg-primary text-primary-foreground"
                          : "bg-secondary text-muted-foreground"
                      }`}
                    >
                      {view === "list" ? "Список" : "Карта"}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {searchQuery.isLoading && (
            <p className="text-sm text-muted-foreground">Загрузка…</p>
          )}
          {searchQuery.isError && (
            <p className="text-sm text-destructive">
              Не удалось загрузить цены. Попробуйте ещё раз.
            </p>
          )}
          {searchQuery.isSuccess && cards.length === 0 && (
            <p className="text-sm text-muted-foreground">
              По запросу «{submitted}» цены не найдены. Попробуйте уточнить услугу.
            </p>
          )}

          <div className={`grid gap-6 ${hasMap ? "lg:grid-cols-2" : ""}`}>
            <div
              className={`space-y-3 ${
                hasMap && mobileView === "map" ? "hidden lg:block" : ""
              }`}
            >
              {cards.map((card) => (
                <ClinicCard
                  key={card.price_id}
                  card={card}
                  isCheapest={card.price_kzt === cheapestPrice}
                  isHighlighted={selectedId === card.price_id}
                  onHover={setSelectedId}
                  onPassport={() => setPassport(card)}
                />
              ))}
            </div>

            {hasMap && (
              <div className={mobileView === "list" ? "hidden lg:block" : ""}>
                <div className="sticky top-20 h-[60vh] lg:h-[72vh]">
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
        </main>
      )}

      <Footer />
      <PricePassport card={passport} onClose={() => setPassport(null)} />
    </div>
  );
}
