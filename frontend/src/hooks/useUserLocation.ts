import { useCallback, useEffect, useRef, useState } from "react";

import type { Coords } from "@/lib/geo";

export const GEO_CONSENT_KEY = "geo-consent";

export type GeoStatus = "idle" | "prompting" | "granted" | "denied" | "unavailable";

interface UserLocation {
  coords: Coords | null;
  status: GeoStatus;
  request: () => void;
}

const PERMISSION_DENIED = 1;

function storedConsent(): "granted" | "denied" | null {
  const value = localStorage.getItem(GEO_CONSENT_KEY);
  return value === "granted" || value === "denied" ? value : null;
}

export function useUserLocation(): UserLocation {
  const [coords, setCoords] = useState<Coords | null>(null);
  const [status, setStatus] = useState<GeoStatus>("idle");
  const didInit = useRef(false);

  const request = useCallback(() => {
    if (!("geolocation" in navigator) || !navigator.geolocation) {
      setStatus("unavailable");
      return;
    }
    setStatus("prompting");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setStatus("granted");
        localStorage.setItem(GEO_CONSENT_KEY, "granted");
      },
      (err) => {
        setStatus(err.code === PERMISSION_DENIED ? "denied" : "unavailable");
        if (err.code === PERMISSION_DENIED) {
          localStorage.setItem(GEO_CONSENT_KEY, "denied");
        }
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 5 * 60 * 1000 },
    );
  }, []);

  useEffect(() => {
    if (didInit.current) return;
    didInit.current = true;

    if (!("geolocation" in navigator) || !navigator.geolocation) {
      setStatus("unavailable");
      return;
    }
    if (storedConsent() === "denied") {
      setStatus("denied");
      return;
    }
    request();
  }, [request]);

  return { coords, status, request };
}
