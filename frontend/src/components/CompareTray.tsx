import { Scale, X } from "lucide-react";

import type { PriceCard } from "@/types";
import { ClinicAvatar } from "./ClinicAvatar";

interface CompareTrayProps {
  clinics: Pick<PriceCard, "clinic_id" | "clinic_name">[];
  onRemove: (clinicId: number) => void;
  onClear: () => void;
  onCompare: () => void;
}

export function CompareTray({ clinics, onRemove, onClear, onCompare }: CompareTrayProps) {
  if (clinics.length === 0) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-white/95 shadow-[0_-4px_20px_rgba(0,0,0,0.06)] backdrop-blur">
      <div className="mx-auto flex w-full max-w-[1400px] flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center lg:px-6">
        <span className="flex items-center gap-1.5 text-sm font-semibold text-foreground">
          <Scale className="h-4 w-4 text-primary" /> Сравнение
        </span>
        <div className="flex flex-1 flex-wrap items-center gap-2">
          {clinics.map((c) => (
            <span
              key={c.clinic_id}
              className="flex items-center gap-1.5 rounded-full border border-border bg-secondary py-1 pl-1 pr-2 text-[11px]"
            >
              <ClinicAvatar name={c.clinic_name} size="sm" />
              <span className="max-w-[120px] truncate font-medium text-foreground">
                {c.clinic_name}
              </span>
              <button
                type="button"
                onClick={() => onRemove(c.clinic_id)}
                aria-label={`Убрать ${c.clinic_name} из сравнения`}
                className="text-muted-foreground transition-colors hover:text-danger"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </span>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onClear}
            className="shrink-0 text-[12px] text-muted-foreground transition-colors hover:text-foreground"
          >
            Очистить
          </button>
          <button
            type="button"
            onClick={onCompare}
            disabled={clinics.length < 2}
            className="flex-1 whitespace-nowrap rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50 sm:flex-none"
          >
            {clinics.length < 2 ? "Выберите ещё" : `Сравнить ${clinics.length} →`}
          </button>
        </div>
      </div>
    </div>
  );
}
