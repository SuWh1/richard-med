import { useEffect, useState } from "react";

import type { SearchState } from "@/hooks/useSearchState";
import type { SortKey } from "@/types";
import { cn } from "@/components/ui/utils";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const SORTS: { key: SortKey; label: string }[] = [
  { key: "best_value", label: "Оптимальные" },
  { key: "cheapest", label: "Дешёвые" },
  { key: "newest", label: "Свежие" },
];

interface FilterControlsProps {
  state: SearchState;
  cities: string[];
  onPatch: (patch: Partial<SearchState>) => void;
}

export function FilterControls({ state, cities, onPatch }: FilterControlsProps) {
  const [min, setMin] = useState(state.priceMin);
  const [max, setMax] = useState(state.priceMax);

  useEffect(() => setMin(state.priceMin), [state.priceMin]);
  useEffect(() => setMax(state.priceMax), [state.priceMax]);

  const applyPrice = () => onPatch({ priceMin: min, priceMax: max });

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <Label>Сортировка</Label>
        <div className="grid grid-cols-3 gap-1 rounded-lg bg-muted p-1">
          {SORTS.map((opt) => (
            <button
              key={opt.key}
              type="button"
              onClick={() => onPatch({ sort: opt.key })}
              className={cn(
                "rounded-md px-2 py-2 text-sm font-medium transition-colors",
                state.sort === opt.key
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground",
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label>Город</Label>
        <Select value={state.city} onValueChange={(city) => onPatch({ city })}>
          <SelectTrigger className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="max-h-72">
            {cities.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Цена, ₸</Label>
        <div className="flex items-center gap-2">
          <Input
            inputMode="numeric"
            placeholder="от 0"
            value={min}
            onChange={(e) => setMin(e.target.value)}
            onBlur={applyPrice}
            onKeyDown={(e) => e.key === "Enter" && applyPrice()}
          />
          <span className="text-muted-foreground">–</span>
          <Input
            inputMode="numeric"
            placeholder="до ∞"
            value={max}
            onChange={(e) => setMax(e.target.value)}
            onBlur={applyPrice}
            onKeyDown={(e) => e.key === "Enter" && applyPrice()}
          />
        </div>
      </div>

      <div className="flex items-center justify-between gap-3">
        <Label htmlFor="stale-toggle" className="cursor-pointer leading-tight">
          Показывать устаревшие цены
          <span className="mt-0.5 block text-[11px] font-normal text-muted-foreground">
            Старше 30 дней — могут быть неактуальны. По умолчанию скрыты.
          </span>
        </Label>
        <Switch
          id="stale-toggle"
          checked={state.includeStale}
          onCheckedChange={(v) => onPatch({ includeStale: v })}
        />
      </div>
    </div>
  );
}
