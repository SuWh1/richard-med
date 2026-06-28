import { useEffect, useMemo, useRef } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import type { MapPin } from "@/types";
import type { Coords } from "@/lib/geo";
import { MapPopupCard } from "./MapPopupCard";

function clusterIcon(cluster: { getChildCount: () => number }): L.DivIcon {
  const count = cluster.getChildCount();
  const size = count < 10 ? 36 : count < 50 ? 44 : 52;
  const html =
    `<div style="display:flex;align-items:center;justify-content:center;width:${size}px;` +
    `height:${size}px;border-radius:9999px;background:#d97757;color:#fff;` +
    `font:700 13px/1 Inter,system-ui,sans-serif;border:3px solid #fff;` +
    `box-shadow:0 2px 8px rgba(15,23,42,.35)">${count}</div>`;
  return L.divIcon({ html, className: "", iconSize: [size, size] });
}

interface ClinicMapProps {
  pins: MapPin[];
  selectedBranchId: number | null;
  onSelectBranch: (branchId: number | null) => void;
  center: [number, number] | null;
  median: number | null;
  userCoords?: Coords | null;
  focusPoint?: [number, number] | null;
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
  focusPoint,
}: {
  points: [number, number][];
  center: [number, number] | null;
  focusPoint?: [number, number] | null;
}) {
  const map = useMap();
  useEffect(() => {
    // Focus a single point (e.g. the first list item on mobile) instead of fitting all.
    if (focusPoint) {
      map.setView(focusPoint, 14);
      return;
    }
    if (points.length === 0) {
      if (center) map.setView(center, 12);
      return;
    }
    if (points.length === 1) {
      map.setView(points[0], 13);
      return;
    }
    map.fitBounds(points, { padding: [48, 48] });
  }, [map, points, center, focusPoint]);
  return null;
}

function PanToSelected({
  pins,
  selectedBranchId,
  markers,
}: {
  pins: MapPin[];
  selectedBranchId: number | null;
  markers: React.MutableRefObject<Map<number, L.Marker>>;
}) {
  const map = useMap();
  useEffect(() => {
    if (selectedBranchId == null) return;
    const pin = pins.find((p) => p.branch_id === selectedBranchId);
    if (!pin) return;
    // Zoom in (not just pan) so the highlighted point is clearly located, not a dot in a wide view.
    map.setView([pin.lat, pin.lng], Math.max(map.getZoom(), 15), {
      animate: true,
      duration: 0.4,
    });
    markers.current.get(pin.branch_id)?.openPopup();
  }, [map, pins, selectedBranchId, markers]);
  return null;
}

export function ClinicMap({
  pins,
  selectedBranchId,
  onSelectBranch,
  center,
  median,
  userCoords,
  focusPoint,
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
      <FitBounds points={points} center={center} focusPoint={focusPoint} />
      <PanToSelected pins={pins} selectedBranchId={selectedBranchId} markers={markers} />
      <MarkerClusterGroup
        chunkedLoading
        maxClusterRadius={45}
        showCoverageOnHover={false}
        iconCreateFunction={clusterIcon}
      >
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
              selected: pin.branch_id === selectedBranchId,
              stale: pin.freshness === "stale",
            })}
            eventHandlers={{ click: () => onSelectBranch(pin.branch_id) }}
          >
            <Popup autoPan={false}>
              <MapPopupCard pin={pin} median={median} userCoords={userCoords} />
            </Popup>
          </Marker>
        ))}
      </MarkerClusterGroup>
    </MapContainer>
  );
}
