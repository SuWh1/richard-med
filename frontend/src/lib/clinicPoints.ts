import type { MapPin } from "@/types";
import { type Coords, distanceKm } from "./geo";

export interface ClinicPoint {
  branchId: number;
  address: string | null;
  lat: number;
  lng: number;
  distanceKm: number | null;
}

export function clinicPoints(
  pins: MapPin[],
  clinicId: number,
  coords: Coords | null,
): ClinicPoint[] {
  const points = pins
    .filter((p) => p.clinic_id === clinicId)
    .map((p) => ({
      branchId: p.branch_id,
      address: p.address,
      lat: p.lat,
      lng: p.lng,
      distanceKm: coords ? distanceKm(coords, p) : null,
    }));
  if (coords) {
    points.sort((a, b) => (a.distanceKm ?? Infinity) - (b.distanceKm ?? Infinity));
  }
  return points;
}
