import { type MouseEvent } from "react";
import { Link } from "react-router-dom";
import {
  Bookmark,
  BookmarkCheck,
  Briefcase,
  Building2,
  Check,
  ChevronDown,
  Info,
  MapPin,
  Navigation,
  Scale,
  Star,
} from "lucide-react";

import type { PriceCard as PriceCardData } from "@/types";
import { formatPrice } from "@/lib/format";
import { pointWord } from "@/lib/rating";
import { discountPct } from "@/lib/results";
import { type Coords, formatDistance } from "@/lib/geo";
import { geoRouteHandler } from "@/lib/geoRoute";
import type { ClinicPoint } from "@/lib/clinicPoints";
import { twoGisRouteUrl, twoGisSearchUrl } from "@/lib/twoGisRoute";
import { cn } from "@/components/ui/utils";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ClinicAvatar } from "./ClinicAvatar";
import { StatusBadge } from "./StatusBadge";
import { FreshBadge } from "./FreshBadge";
import { RatingBadge } from "./RatingBadge";

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
  inCompare?: boolean;
  onCompare?: () => void;
  userCoords?: Coords | null;
  distanceKm?: number | null;
  points?: ClinicPoint[];
  onPointHover?: (branchId: number) => void;
  onPointOpen?: (branchId: number) => void;
  onRequestLocation?: () => Promise<Coords | null>;
  isSaved?: boolean;
  onSave?: () => void;
}

function routeUrl(card: PriceCardData, userCoords?: Coords | null): string {
  if (card.lat != null && card.lng != null) {
    return twoGisRouteUrl({
      dest: { lat: card.lat, lng: card.lng },
      origin: userCoords,
      city: card.city,
    });
  }
  const query = [card.city, card.address, card.clinic_name].filter(Boolean).join(", ");
  return twoGisSearchUrl({ query, city: card.city });
}

export function ClinicCard({
  card,
  isCheapest,
  isHighlighted,
  median,
  onHover,
  onPassport,
  onDetail,
  inCompare = false,
  onCompare,
  userCoords,
  distanceKm,
  points,
  onPointHover,
  onPointOpen,
  onRequestLocation,
  isSaved = false,
  onSave,
}: ClinicCardProps) {
  const distance = formatDistance(distanceKm ?? null);
  const multiPoint = (points?.length ?? 0) > 1;
  const belowMedianPct = median != null ? discountPct(card.price_kzt, median) : 0;
  const stop = (e: MouseEvent) => e.stopPropagation();
  const handleRoute = geoRouteHandler(
    (c) => routeUrl(card, c),
    userCoords,
    onRequestLocation,
  );

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

          <div className="mb-3 flex flex-wrap items-center gap-2">
            <FreshBadge freshness={card.freshness} ageDays={card.age_days} />
            <RatingBadge rating={card.rating} reviewsCount={card.reviews_count} />
            {distance && (
              <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <MapPin className="h-3 w-3" /> {distance}
              </span>
            )}
            {!multiPoint && card.branch_count > 1 && (
              <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                <Building2 className="h-3 w-3" /> {card.branch_count}{" "}
                {pointWord(card.branch_count)} в городе
              </span>
            )}
          </div>

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
              href={routeUrl(card, userCoords)}
              target="_blank"
              rel="noreferrer"
              onClick={handleRoute}
              className="flex min-h-[32px] items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-[11px] text-muted-foreground transition-all hover:border-primary/30 hover:bg-secondary"
            >
              <Navigation className="h-3 w-3" /> Маршрут
            </a>
            {onCompare && (
              <button
                type="button"
                onClick={(e) => {
                  stop(e);
                  onCompare();
                }}
                aria-pressed={inCompare}
                className={cn(
                  "flex min-h-[32px] items-center gap-1 rounded-lg border px-3 py-1.5 text-[11px] transition-all",
                  inCompare
                    ? "border-primary bg-accent/50 text-primary"
                    : "border-border text-muted-foreground hover:border-primary/30 hover:bg-secondary",
                )}
              >
                {inCompare ? (
                  <>
                    <Check className="h-3 w-3" /> В сравнении
                  </>
                ) : (
                  <>
                    <Scale className="h-3 w-3" /> Сравнить
                  </>
                )}
              </button>
            )}
            {onSave && (
              <button
                type="button"
                onClick={(e) => {
                  stop(e);
                  onSave();
                }}
                aria-pressed={isSaved}
                title={isSaved ? "В избранном" : "Сохранить клинику"}
                className={cn(
                  "flex min-h-[32px] items-center gap-1 rounded-lg border px-3 py-1.5 text-[11px] transition-all",
                  isSaved
                    ? "border-primary bg-accent/50 text-primary"
                    : "border-border text-muted-foreground hover:border-primary/30 hover:bg-secondary",
                )}
              >
                {isSaved ? (
                  <>
                    <BookmarkCheck className="h-3 w-3" /> Сохранено
                  </>
                ) : (
                  <>
                    <Bookmark className="h-3 w-3" /> Сохранить
                  </>
                )}
              </button>
            )}
            {onDetail && (
              <span className="ml-auto text-[11px] font-medium text-muted-foreground">
                Подробнее →
              </span>
            )}
          </div>

          {multiPoint && points && (
            <Collapsible className="mt-3 border-t border-secondary pt-3">
              <CollapsibleTrigger
                onClick={stop}
                className="group flex w-full items-center gap-1.5 text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                <Building2 className="h-3.5 w-3.5" />
                {points.length} {pointWord(points.length)} в городе
                <ChevronDown className="h-3.5 w-3.5 transition-transform group-data-[state=open]:rotate-180" />
              </CollapsibleTrigger>
              <CollapsibleContent>
                <div className="mt-2 max-h-52 space-y-1 overflow-y-auto pr-1">
                  {points.map((pt) => (
                    <div
                      key={pt.branchId}
                      role="button"
                      title="Открыть этот филиал"
                      onMouseEnter={() => onPointHover?.(pt.branchId)}
                      onClick={(e) => {
                        stop(e);
                        onPointOpen?.(pt.branchId);
                      }}
                      className="flex cursor-pointer items-center justify-between gap-2 rounded-lg border border-border px-2.5 py-1.5 text-[11px] transition-all hover:border-primary/40 hover:bg-secondary"
                    >
                      <span className="flex min-w-0 items-center gap-1 text-muted-foreground">
                        <MapPin className="h-3 w-3 shrink-0 text-faintest" />
                        <span className="truncate">{pt.address ?? ""}</span>
                      </span>
                      {pt.distanceKm != null && (
                        <span className="shrink-0 text-faintest">
                          {formatDistance(pt.distanceKm)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </CollapsibleContent>
            </Collapsible>
          )}
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
