import { ExternalLink, Navigation } from "lucide-react";

import type { MapPin } from "@/types";
import { formatPrice } from "@/lib/format";
import { savingsVsMedian } from "@/lib/results";
import { ClinicAvatar } from "@/components/ClinicAvatar";
import { FreshBadge } from "@/components/FreshBadge";

interface MapPopupCardProps {
  pin: MapPin;
  median: number | null;
}

function routeUrl(pin: MapPin): string {
  return `https://www.google.com/maps/dir/?api=1&destination=${pin.lat},${pin.lng}`;
}

export function MapPopupCard({ pin, median }: MapPopupCardProps) {
  const savings = median != null ? savingsVsMedian(pin.price_kzt, median) : 0;

  return (
    <div className="w-60">
      <div className="mb-3 flex items-center gap-2">
        <ClinicAvatar name={pin.clinic_name} size="sm" />
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold leading-tight text-foreground">
            {pin.clinic_name}
          </div>
          {pin.address && (
            <div className="truncate text-[11px] text-muted-foreground">{pin.address}</div>
          )}
        </div>
      </div>

      <div className="mb-0.5 text-2xl font-bold leading-none text-foreground">
        {formatPrice(pin.price_kzt)}
      </div>
      {median != null && (
        <div className="mb-2 text-[11px] text-faint">
          медиана {formatPrice(median)} ·{" "}
          {savings > 0 ? `экономия ${formatPrice(savings)}` : "выше медианы"}
        </div>
      )}

      <FreshBadge freshness={pin.freshness} ageDays={pin.age_days} />

      <div className="mt-3 flex gap-2">
        <a
          href={routeUrl(pin)}
          target="_blank"
          rel="noreferrer"
          className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-border py-2 text-xs font-medium !text-muted-foreground transition-colors hover:bg-secondary"
        >
          <Navigation className="h-3.5 w-3.5" /> Маршрут
        </a>
        <a
          href={pin.source_url}
          target="_blank"
          rel="noreferrer"
          className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary py-2 text-center text-xs font-semibold !text-white transition-colors hover:bg-primary-hover"
        >
          <ExternalLink className="h-3.5 w-3.5" /> Источник
        </a>
      </div>
    </div>
  );
}
