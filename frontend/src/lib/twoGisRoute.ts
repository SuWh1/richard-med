import { KDL_CITY_SLUG } from "./sourceUrl";
import type { Coords } from "./geo";

const DEFAULT_SLUG = "astana";

function citySlug(city: string | null | undefined): string {
  return (city && KDL_CITY_SLUG[city]) || DEFAULT_SLUG;
}

// 2GIS waypoints are "<lng>,<lat>" joined by `|`; an empty leading point means "ask for origin".
function point(c: Coords): string {
  return `${c.lng},${c.lat}`;
}

interface RouteArgs {
  dest: Coords;
  origin?: Coords | null;
  city?: string | null;
}

export function twoGisRouteUrl({ dest, origin, city }: RouteArgs): string {
  const base = `https://2gis.kz/${citySlug(city)}/directions/points`;
  if (origin) {
    return `${base}/${point(origin)}|${point(dest)}`;
  }
  return `${base}/|${point(dest)}?m=${point(dest)}/16`;
}

interface SearchArgs {
  query: string;
  city?: string | null;
}

export function twoGisSearchUrl({ query, city }: SearchArgs): string {
  return `https://2gis.kz/${citySlug(city)}/search/${encodeURIComponent(query)}`;
}
