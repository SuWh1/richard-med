import { useCallback, useEffect, useRef, useState } from "react";

import type { Coords } from "@/lib/geo";

export const GEO_CONSENT_KEY = "geo-consent";

export type GeoStatus = "idle" | "prompting" | "granted" | "denied" | "unavailable";

interface UserLocation {
  coords: Coords | null;
  status: GeoStatus;
  permission: PermissionState | null;
  request: () => void;
  requestOnce: () => Promise<Coords | null>;
}

const PERMISSION_DENIED = 1;

function storedConsent(): "granted" | "denied" | null {
  const value = localStorage.getItem(GEO_CONSENT_KEY);
  return value === "granted" || value === "denied" ? value : null;
}

export function useUserLocation(): UserLocation {
  const [coords, setCoords] = useState<Coords | null>(null);
  const [status, setStatus] = useState<GeoStatus>("idle");
  const [permission, setPermission] = useState<PermissionState | null>(null);
  const didInit = useRef(false);

  useEffect(() => {
    if (!navigator.permissions?.query) return;
    let active = true;
    navigator.permissions
      .query({ name: "geolocation" as PermissionName })
      .then((p) => {
        if (!active) return;
        setPermission(p.state);
        p.onchange = () => setPermission(p.state);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  const requestOnce = useCallback((): Promise<Coords | null> => {
    if (!("geolocation" in navigator) || !navigator.geolocation) {
      setStatus("unavailable");
      return Promise.resolve(null);
    }
    setStatus("prompting");
    return new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const c = { lat: pos.coords.latitude, lng: pos.coords.longitude };
          setCoords(c);
          setStatus("granted");
          localStorage.setItem(GEO_CONSENT_KEY, "granted");
          resolve(c);
        },
        (err) => {
          setStatus(err.code === PERMISSION_DENIED ? "denied" : "unavailable");
          if (err.code === PERMISSION_DENIED) {
            localStorage.setItem(GEO_CONSENT_KEY, "denied");
          }
          resolve(null);
        },
        { enableHighAccuracy: false, timeout: 10000, maximumAge: 5 * 60 * 1000 },
      );
    });
  }, []);

  const request = useCallback(() => {
    void requestOnce();
  }, [requestOnce]);

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

  return { coords, status, permission, request, requestOnce };
}
