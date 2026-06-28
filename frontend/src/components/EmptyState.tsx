import { Search } from "lucide-react";

import type { CityCount, Suggestion } from "@/types";

interface EmptyStateProps {
  query: string;
  suggestions: Suggestion[];
  currentCity?: string;
  otherCities?: CityCount[];
  onPickCity?: (city: string) => void;
  onPickSuggestion: (suggestion: Suggestion) => void;
}

export function EmptyState({
  query,
  suggestions,
  currentCity,
  otherCities = [],
  onPickCity,
  onPickSuggestion,
}: EmptyStateProps) {
  const didYouMean = suggestions.filter((s) => s.has_prices).slice(0, 3);
  const cityHints = otherCities.slice(0, 4);

  return (
    <div className="flex min-h-[55vh] flex-col items-center justify-center px-4 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary">
        <Search className="h-6 w-6 text-faintest" />
      </div>
      <div className="mb-1 text-lg font-semibold text-foreground">
        По запросу «{query}» ничего не нашли
      </div>
      <div className="text-sm text-muted-foreground">Попробуйте уточнить услугу</div>

      {cityHints.length > 0 && (
        <div className="mt-5 max-w-xl rounded-xl border border-border bg-white p-4 text-sm shadow-sm">
          <div className="font-medium text-foreground">
            {currentCity ? `В городе ${currentCity} свежих цен нет` : "Свежих цен нет"}
          </div>
          <div className="mt-1 text-muted-foreground">
            Но эта услуга есть в других городах:
          </div>
          <div className="mt-3 flex flex-wrap justify-center gap-2">
            {cityHints.map((city) => (
              <button
                key={city.name}
                type="button"
                onClick={() => onPickCity?.(city.name)}
                className="rounded-full border border-primary/30 px-3 py-1.5 text-xs font-medium text-primary transition-colors hover:border-primary hover:bg-accent/40"
              >
                {city.name} · {city.count}
              </button>
            ))}
          </div>
        </div>
      )}

      {didYouMean.length > 0 && (
        <div className="mt-5 text-sm text-muted-foreground">
          Возможно, вы имели в виду:{" "}
          {didYouMean.map((s, i) => (
            <span key={s.id}>
              {i > 0 && ", "}
              <button
                type="button"
                onClick={() => onPickSuggestion(s)}
                className="font-medium text-primary hover:underline"
              >
                {s.name_ru}
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
