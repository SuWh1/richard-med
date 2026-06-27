import { SlidersHorizontal } from "lucide-react";

import type { SearchState } from "@/hooks/useSearchState";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { FilterControls } from "./FilterControls";

interface FiltersSheetProps {
  state: SearchState;
  cities: string[];
  onPatch: (patch: Partial<SearchState>) => void;
  onReset: () => void;
  activeCount: number;
}

export function FiltersSheet({
  state,
  cities,
  onPatch,
  onReset,
  activeCount,
}: FiltersSheetProps) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5">
          <SlidersHorizontal className="h-4 w-4" />
          Фильтры
          {activeCount > 0 && (
            <span className="ml-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground">
              {activeCount}
            </span>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="mx-auto max-w-lg rounded-t-2xl">
        <SheetHeader>
          <SheetTitle>Фильтры</SheetTitle>
        </SheetHeader>
        <div className="px-4">
          <FilterControls state={state} cities={cities} onPatch={onPatch} />
        </div>
        <SheetFooter className="flex-row gap-3">
          <Button variant="outline" className="flex-1" onClick={onReset}>
            Сбросить
          </Button>
          <SheetClose asChild>
            <Button className="flex-1">Готово</Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
