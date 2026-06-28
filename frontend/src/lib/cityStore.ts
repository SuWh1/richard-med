import { useSyncExternalStore } from "react";

// Single source of truth for the user's selected city, shared across every page.
export const DEFAULT_CITY = "Астана";
const KEY = "selected_city";
const listeners = new Set<() => void>();

export function getStoredCity(): string {
  if (typeof localStorage === "undefined") return DEFAULT_CITY;
  return localStorage.getItem(KEY) ?? DEFAULT_CITY;
}

export function hasStoredCity(): boolean {
  return typeof localStorage !== "undefined" && localStorage.getItem(KEY) != null;
}

export function setStoredCity(city: string): void {
  if (!city || typeof localStorage === "undefined") return;
  if (localStorage.getItem(KEY) === city) return;
  localStorage.setItem(KEY, city);
  listeners.forEach((l) => l());
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function useCity(): { city: string; setCity: (c: string) => void } {
  const city = useSyncExternalStore(subscribe, getStoredCity, () => DEFAULT_CITY);
  return { city, setCity: setStoredCity };
}
