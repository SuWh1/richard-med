import { useState } from "react";
import { Search, X } from "lucide-react";

import type { Suggestion } from "@/types";
import { cn } from "@/components/ui/utils";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  suggestions: Suggestion[];
  onPick: (suggestion: Suggestion) => void;
  variant?: "hero" | "compact";
}

export function SearchBar({
  value,
  onChange,
  onSubmit,
  suggestions,
  onPick,
  variant = "hero",
}: SearchBarProps) {
  const [focused, setFocused] = useState(false);
  // Only services with prices are useful picks — never suggest dead-end "нет цен" rows.
  const shown = suggestions.filter((s) => s.has_prices);
  const showDropdown = focused && shown.length > 0;
  const compact = variant === "compact";

  return (
    <div className="relative">
      {!compact && (
        <div
          aria-hidden
          className={cn(
            "pointer-events-none absolute -inset-3 -z-10 rounded-[1.75rem] bg-gradient-to-r from-primary/30 via-sky-300/25 to-violet-300/25 blur-2xl transition-opacity duration-500",
            focused ? "opacity-90" : "opacity-50",
          )}
        />
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
        className={cn(
          "relative flex items-center bg-white transition-all duration-300",
          compact
            ? "gap-2 rounded-lg border border-border px-3 py-1.5 focus-within:border-primary"
            : cn(
                "gap-3 rounded-2xl border px-4 py-3.5 shadow-sm",
                focused
                  ? "border-primary shadow-xl ring-4 ring-primary/15"
                  : "border-border hover:border-primary/50 hover:shadow-md",
              ),
        )}
      >
        <Search
          className={cn(
            "shrink-0",
            compact ? "h-4 w-4 text-faint" : "h-5 w-5 text-primary",
          )}
        />
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 180)}
          placeholder="Введите услугу: ОАК, УЗИ, терапевт..."
          className={cn(
            "flex-1 bg-transparent text-foreground outline-none placeholder:text-faintest",
            compact ? "text-sm" : "text-base",
          )}
        />
        {value && (
          <button
            type="button"
            aria-label="Очистить"
            onMouseDown={(e) => e.preventDefault()}
            onClick={() => onChange("")}
            className="flex shrink-0 items-center justify-center rounded-full bg-secondary p-1 text-muted-foreground transition-colors hover:bg-border hover:text-foreground"
          >
            <X className={compact ? "h-3.5 w-3.5" : "h-4 w-4"} />
          </button>
        )}
        {!compact && (
          <button
            type="submit"
            className="min-h-[36px] shrink-0 rounded-xl bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary-hover"
          >
            Найти
          </button>
        )}
      </form>

      {showDropdown && (
        <ul className="absolute left-0 right-0 top-full z-30 mt-2 overflow-hidden rounded-xl border border-border bg-white shadow-xl motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-top-1 motion-safe:duration-150">
          {shown.map((s) => (
            <li key={s.id}>
              <button
                type="button"
                onMouseDown={() => onPick(s)}
                className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-secondary"
              >
                <span className="flex items-center gap-3">
                  <Search className="h-4 w-4 text-faintest" />
                  <span className="text-sm text-foreground">{s.name_ru}</span>
                  {s.specialty && (
                    <span className="text-xs text-[#CBD5E1]">· {s.specialty}</span>
                  )}
                </span>
                <span className="shrink-0 rounded-full bg-secondary px-2 py-0.5 text-[11px] text-muted-foreground">
                  {s.has_prices ? s.category : "нет цен"}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
