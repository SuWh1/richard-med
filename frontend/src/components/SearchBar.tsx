import { useState } from "react";
import { Search } from "lucide-react";

import type { Suggestion } from "@/types";
import { cn } from "@/components/ui/utils";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  suggestions: Suggestion[];
  onPick: (suggestion: Suggestion) => void;
}

export function SearchBar({ value, onChange, onSubmit, suggestions, onPick }: SearchBarProps) {
  const [focused, setFocused] = useState(false);
  const showDropdown = focused && suggestions.length > 0;

  return (
    <div className="relative">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
        className={cn(
          "flex items-center gap-3 rounded-2xl border-2 bg-white px-4 py-3 shadow-sm transition-all",
          focused ? "border-primary shadow-lg" : "border-border hover:border-primary/50",
        )}
      >
        <Search className="h-5 w-5 shrink-0 text-primary" />
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 180)}
          placeholder="Введите услугу: ОАК, УЗИ, терапевт..."
          className="flex-1 bg-transparent text-base text-foreground outline-none placeholder:text-[#CBD5E1]"
        />
        <button
          type="submit"
          className="min-h-[36px] shrink-0 rounded-xl bg-primary px-5 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-[#0b8a7a]"
        >
          Найти
        </button>
      </form>

      {showDropdown && (
        <ul className="absolute left-0 right-0 top-full z-20 mt-2 overflow-hidden rounded-xl border border-border bg-white shadow-xl">
          {suggestions.map((s) => (
            <li key={s.id}>
              <button
                type="button"
                onMouseDown={() => onPick(s)}
                className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-secondary"
              >
                <span className="flex items-center gap-3">
                  <Search className="h-4 w-4 text-[#CBD5E1]" />
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
