import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Map as MapIcon, Search as SearchIcon } from "lucide-react";

import type { PriceCard as PriceCardData, Suggestion } from "@/types";
import { fetchCities, fetchMapPins, fetchSearch, fetchSuggestions } from "@/lib/api";
import { clinicPoints } from "@/lib/clinicPoints";
import {
  DEFAULT_CITY,
  type SearchState,
  useSearchState,
} from "@/hooks/useSearchState";
import { dedupePinsByLocation, medianPrice } from "@/lib/results";
import { distanceKm, nearestCity, sortByNearest } from "@/lib/geo";
import { useDebounce } from "@/hooks/useDebounce";
import { useUserLocation } from "@/hooks/useUserLocation";
import { Button } from "@/components/ui/button";
import { cn } from "@/components/ui/utils";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { AppShell } from "@/components/AppShell";
import { SearchBar } from "@/components/SearchBar";
import { ResultsControlsBar } from "@/components/results/ResultsControlsBar";
import { EmptyState } from "@/components/EmptyState";
import { ClinicCardSkeletonList } from "@/components/ClinicCardSkeleton";
import { ClinicCard } from "@/components/ClinicCard";
import { AnimatedList } from "@/components/AnimatedList";
import { PricePassport } from "@/components/PricePassport";
import { CompareTray } from "@/components/CompareTray";
import { ClinicMap } from "@/components/map/ClinicMap";
import { useCompareSelection } from "@/hooks/useCompareSelection";
import { buildCompareHref } from "@/lib/compare";

function toNum(value: string): number | undefined {
  if (!value) return undefined;
  const n = Number(value);
  return Number.isFinite(n) ? n : undefined;
}

