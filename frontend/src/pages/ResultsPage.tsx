import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Map as MapIcon } from "lucide-react";

import type { PriceCard as PriceCardData, Suggestion } from "@/types";
import { fetchCities, fetchMapPins, fetchSearch, fetchSuggestions } from "@/lib/api";
import {
  DEFAULT_CITY,
  type SearchState,
  useSearchState,
} from "@/hooks/useSearchState";
import { dedupePinsByLocation, medianPrice } from "@/lib/results";
import { useDebounce } from "@/hooks/useDebounce";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { AppShell } from "@/components/AppShell";
import { SearchBar } from "@/components/SearchBar";
import { ResultsControlsBar } from "@/components/results/ResultsControlsBar";
import { EmptyState } from "@/components/EmptyState";
import { ClinicCardSkeletonList } from "@/components/ClinicCardSkeleton";
import { ClinicCard } from "@/components/ClinicCard";
import { AnimatedList } from "@/components/AnimatedList";
import { PricePassport } from "@/components/PricePassport";
import { ClinicMap } from "@/components/map/ClinicMap";

function toNum(value: string): number | undefined {
  if (!value) return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

export function ResultsPage() {
  const { state, update } = useSearchState();
  const navigate = useNavigate();

  const [input, setInput] = useState(state.q);
  const [selectedClinicId, setSelectedClinicId] = useState<number | null>(null);
  const [passport, setPassport] = useState<PriceCardData | null>(null);
  const [mapOpen, setMapOpen] = useState(false);

  const debounced = useDebounce(input, 250);
  const listRef = useRef<HTMLDivElement>(null);
  const scrollOnSelect = useRef(false);

  useEffect(() => setInput(state.q), [state.q]);

  const isSearching = state.q.trim().length >= 2;
  useEffect(() => {
    if (!isSearching) navigate("/", { replace: true });
  }, [isSearching, navigate]);

  const citiesQuery = useQuery({ queryKey: ["cities"], queryFn: fetchCities });
  const cities = citiesQuery.data ?? [];
  const cityNames = cities.length ? cities.map((c) => c.name) : ["Астана", "Алматы"];
  const cityCenter = useMemo<[number, number] | null>(() => {
    const found = cities.find((c) => c.name === state.city);
    return found ? [found.lat, found.lng] : null;
  }, [cities, state.city]);

  const suggestionsQuery = useQuery({
    queryKey: ["suggestions", debounced],
    queryFn: () => fetchSuggestions(debounced),
    enabled: debounced.trim().length >= 2,
  });

  const searchQuery = useQuery({
    queryKey: [
      "search",
      state.q,
      state.city,
      state.sort,
      state.includeStale,
      state.priceMin,
      state.priceMax,
    ],
    queryFn: () =>
      fetchSearch({
        q: state.q,
        city: state.city,
        sort: state.sort,
        include_stale: state.includeStale,
        price_min: toNum(state.priceMin),
        price_max: toNum(state.priceMax),
      }),
    enabled: isSearching,
  });

  const cards = searchQuery.data?.cards ?? [];
  const median = useMemo(() => medianPrice(cards.map((c) => c.price_kzt)), [cards]);
  const cheapestPrice = useMemo(
    () => (cards.length ? Math.min(...cards.map((c) => c.price_kzt)) : null),
    [cards],
  );
  const resolved = searchQuery.data?.resolved_service ?? null;
  const resolvedId = resolved?.id ?? null;

  const mapQuery = useQuery({
    queryKey: ["map-pins", resolvedId, state.city],
    queryFn: () => fetchMapPins(resolvedId as number, state.city),
    enabled: isSearching && resolvedId !== null,
  });
  const pins = useMemo(() => dedupePinsByLocation(mapQuery.data ?? []), [mapQuery.data]);
  const hasMap = pins.length > 0;

  useEffect(() => {
    if (!scrollOnSelect.current || selectedClinicId == null) return;
    scrollOnSelect.current = false;
    listRef.current
      ?.querySelector(`[data-clinic-id="${selectedClinicId}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [selectedClinicId]);

  const runSearch = (q: string) => {
    if (q.trim().length < 2) return;
    setSelectedClinicId(null);
    update({ q: q.trim(), priceMin: "", priceMax: "" }, { replace: false });
  };
  const pickSuggestion = (s: Suggestion) => runSearch(s.name_ru);

  const patch = (p: Partial<SearchState>) => {
    setSelectedClinicId(null);
    update(p, { replace: true });
  };
  const resetFilters = () =>
    patch({ city: DEFAULT_CITY, priceMin: "", priceMax: "", includeStale: false });

  const selectFromMap = (clinicId: number | null) => {
    scrollOnSelect.current = true;
    setSelectedClinicId(clinicId);
  };

  const searchBar = (
    <SearchBar
      variant="compact"
      value={input}
      onChange={setInput}
      onSubmit={() => runSearch(input)}
      suggestions={suggestionsQuery.data ?? []}
      onPick={pickSuggestion}
    />
  );

  const mapEl = (overlay: boolean) => (
    <div className="relative h-full">
      <ClinicMap
        pins={pins}
        selectedClinicId={selectedClinicId}
        onSelectClinic={overlay ? setSelectedClinicId : selectFromMap}
        center={cityCenter}
        median={median}
      />
    </div>
  );

  return (
    <AppShell
      city={state.city}
      breadcrumb={[
        { label: "Поиск" },
        { label: resolved?.name_ru ?? "Результаты" },
      ]}
    >
      <ResultsControlsBar
        searchBar={searchBar}
        state={state}
        cities={cityNames}
        onPatch={patch}
        onReset={resetFilters}
        count={searchQuery.data?.count ?? cards.length}
      />

      <div className="mx-auto flex w-full max-w-[1400px] flex-1">
        <div ref={listRef} className="w-full p-4 lg:w-[58%] lg:p-5">
          {searchQuery.isLoading && <ClinicCardSkeletonList count={5} />}

          {searchQuery.isError && (
            <div className="rounded-xl border border-danger/30 bg-card p-6 text-center shadow-sm">
              <p className="mb-2 text-sm font-semibold text-foreground">
                Не удалось загрузить цены
              </p>
              <Button variant="link" onClick={() => searchQuery.refetch()}>
                Повторить
              </Button>
            </div>
          )}

          {searchQuery.isSuccess && cards.length === 0 && (
            <EmptyState
              query={state.q}
              suggestions={searchQuery.data?.suggestions ?? []}
              onPickSuggestion={pickSuggestion}
              onPickPopular={runSearch}
            />
          )}

          <AnimatedList className="space-y-3">
            {cards.map((card) => (
              <div key={card.price_id} data-clinic-id={card.clinic_id}>
                <ClinicCard
                  card={card}
                  isCheapest={card.price_kzt === cheapestPrice}
                  median={median}
                  isHighlighted={selectedClinicId === card.clinic_id}
                  onHover={() => setSelectedClinicId(card.clinic_id)}
                  onPassport={() => setPassport(card)}
                  onDetail={() => navigate(`/clinics/${card.clinic_id}`)}
                />
              </div>
            ))}
          </AnimatedList>
        </div>

        {hasMap && (
          <div className="hidden lg:block lg:w-[42%]">
            <div className="sticky top-[6rem] h-[calc(100svh-10.5rem)] p-4 pl-0">
              {mapEl(false)}
            </div>
          </div>
        )}
      </div>

      {/* Mobile map trigger */}
      {hasMap && (
        <Button
          onClick={() => setMapOpen(true)}
          className="fixed bottom-5 left-1/2 z-40 -translate-x-1/2 gap-2 rounded-full shadow-lg lg:hidden"
        >
          <MapIcon className="h-4 w-4" /> Карта · {pins.length}
        </Button>
      )}

      <Sheet open={mapOpen} onOpenChange={setMapOpen}>
        <SheetContent side="bottom" className="h-[88vh] rounded-t-2xl p-0">
          <SheetHeader className="border-b border-border">
            <SheetTitle>Клиники на карте</SheetTitle>
          </SheetHeader>
          <div className="h-[calc(88vh-3.5rem)] p-3">{mapEl(true)}</div>
        </SheetContent>
      </Sheet>

      <PricePassport card={passport} onClose={() => setPassport(null)} />
    </AppShell>
  );
}
