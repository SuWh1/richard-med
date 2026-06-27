import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import type { PriceCard } from "@/types";
import { formatPrice, freshnessLabel } from "@/lib/format";

interface ClinicMapProps {
  cards: PriceCard[];
  cheapestPrice: number | null;
  selectedId: number | null;
  onSelect: (priceId: number) => void;
}

interface PlottableCard extends PriceCard {
  lat: number;
  lng: number;
}

const ALMATY: [number, number] = [43.238949, 76.945465];

function isPlottable(card: PriceCard): card is PlottableCard {
  return card.lat !== null && card.lng !== null;
}

function pinIcon(
  label: string,
  state: { cheapest: boolean; selected: boolean; stale: boolean },
): L.DivIcon {
  const bg = state.stale ? "#94a3b8" : state.cheapest ? "#16a34a" : "#0e9f8e";
  const ring = state.selected
    ? "box-shadow:0 0 0 3px rgba(14,159,142,.5);transform:translate(-50%,-100%) scale(1.08);"
    : "transform:translate(-50%,-100%);";
  const html =
    `<div style="${ring}background:${bg};color:#fff;padding:3px 9px;border-radius:9999px;` +
    `font:600 12px/1.2 Inter,system-ui,sans-serif;white-space:nowrap;` +
    `border:1px solid rgba(255,255,255,.8);box-shadow:0 1px 4px rgba(15,23,42,.25)">${label}</div>`;
  // Anchor at [0,0]; the inner div translates itself so the pill points at the coordinate.
  return L.divIcon({ html, className: "", iconSize: [0, 0], iconAnchor: [0, 0] });
}

function routeUrl(card: PlottableCard): string {
  return `https://www.google.com/maps/dir/?api=1&destination=${card.lat},${card.lng}`;
}

function FitBounds({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) return;
    if (points.length === 1) {
      map.setView(points[0], 13);
      return;
    }
    map.fitBounds(points, { padding: [48, 48] });
  }, [map, points]);
  return null;
}

export function ClinicMap({ cards, cheapestPrice, selectedId, onSelect }: ClinicMapProps) {
  const pins = useMemo(() => cards.filter(isPlottable), [cards]);
  const points = useMemo<[number, number][]>(
    () => pins.map((c) => [c.lat, c.lng]),
    [pins],
  );

  return (
    <MapContainer
      center={points[0] ?? ALMATY}
      zoom={12}
      scrollWheelZoom
      className="h-full w-full rounded-xl"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds points={points} />
      {pins.map((card) => (
        <Marker
          key={card.price_id}
          position={[card.lat, card.lng]}
          icon={pinIcon(formatPrice(card.price_kzt), {
            cheapest: card.price_kzt === cheapestPrice,
            selected: card.price_id === selectedId,
            stale: card.freshness === "stale",
          })}
          eventHandlers={{ click: () => onSelect(card.price_id) }}
        >
          <Popup>
            <div className="space-y-1">
              <p className="font-semibold text-slate-900">{card.clinic_name}</p>
              <p className="text-lg font-bold text-slate-900">
                {formatPrice(card.price_kzt)}
              </p>
              <p className="text-xs text-slate-500">
                {freshnessLabel(card.freshness, card.age_days)}
              </p>
              {card.address && <p className="text-xs text-slate-500">{card.address}</p>}
              <div className="flex gap-3 pt-1 text-xs font-medium text-teal-700">
                <a href={routeUrl(card)} target="_blank" rel="noreferrer">
                  Маршрут
                </a>
                <a href={card.source_url} target="_blank" rel="noreferrer">
                  Открыть источник
                </a>
              </div>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
