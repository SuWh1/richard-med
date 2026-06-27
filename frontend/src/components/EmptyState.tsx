import { Search } from "lucide-react";

import type { Suggestion } from "@/types";
import { POPULAR_SERVICES } from "@/lib/constants";

interface EmptyStateProps {
  query: string;
  suggestions: Suggestion[];
  onPickSuggestion: (suggestion: Suggestion) => void;
  onPickPopular: (query: string) => void;
}

export function EmptyState({
  query,
  suggestions,
  onPickSuggestion,
  onPickPopular,
}: EmptyStateProps) {
  const didYouMean = suggestions.filter((s) => s.has_prices).slice(0, 3);

  return (
    <div className="rounded-xl border border-border bg-white p-8 text-center shadow-sm">
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary">
        <Search className="h-5 w-5 text-faintest" />
      </div>
      <div className="mb-1 font-semibold text-foreground">
        По запросу «{query}» ничего не нашли
      </div>
      <div className="mb-4 text-sm text-muted-foreground">
        Попробуйте уточнить услугу
      </div>

      <div className="mb-4 flex flex-wrap justify-center gap-2">
        {POPULAR_SERVICES.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onPickPopular(s)}
            className="rounded-full border border-border bg-background px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/50 hover:text-primary"
          >
            {s}
          </button>
        ))}
      </div>

      {didYouMean.length > 0 && (
        <div className="text-xs text-muted-foreground">
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
