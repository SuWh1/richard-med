import type { CityInfo } from "@/types";

export interface Coords {
  lat: number;
  lng: number;
}

interface MaybeCoords {
  lat: number | null;
  lng: number | null;
}

const EARTH_RADIUS_KM = 6371;

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

export function haversineKm(a: Coords, b: Coords): number {
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const lat1 = toRad(a.lat);
  const lat2 = toRad(b.lat);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function geoCityFor(
  coords: Coords | null,
  cities: readonly CityInfo[],
  currentCity: string,
): string | null {
  if (!coords || cities.length === 0) return null;
  const near = nearestCity(coords, cities);
  if (!near || near.name === currentCity) return null;
  return near.name;
}

export function nearestCity(coords: Coords, cities: readonly CityInfo[]): CityInfo | null {
  let best: CityInfo | null = null;
  let bestDist = Infinity;
  for (const city of cities) {
    const dist = haversineKm(coords, { lat: city.lat, lng: city.lng });
    if (dist < bestDist) {
      bestDist = dist;
      best = city;
    }
  }
  return best;
}

export function distanceKm(from: Coords, to: MaybeCoords): number | null {
  if (to.lat == null || to.lng == null) return null;
  return haversineKm(from, { lat: to.lat, lng: to.lng });
}

export function sortByNearest<T extends MaybeCoords>(items: readonly T[], from: Coords): T[] {
  return [...items]
    .map((item) => ({ item, dist: distanceKm(from, item) }))
    .sort((a, b) => (a.dist ?? Infinity) - (b.dist ?? Infinity))
    .map(({ item }) => item);
}

export function formatDistance(km: number | null): string {
  if (km == null) return "";
  if (km < 1) return `${Math.round(km * 1000)} м`;
  const rounded = Math.round(km * 10) / 10;
  return Number.isInteger(rounded) ? `${rounded} км` : `${rounded.toFixed(1)} км`;
}
