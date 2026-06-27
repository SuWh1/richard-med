import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import type { MapPin } from "@/types";
import { formatPrice, freshnessLabel } from "@/lib/format";

interface ClinicMapProps {
  pins: MapPin[];
  selectedClinicId: number | null;
  onSelectClinic: (clinicId: number | null) => void;
  center: [number, number] | null;
}

const KZ_CENTER: [number, number] = [48.0196, 66.9237];

function pinIcon(
  label: string,
  state: { cheapest: boolean; selected: boolean; stale: boolean },
): L.DivIcon {
  const bg = state.stale ? "#94a3b8" : state.cheapest ? "#16a34a" : "#0e9f8e";
  const ring = state.selected
    ? "box-shadow:0 0 0 3px rgba(14,159,142,.5);transform:translate(-50%,-100%) scale(1.1);z-index:10000;"
    : "transform:translate(-50%,-100%);";
  const html =
    `<div style="${ring}background:${bg};color:#fff;padding:3px 9px;border-radius:9999px;` +
    `font:600 12px/1.2 Inter,system-ui,sans-serif;white-space:nowrap;` +
    `border:1px solid rgba(255,255,255,.8);box-shadow:0 1px 4px rgba(15,23,42,.25)">${label}</div>`;
  return L.divIcon({ html, className: "", iconSize: [0, 0], iconAnchor: [0, 0] });
}

function routeUrl(pin: MapPin): string {
  return `https://www.google.com/maps/dir/?api=1&destination=${pin.lat},${pin.lng}`;
}

function FitBounds({
  points,
  center,
}: {
  points: [number, number][];
  center: [number, number] | null;
}) {
  const map = useMap();
  useEffect(() => {
    if (points.length === 0) {
      if (center) map.setView(center, 12);
      return;
    }
    if (points.length === 1) {
      map.setView(points[0], 13);
      return;
    }
    map.fitBounds(points, { padding: [48, 48] });
  }, [map, points, center]);
  return null;
}

export function ClinicMap({ pins, selectedClinicId, onSelectClinic, center }: ClinicMapProps) {
  const points = useMemo<[number, number][]>(
    () => pins.map((p) => [p.lat, p.lng]),
    [pins],
  );

  return (
    <MapContainer
      center={center ?? points[0] ?? KZ_CENTER}
      zoom={12}
      scrollWheelZoom
      className="h-full w-full rounded-xl"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds points={points} center={center} />
      {pins.map((pin) => (
        <Marker
          key={pin.branch_id}
          position={[pin.lat, pin.lng]}
          icon={pinIcon(formatPrice(pin.price_kzt), {
            cheapest: pin.is_cheapest,
            selected: pin.clinic_id === selectedClinicId,
            stale: pin.freshness === "stale",
          })}
          eventHandlers={{ click: () => onSelectClinic(pin.clinic_id) }}
        >
          <Popup>
            <div className="space-y-1">
              <p className="font-semibold text-slate-900">{pin.clinic_name}</p>
              <p className="text-lg font-bold text-slate-900">{formatPrice(pin.price_kzt)}</p>
              <p className="text-xs text-slate-500">
                {freshnessLabel(pin.freshness, pin.age_days)}
              </p>
              {pin.address && <p className="text-xs text-slate-500">{pin.address}</p>}
              <div className="flex gap-3 pt-1 text-xs font-medium text-teal-700">
                <a href={routeUrl(pin)} target="_blank" rel="noreferrer">
                  Маршрут
                </a>
                <a href={pin.source_url} target="_blank" rel="noreferrer">
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
