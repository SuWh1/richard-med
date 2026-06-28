import { type MouseEvent } from "react";
import { Link } from "react-router-dom";
import { Briefcase, Info, Navigation, Star } from "lucide-react";

import type { PriceCard as PriceCardData } from "@/types";
import { formatPrice } from "@/lib/format";
import { discountPct } from "@/lib/results";
import { cn } from "@/components/ui/utils";
import { ClinicAvatar } from "./ClinicAvatar";
import { StatusBadge } from "./StatusBadge";

function experienceLabel(years: number): string {
  const mod10 = years % 10;
  const mod100 = years % 100;
  if (mod10 === 1 && mod100 !== 11) return `${years} год опыта`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20))
    return `${years} года опыта`;
  return `${years} лет опыта`;
}

interface ClinicCardProps {
  card: PriceCardData;
  isCheapest: boolean;
  isHighlighted: boolean;
  median: number | null;
  onHover: (priceId: number | null) => void;
  onPassport: () => void;
  onDetail?: () => void;
}

function durationLabel(min: number | null, max: number | null): string | null {
  if (min == null && max == null) return null;
  if (min != null && max != null && min !== max) return `${min}–${max} дн.`;
  return `${max ?? min} дн.`;
}

function routeUrl(card: PriceCardData): string {
  if (card.lat != null && card.lng != null) {
    return `https://www.google.com/maps/dir/?api=1&destination=${card.lat},${card.lng}`;
  }
  const q = encodeURIComponent([card.city, card.address].filter(Boolean).join(", "));
  return `https://www.google.com/maps/search/?api=1&query=${q}`;
}

export function ClinicCard({
  card,
  isCheapest,
  isHighlighted,
  median,
  onHover,
  onPassport,
  onDetail,
}: ClinicCardProps) {
  const duration = durationLabel(card.duration_min, card.duration_max);
  const belowMedianPct = median != null ? discountPct(card.price_kzt, median) : 0;
  const stop = (e: MouseEvent) => e.stopPropagation();

  return (
    <div
      onMouseEnter={() => onHover(card.price_id)}
      onClick={onDetail}
      role={onDetail ? "button" : undefined}
      className={cn(
        "rounded-xl border bg-white p-5 transition-all duration-150",
        onDetail && "cursor-pointer",
        isHighlighted
          ? "border-primary shadow-md"
          : "border-border shadow-sm hover:border-primary/40 hover:shadow-md",
      )}
    >
      {isCheapest && (
        <div className="mb-3 flex items-center gap-1.5 border-b border-secondary pb-3 text-[11px] font-semibold text-primary">
          <Star className="h-3.5 w-3.5 fill-primary" /> Оптимальный выбор
        </div>
      )}

      <div className="flex items-start gap-3">
        <ClinicAvatar name={card.clinic_name} />
        <div className="min-w-0 flex-1">
          <div className="mb-0.5 flex items-start justify-between gap-2">
            <div className="min-w-0">
              <div className="truncate text-sm font-semibold text-foreground">
                {card.clinic_name}
              </div>
              <div className="truncate text-[11px] text-muted-foreground">
                {card.address ?? card.city ?? ""}
              </div>
            </div>
            <div className="shrink-0 text-right">
              <div className="text-[26px] font-bold leading-none text-foreground">
                {formatPrice(card.price_kzt)}
              </div>
              {isCheapest ? (
                <div className="mt-1">
                  <StatusBadge variant="success">Лучшая цена</StatusBadge>
                </div>
              ) : (
                belowMedianPct <= -5 && (
                  <div className="mt-1">
                    <StatusBadge variant="success">
                      {belowMedianPct}% ниже среднего
                    </StatusBadge>
                  </div>
                )
              )}
            </div>
          </div>

          <div className="mb-2 mt-2 flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-muted-foreground">{card.service_name}</span>
            {card.service_name_raw && card.service_name_raw !== card.service_name && (
              <span
                title={`сопоставлено с «${card.service_name_raw}»`}
                className="cursor-help text-faintest transition-colors hover:text-muted-foreground"
              >
                <Info className="h-3.5 w-3.5" />
              </span>
            )}
            {card.source_category && (
              <span
                title="Раздел каталога источника"
                className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground"
              >
                {card.source_category}
              </span>
            )}
          </div>

          {card.doctor_name && (
            <DoctorRow card={card} onStop={stop} />
          )}

          {duration && (
            <div className="mb-3 text-[11px] text-muted-foreground">{duration}</div>
          )}

          <div className="flex flex-wrap items-center gap-2">
            {card.doctor_id != null && (
              <Link
                to={`/doctors/${card.doctor_id}`}
                onClick={stop}
                className="min-h-[32px] rounded-lg border border-border px-3 py-1.5 text-[11px] text-muted-foreground transition-all hover:border-primary/30 hover:bg-secondary"
              >
                О враче
              </Link>
            )}
            <button
              type="button"
              onClick={(e) => {
                stop(e);
                onPassport();
              }}
              className="min-h-[32px] rounded-lg border border-primary/30 px-3 py-1.5 text-[11px] text-primary transition-all hover:border-primary hover:bg-accent/40"
            >
              Источник цены
            </button>
            <a
              href={routeUrl(card)}
              target="_blank"
              rel="noreferrer"
              onClick={stop}
              className="flex min-h-[32px] items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-[11px] text-muted-foreground transition-all hover:border-primary/30 hover:bg-secondary"
            >
              <Navigation className="h-3 w-3" /> Маршрут
            </a>
            {onDetail && (
              <span className="ml-auto text-[11px] font-medium text-muted-foreground">
                Подробнее →
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function DoctorRow({
  card,
  onStop,
}: {
  card: PriceCardData;
  onStop: (e: MouseEvent) => void;
}) {
  const name = (
    <span className="truncate text-xs font-medium text-foreground">
      {card.doctor_name}
    </span>
  );
  return (
    <div className="mb-2 mt-2 flex items-center gap-2.5 rounded-lg bg-secondary/40 p-2">
      {card.doctor_avatar ? (
        <img
          src={card.doctor_avatar}
          alt={card.doctor_name ?? ""}
          loading="lazy"
          className="h-9 w-9 shrink-0 rounded-full object-cover"
        />
      ) : (
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[11px] font-semibold text-primary">
          {card.doctor_name?.[0] ?? "?"}
        </div>
      )}
      <div className="min-w-0 flex-1">
        {card.doctor_id != null ? (
          <Link
            to={`/doctors/${card.doctor_id}`}
            onClick={onStop}
            className="block min-w-0 hover:underline"
          >
            {name}
          </Link>
        ) : (
          name
        )}
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-0.5 text-[11px] text-muted-foreground">
          {card.doctor_rating != null && (
            <span className="flex items-center gap-0.5 font-medium text-foreground">
              <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
              {card.doctor_rating.toFixed(1)}
              {card.doctor_reviews ? (
                <span className="font-normal text-muted-foreground">
                  {" "}
                  · {card.doctor_reviews} отз.
                </span>
              ) : null}
            </span>
          )}
          {card.doctor_experience != null && (
            <span className="flex items-center gap-0.5">
              <Briefcase className="h-3 w-3" />
              {experienceLabel(card.doctor_experience)}
            </span>
          )}
        </div>
        {card.qualification && (
          <div className="truncate text-[11px] text-muted-foreground">
            {card.qualification}
          </div>
        )}
      </div>
    </div>
  );
}
