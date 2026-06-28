import { Search } from "lucide-react";

import type { Suggestion } from "@/types";

interface EmptyStateProps {
  query: string;
  suggestions: Suggestion[];
  onPickSuggestion: (suggestion: Suggestion) => void;
}

export function EmptyState({ query, suggestions, onPickSuggestion }: EmptyStateProps) {
  const didYouMean = suggestions.filter((s) => s.has_prices).slice(0, 3);

  return (
    <div className="flex min-h-[55vh] flex-col items-center justify-center px-4 text-center">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary">
        <Search className="h-6 w-6 text-faintest" />
      </div>
      <div className="mb-1 text-lg font-semibold text-foreground">
        По запросу «{query}» ничего не нашли
      </div>
      <div className="text-sm text-muted-foreground">Попробуйте уточнить услугу</div>

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
