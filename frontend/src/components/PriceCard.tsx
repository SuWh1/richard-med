import type { PriceCard as PriceCardData } from "@/types";
import { formatPrice } from "@/lib/format";
import { FreshnessBadge } from "./FreshnessBadge";

export function PriceCard({
  card,
  isCheapest,
  onOpenPassport,
}: {
  card: PriceCardData;
  isCheapest: boolean;
  onOpenPassport: () => void;
}) {
  return (
    <article className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-5 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="text-base font-semibold text-slate-900">
            {card.service_name}
          </span>
          {isCheapest && (
            <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-xs font-medium text-white">
              Лучшая цена
            </span>
          )}
        </div>
        {card.doctor_name && (
          <span className="text-sm font-medium text-slate-700">
            {card.doctor_name}
          </span>
        )}
        <span className="text-sm text-slate-500">
          {card.clinic_name}
          {(card.city || card.address) &&
            ` · ${[card.city, card.address].filter(Boolean).join(", ")}`}
        </span>
        <div className="mt-1">
          <FreshnessBadge freshness={card.freshness} ageDays={card.age_days} />
        </div>
      </div>

      <div className="flex items-center justify-between gap-4 sm:flex-col sm:items-end">
        <span className="text-3xl font-bold tracking-tight text-slate-900">
          {formatPrice(card.price_kzt)}
        </span>
        <button
          onClick={onOpenPassport}
          className="text-sm font-medium text-sky-600 hover:text-sky-700"
        >
          Паспорт цены →
        </button>
      </div>
    </article>
  );
}
