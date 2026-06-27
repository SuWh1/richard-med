import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import type { PriceCard as PriceCardData, SortKey, Suggestion } from "@/types";
import { fetchCities, fetchMapPins, fetchSearch, fetchSuggestions } from "@/lib/api";
import { buildCompareHref } from "@/lib/compare";
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
  const [city, setCity] = useState("Астана");
  const [input, setInput] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [sort, setSort] = useState<SortKey>("best_value");
  const [includeStale, setIncludeStale] = useState(false);
  const [passport, setPassport] = useState<PriceCardData | null>(null);
  const [selectedClinicId, setSelectedClinicId] = useState<number | null>(null);
  const [mobileView, setMobileView] = useState<"list" | "map">("list");
  const [compareIds, setCompareIds] = useState<number[]>([]);

  const navigate = useNavigate();
  const debounced = useDebounce(input, 250);
  const isSearching = submitted.trim().length >= 2;

  const citiesQuery = useQuery({ queryKey: ["cities"], queryFn: fetchCities });
  const cities = citiesQuery.data ?? [];
  const cityNames = cities.length ? cities.map((c) => c.name) : ["Астана", "Алматы"];
  const cityCenter = useMemo<[number, number] | null>(() => {
    const found = cities.find((c) => c.name === city);
    return found ? [found.lat, found.lng] : null;
  }, [cities, city]);

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
  const resolvedId = searchQuery.data?.resolved_service?.id ?? null;

  const mapQuery = useQuery({
    queryKey: ["map-pins", resolvedId, city],
    queryFn: () => fetchMapPins(resolvedId as number, city),
    enabled: isSearching && resolvedId !== null,
  });
  const pins = mapQuery.data ?? [];
  const hasMap = pins.length > 0;

  const runSearch = (q: string) => {
    setInput(q);
    setSubmitted(q);
    setSelectedClinicId(null);
    setCompareIds([]);
  };
  const pickSuggestion = (s: Suggestion) => runSearch(s.name_ru);

  const toggleCompare = (clinicId: number) =>
    setCompareIds((ids) =>
      ids.includes(clinicId) ? ids.filter((i) => i !== clinicId) : [...ids, clinicId],
    );

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
      <Header city={city} onCityChange={setCity} cities={cityNames} />

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
                  isHighlighted={selectedClinicId === card.clinic_id}
                  onHover={() => setSelectedClinicId(card.clinic_id)}
                  onPassport={() => setPassport(card)}
                  onCompare={() => toggleCompare(card.clinic_id)}
                  onDetail={() => navigate(`/clinics/${card.clinic_id}`)}
                  inCompare={compareIds.includes(card.clinic_id)}
                />
              ))}
            </div>

            {hasMap && (
              <div className={mobileView === "list" ? "hidden lg:block" : ""}>
                <div className="sticky top-20 h-[60vh] lg:h-[72vh]">
                  <ClinicMap
                    pins={pins}
                    selectedClinicId={selectedClinicId}
                    onSelectClinic={setSelectedClinicId}
                    center={cityCenter}
                  />
                </div>
              </div>
            )}
          </div>
        </main>
      )}

      {compareIds.length >= 2 && resolvedId !== null && (
        <div className="sticky bottom-4 z-40 mx-auto flex w-fit items-center gap-3 rounded-full border border-border bg-white px-5 py-2.5 shadow-lg">
          <span className="text-sm text-muted-foreground">
            Выбрано клиник: {compareIds.length}
          </span>
          <button
            type="button"
            onClick={() => navigate(buildCompareHref(resolvedId, compareIds))}
            className="rounded-full bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground transition hover:bg-[#0b8a7a]"
          >
            Сравнить выбранные
          </button>
        </div>
      )}

      <Footer />
      <PricePassport card={passport} onClose={() => setPassport(null)} />
    </div>
  );
}
