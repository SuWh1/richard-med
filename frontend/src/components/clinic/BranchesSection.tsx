import { useEffect, useState } from "react";
import { Check, Clock, MapPin, Navigation, Phone } from "lucide-react";

import type { BranchInfo } from "@/types";
import { type Coords } from "@/lib/geo";
import { geoRouteHandler } from "@/lib/geoRoute";
import { twoGisRouteUrl } from "@/lib/twoGisRoute";
import { cn } from "@/components/ui/utils";
import { RatingBadge } from "@/components/RatingBadge";
import { Pager } from "@/components/Pager";

const PER_PAGE = 6;

interface BranchesSectionProps {
  branches: BranchInfo[];
  selectedId: number | undefined;
  onSelect: (id: number) => void;
  userCoords?: Coords | null;
  onRequestLocation?: () => Promise<Coords | null>;
}

export function BranchesSection({
  branches,
  selectedId,
  onSelect,
  userCoords,
  onRequestLocation,
}: BranchesSectionProps) {
  const [page, setPage] = useState(1);
  const totalPages = Math.max(1, Math.ceil(branches.length / PER_PAGE));
  useEffect(() => {
    if (page > totalPages) setPage(1);
  }, [page, totalPages]);

  if (branches.length === 0) return null;
  const items = branches.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  return (
    <div className="mb-6 overflow-hidden rounded-2xl border border-border bg-white shadow-sm">
      <div className="flex items-center gap-3 border-b border-border px-5 py-4">
        <h2 className="font-semibold text-foreground">Филиалы</h2>
        <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] text-muted-foreground">
          {branches.length}
        </span>
      </div>

      <div className="divide-y divide-secondary">
        {items.map((b) => {
          const selected = b.id === selectedId;
          const hasCoords = b.lat != null && b.lng != null;
          const buildRoute = (origin: Coords | null) =>
            twoGisRouteUrl({ dest: { lat: b.lat!, lng: b.lng! }, origin, city: b.city });
          return (
            <div
              key={b.id}
              className={cn(
                "flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center",
                selected && "bg-accent/30",
              )}
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <MapPin className="h-3.5 w-3.5 shrink-0 text-primary" />
                  <span className="truncate text-sm font-medium text-foreground">
                    {[b.city, b.address].filter(Boolean).join(", ") || "Адрес не указан"}
                  </span>
                </div>
                <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted-foreground">
                  {b.phone && (
                    <span className="flex items-center gap-1">
                      <Phone className="h-3 w-3" /> {b.phone}
                    </span>
                  )}
                  {b.working_hours && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" /> {b.working_hours}
                    </span>
                  )}
                  {b.rating != null && (
                    <RatingBadge rating={b.rating} reviewsCount={b.reviews_count} />
                  )}
                </div>
              </div>

              {hasCoords && (
                <div className="flex shrink-0 items-center gap-2">
                  <button
                    type="button"
                    onClick={() => onSelect(b.id)}
                    className={cn(
                      "flex min-h-[32px] items-center gap-1 rounded-lg border px-3 py-1.5 text-[11px] transition-colors",
                      selected
                        ? "border-primary bg-accent/50 text-primary"
                        : "border-border text-muted-foreground hover:border-primary/30 hover:bg-secondary",
                    )}
                  >
                    {selected ? <Check className="h-3 w-3" /> : <MapPin className="h-3 w-3" />}
                    На карте
                  </button>
                  <a
                    href={buildRoute(userCoords ?? null)}
                    target="_blank"
                    rel="noreferrer"
                    onClick={geoRouteHandler(buildRoute, userCoords, onRequestLocation)}
                    className="flex min-h-[32px] items-center gap-1 rounded-lg border border-border px-3 py-1.5 text-[11px] text-muted-foreground transition-colors hover:border-primary/30 hover:bg-secondary"
                  >
                    <Navigation className="h-3 w-3" /> Маршрут
                  </a>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {totalPages > 1 && (
        <div className="border-t border-secondary py-3">
          <Pager page={page} totalPages={totalPages} onPage={setPage} />
        </div>
      )}
    </div>
  );
}
