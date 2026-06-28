import { useEffect, useRef } from "react";
import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Navigation } from "lucide-react";

import { type Coords } from "@/lib/geo";
import { geoRouteHandler } from "@/lib/geoRoute";
import { twoGisRouteUrl } from "@/lib/twoGisRoute";
import { ClinicAvatar } from "@/components/ClinicAvatar";

const markerIcon = L.divIcon({
  html:
    `<div style="width:20px;height:20px;border-radius:9999px;background:#d97757;` +
    `border:3px solid #fff;box-shadow:0 2px 8px rgba(15,23,42,.35)"></div>`,
  className: "",
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

interface ClinicLocationMapProps {
  lat: number;
  lng: number;
  name: string;
  address?: string | null;
  city?: string | null;
  userCoords?: Coords | null;
  onRequestLocation?: () => Promise<Coords | null>;
}

export function ClinicLocationMap({
  lat,
  lng,
  name,
  address,
  city,
  userCoords,
  onRequestLocation,
}: ClinicLocationMapProps) {
  const markerRef = useRef<L.Marker>(null);
  useEffect(() => {
    // Defer a tick so react-leaflet has bound the <Popup> child before we open it.
    const id = setTimeout(() => markerRef.current?.openPopup(), 60);
    return () => clearTimeout(id);
  }, [lat, lng]);

  const buildRoute = (origin: Coords | null) =>
    twoGisRouteUrl({ dest: { lat, lng }, origin, city });
  const handleRoute = geoRouteHandler(buildRoute, userCoords, onRequestLocation);

  return (
    <MapContainer
      center={[lat, lng]}
      zoom={16}
      scrollWheelZoom={false}
      zoomControl={false}
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Marker ref={markerRef} position={[lat, lng]} icon={markerIcon}>
        <Popup autoPan={false}>
          <div className="w-56">
            <div className="mb-3 flex items-center gap-2">
              <ClinicAvatar name={name} size="sm" />
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold leading-tight text-foreground">
                  {name}
                </div>
                {address && (
                  <div className="truncate text-[11px] text-muted-foreground">{address}</div>
                )}
              </div>
            </div>
            <a
              href={buildRoute(userCoords ?? null)}
              target="_blank"
              rel="noreferrer"
              onClick={handleRoute}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-border py-2 text-xs font-medium !text-muted-foreground transition-colors hover:bg-secondary"
            >
              <Navigation className="h-3.5 w-3.5" /> Маршрут
            </a>
          </div>
        </Popup>
      </Marker>
    </MapContainer>
  );
}
