import { useEffect, useMemo, useRef } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import type { MapPin } from "@/types";
import { MapPopupCard } from "./MapPopupCard";

interface ClinicMapProps {
  pins: MapPin[];
  selectedClinicId: number | null;
  onSelectClinic: (clinicId: number | null) => void;
  center: [number, number] | null;
  median: number | null;
}

const KZ_CENTER: [number, number] = [48.0196, 66.9237];

function pinIcon(state: { cheapest: boolean; selected: boolean; stale: boolean }): L.DivIcon {
  const size = state.selected ? 26 : 18;
  const ring = state.cheapest
    ? "box-shadow:0 0 0 4px rgba(217,119,87,.22),0 2px 6px rgba(15,23,42,.3);"
    : "box-shadow:0 2px 6px rgba(15,23,42,.3);";
  const html =
    `<div style="width:100%;height:100%;border-radius:9999px;background:#d97757;` +
    `border:3px solid #fff;${ring}opacity:${state.stale ? 0.5 : 1}"></div>`;
  return L.divIcon({
    html,
    className: "",
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
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

function PanToSelected({
  pins,
  selectedClinicId,
  markers,
}: {
  pins: MapPin[];
  selectedClinicId: number | null;
  markers: React.MutableRefObject<Map<number, L.Marker>>;
}) {
  const map = useMap();
  useEffect(() => {
    if (selectedClinicId == null) return;
    const pin = pins.find((p) => p.clinic_id === selectedClinicId);
    if (!pin) return;
    map.panTo([pin.lat, pin.lng], { animate: true, duration: 0.4 });
    markers.current.get(pin.branch_id)?.openPopup();
  }, [map, pins, selectedClinicId, markers]);
  return null;
}

export function ClinicMap({
  pins,
  selectedClinicId,
  onSelectClinic,
  center,
  median,
}: ClinicMapProps) {
  const points = useMemo<[number, number][]>(
    () => pins.map((p) => [p.lat, p.lng]),
    [pins],
  );
  const markers = useRef<Map<number, L.Marker>>(new Map());

  return (
    <MapContainer
      center={center ?? points[0] ?? KZ_CENTER}
      zoom={12}
      scrollWheelZoom
      zoomControl={false}
      className="h-full w-full rounded-xl"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds points={points} center={center} />
      <PanToSelected pins={pins} selectedClinicId={selectedClinicId} markers={markers} />
      {pins.map((pin) => (
        <Marker
          key={pin.branch_id}
          position={[pin.lat, pin.lng]}
          ref={(m) => {
            if (m) markers.current.set(pin.branch_id, m);
            else markers.current.delete(pin.branch_id);
          }}
          icon={pinIcon({
            cheapest: pin.is_cheapest,
            selected: pin.clinic_id === selectedClinicId,
            stale: pin.freshness === "stale",
          })}
          eventHandlers={{ click: () => onSelectClinic(pin.clinic_id) }}
        >
          <Popup>
            <MapPopupCard pin={pin} median={median} />
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
