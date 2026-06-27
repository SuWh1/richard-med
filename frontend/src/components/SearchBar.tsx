import { useState } from "react";

import type { Suggestion } from "@/types";

export function SearchBar({
  value,
  onChange,
  onSubmit,
  suggestions,
  onPick,
}: {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  suggestions: Suggestion[];
  onPick: (s: Suggestion) => void;
}) {
  const [focused, setFocused] = useState(false);
  const showDropdown = focused && suggestions.length > 0;

  return (
    <div className="relative">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSubmit();
        }}
      >
        <input
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 150)}
          placeholder="Найдите услугу, например ОАК или приём терапевта"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-base shadow-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100"
        />
      </form>

      {showDropdown && (
        <ul className="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
          {suggestions.map((s) => (
            <li key={s.id}>
              <button
                onMouseDown={() => onPick(s)}
                className="flex w-full items-center justify-between px-4 py-2.5 text-left hover:bg-slate-50"
              >
                <span className="text-sm text-slate-800">{s.name_ru}</span>
                <span className="ml-3 shrink-0 text-xs text-slate-400">
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