export function ResultsPage() {
  const { state, update } = useSearchState();
  const navigate = useNavigate();
  const [rawParams] = useSearchParams();
  const { coords, request: requestLocation } = useUserLocation();
  const appliedGeoCity = useRef(false);

  const [input, setInput] = useState(state.q);
  const [selectedBranchId, setSelectedBranchId] = useState<number | null>(null);
  const [passport, setPassport] = useState<PriceCardData | null>(null);
  const [mapOpen, setMapOpen] = useState(false);

  const debounced = useDebounce(input, 250);
  const listRef = useRef<HTMLDivElement>(null);
  const scrollOnSelect = useRef(false);

  useEffect(() => setInput(state.q), [state.q]);

  const isSearching = state.q.trim().length >= 2;

  const citiesQuery = useQuery({ queryKey: ["cities"], queryFn: fetchCities });
  const cities = citiesQuery.data ?? [];
  const cityNames = cities.length ? cities.map((c) => c.name) : ["Астана", "Алматы"];
  const cityCenter = useMemo<[number, number] | null>(() => {
    const found = cities.find((c) => c.name === state.city);
    return found ? [found.lat, found.lng] : null;
  }, [cities, state.city]);

  useEffect(() => {
    if (appliedGeoCity.current || !coords || cities.length === 0) return;
    appliedGeoCity.current = true;
    if (rawParams.get("city")) return;
    const near = nearestCity(coords, cities);
    if (near && near.name !== state.city) update({ city: near.name }, { replace: true });
  }, [coords, cities, rawParams, state.city, update]);

  const suggestionsQuery = useQuery({
    queryKey: ["suggestions", debounced],
    queryFn: () => fetchSuggestions(debounced),
    enabled: debounced.trim().length >= 2,
  });

  // "nearest" is sorted client-side from coords; the backend only knows best_value/cheapest/newest.
  const backendSort = state.sort === "nearest" ? "best_value" : state.sort;
  // Round coords (~100m) so the clinic card binds to the user's nearest branch
  // without refetching on every GPS jitter.
  const geo = coords
    ? { lat: Math.round(coords.lat * 1000) / 1000, lng: Math.round(coords.lng * 1000) / 1000 }
    : null;

  const searchQuery = useQuery({
    queryKey: [
      "search",
      state.q,
      state.city,
      backendSort,
      state.includeStale,
      state.priceMin,
      state.priceMax,
      geo?.lat ?? null,
      geo?.lng ?? null,
    ],
    queryFn: () =>
      fetchSearch({
        q: state.q,
        city: state.city,
        sort: backendSort,
        include_stale: state.includeStale,
        price_min: toNum(state.priceMin),
        price_max: toNum(state.priceMax),
        lat: geo?.lat,
        lng: geo?.lng,
      }),
    enabled: isSearching,
  });

  const cards = useMemo(() => {
    const base = searchQuery.data?.cards ?? [];
    return state.sort === "nearest" && coords ? sortByNearest(base, coords) : base;
  }, [searchQuery.data, state.sort, coords]);
  const median = useMemo(() => medianPrice(cards.map((c) => c.price_kzt)), [cards]);
  const cheapestPrice = useMemo(
    () => (cards.length ? Math.min(...cards.map((c) => c.price_kzt)) : null),
    [cards],
  );
  const resolved = searchQuery.data?.resolved_service ?? null;
  const resolvedId = resolved?.id ?? null;

  const compare = useCompareSelection(resolvedId);
  const compareClinics = useMemo(() => {
    const byId = new Map(cards.map((c) => [c.clinic_id, c]));
    return compare.selected
      .map((id) => byId.get(id))
      .filter((c): c is PriceCardData => c != null)
      .map((c) => ({ clinic_id: c.clinic_id, clinic_name: c.clinic_name }));
  }, [cards, compare.selected]);

  const openCompare = () => {
    if (resolvedId == null || compare.selected.length < 2) return;
    navigate(buildCompareHref(resolvedId, compare.selected, state.city), {
      state: { q: state.q, city: state.city, label: resolved?.name_ru },
    });
  };

  const mapQuery = useQuery({
    queryKey: ["map-pins", resolvedId, state.city],
    queryFn: () => fetchMapPins(resolvedId as number, state.city),
    enabled: isSearching && resolvedId !== null,
  });
  const pins = useMemo(() => dedupePinsByLocation(mapQuery.data ?? []), [mapQuery.data]);
  const hasMap = pins.length > 0;

  // A card binds to its clinic's nearest branch, but a map pin can be any branch — so
  // resolve the selected branch back to its clinic to highlight/scroll the right card.
  const selectedClinicId = useMemo(
    () => pins.find((p) => p.branch_id === selectedBranchId)?.clinic_id ?? null,
    [pins, selectedBranchId],
  );

  useEffect(() => {
    if (!scrollOnSelect.current || selectedClinicId == null) return;
    scrollOnSelect.current = false;
    listRef.current
      ?.querySelector(`[data-clinic-id="${selectedClinicId}"]`)
      ?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [selectedClinicId]);

  const runSearch = (q: string) => {
    if (q.trim().length < 2) return;
    setSelectedBranchId(null);
    update({ q: q.trim(), priceMin: "", priceMax: "" }, { replace: false });
  };
  const pickSuggestion = (s: Suggestion) => runSearch(s.name_ru);

  const patch = (p: Partial<SearchState>) => {
    setSelectedBranchId(null);
    if (p.sort === "nearest" && !coords) requestLocation();
    update(p, { replace: true });
  };
  const resetFilters = () =>
    patch({ city: DEFAULT_CITY, priceMin: "", priceMax: "", includeStale: false });

  const selectFromMap = (branchId: number | null) => {
    scrollOnSelect.current = true;
    setSelectedBranchId(branchId);
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

  const firstCardPoint = useMemo<[number, number] | null>(() => {
    const first = cards.find((c) => c.lat != null && c.lng != null);
    return first ? [first.lat as number, first.lng as number] : null;
  }, [cards]);

  const mapEl = (overlay: boolean) => (
    <div className="relative h-full">
      <ClinicMap
        pins={pins}
        selectedBranchId={selectedBranchId}
        onSelectBranch={overlay ? setSelectedBranchId : selectFromMap}
        center={cityCenter}
        median={median}
        userCoords={coords}
        focusPoint={overlay ? firstCardPoint : null}
      />
    </div>
  );

  return (
    <AppShell
      city={state.city}
      breadcrumb={[
        { label: "Поиск", href: "/search" },
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
        <div
          ref={listRef}
          className={cn(
            "w-full p-4 lg:p-5",
            hasMap && "lg:w-[58%]",
            compareClinics.length > 0 && "pb-24",
          )}
        >
          {!isSearching && (
            <div className="flex min-h-[55vh] flex-col items-center justify-center px-4 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary">
                <SearchIcon className="h-6 w-6 text-faintest" />
              </div>
              <div className="mb-1 text-lg font-semibold text-foreground">
                Найдите медицинскую услугу
              </div>
              <div className="text-sm text-muted-foreground">
                Введите название услуги в поиске сверху
              </div>
            </div>
          )}

          {searchQuery.isLoading && <ClinicCardSkeletonList count={5} />}

          {searchQuery.isError && (
            <div className="rounded-xl border border-danger/30 bg-card p-6 text-center shadow-sm">
              <p className="mb-2 text-sm font-semibold text-foreground">
                Не удалось загрузить клиники
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
            />
          )}

          <AnimatedList className="space-y-3">
            {cards.map((card) => (
              <div
                key={`${card.price_id}-${card.branch_id ?? "c"}`}
                data-clinic-id={card.clinic_id}
              >
                <ClinicCard
                  card={card}
                  isCheapest={card.price_kzt === cheapestPrice}
                  median={median}
                  isHighlighted={selectedClinicId === card.clinic_id}
                  userCoords={coords}
                  distanceKm={coords ? distanceKm(coords, card) : null}
                  points={clinicPoints(pins, card.clinic_id, coords)}
                  onPointHover={(branchId) => setSelectedBranchId(branchId)}
                  onHover={() => setSelectedBranchId(card.branch_id)}
                  onPassport={() => setPassport(card)}
                  onDetail={() =>
                    navigate(`/clinics/${card.clinic_id}`, {
                      state: { q: state.q, city: state.city, label: resolved?.name_ru },
                    })
                  }
                  inCompare={compare.isSelected(card.clinic_id)}
                  onCompare={
                    compare.isSelected(card.clinic_id) || !compare.isFull
                      ? () => compare.toggle(card.clinic_id)
                      : undefined
                  }
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
          className={cn(
            "fixed left-1/2 z-40 -translate-x-1/2 gap-2 rounded-full shadow-lg lg:hidden",
            compareClinics.length > 0 ? "bottom-24" : "bottom-5",
          )}
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

      <CompareTray
        clinics={compareClinics}
        onRemove={compare.toggle}
        onClear={compare.clear}
        onCompare={openCompare}
      />
    </AppShell>
  );
}
