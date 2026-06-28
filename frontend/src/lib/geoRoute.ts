import { type MouseEvent } from "react";

import { type Coords } from "@/lib/geo";

/**
 * Click handler for a "Маршрут" link when the user's location may be unknown.
 * Opens the destination route immediately (no popup-block), then re-asks for
 * location and upgrades the opened tab to a from→to route once it's granted.
 * If location is rejected/unavailable, the destination-only route stays open.
 */
export function geoRouteHandler(
  buildHref: (coords: Coords | null) => string,
  userCoords: Coords | null | undefined,
  onRequestLocation: (() => Promise<Coords | null>) | undefined,
) {
  return (e: MouseEvent<HTMLAnchorElement>) => {
    e.stopPropagation();
    if (userCoords || !onRequestLocation) return;
    e.preventDefault();
    const win = window.open(buildHref(null), "_blank");
    void onRequestLocation().then((c) => {
      if (c && win && !win.closed) win.location.href = buildHref(c);
    });
  };
}
