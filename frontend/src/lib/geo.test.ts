import { describe, expect, it } from "vitest";

import type { CityInfo } from "@/types";
import {
  distanceKm,
  formatDistance,
  geoCityFor,
  haversineKm,
  nearestCity,
  sortByNearest,
} from "./geo";

const ASTANA = { lat: 51.1605, lng: 71.4704 };
const ALMATY = { lat: 43.2389, lng: 76.8897 };

const CITIES: CityInfo[] = [
  { name: "Астана", lat: 51.1605, lng: 71.4704 },
  { name: "Алматы", lat: 43.2389, lng: 76.8897 },
  { name: "Караганда", lat: 49.806, lng: 73.0857 },
];

describe("geoCityFor", () => {
  it("should return the nearest city when it differs from the current one", () => {
    expect(geoCityFor(ALMATY, CITIES, "Астана")).toBe("Алматы");
  });

  it("should return null when the nearest city is already selected", () => {
    expect(geoCityFor(ASTANA, CITIES, "Астана")).toBeNull();
  });

  it("should return null when coords are missing", () => {
    expect(geoCityFor(null, CITIES, "Астана")).toBeNull();
  });

  it("should return null when no cities are available", () => {
    expect(geoCityFor(ALMATY, [], "Астана")).toBeNull();
  });
});

describe("haversineKm", () => {
  it("should return ~0 for identical points", () => {
    expect(haversineKm(ASTANA, ASTANA)).toBeCloseTo(0, 5);
  });

  it("should return the great-circle distance between Astana and Almaty", () => {
    // ~970 km in reality; allow a generous band for the spherical model
    expect(haversineKm(ASTANA, ALMATY)).toBeGreaterThan(900);
    expect(haversineKm(ASTANA, ALMATY)).toBeLessThan(1050);
  });

  it("should be symmetric", () => {
    expect(haversineKm(ASTANA, ALMATY)).toBeCloseTo(haversineKm(ALMATY, ASTANA), 6);
  });
});

describe("nearestCity", () => {
  it("should pick the closest city to the given coordinates", () => {
    const nearAlmaty = { lat: 43.3, lng: 76.95 };
    expect(nearestCity(nearAlmaty, CITIES)?.name).toBe("Алматы");
  });

  it("should pick Astana for a point near Astana", () => {
    expect(nearestCity({ lat: 51.2, lng: 71.5 }, CITIES)?.name).toBe("Астана");
  });

  it("should return null when the city list is empty", () => {
    expect(nearestCity(ASTANA, [])).toBeNull();
  });
});

describe("distanceKm", () => {
  it("should return null when the target has no coordinates", () => {
    expect(distanceKm(ASTANA, { lat: null, lng: null })).toBeNull();
    expect(distanceKm(ASTANA, { lat: 51.1, lng: null })).toBeNull();
  });

  it("should return a positive distance for valid coordinates", () => {
    expect(distanceKm(ASTANA, { lat: ALMATY.lat, lng: ALMATY.lng })).toBeGreaterThan(900);
  });
});

describe("sortByNearest", () => {
  it("should order items by ascending distance from the origin", () => {
    const items = [
      { id: "far", lat: ALMATY.lat, lng: ALMATY.lng },
      { id: "near", lat: 51.2, lng: 71.5 },
      { id: "mid", lat: 49.806, lng: 73.0857 },
    ];
    const sorted = sortByNearest(items, ASTANA);
    expect(sorted.map((i) => i.id)).toEqual(["near", "mid", "far"]);
  });

  it("should push items without coordinates to the end", () => {
    const items = [
      { id: "noCoords", lat: null, lng: null },
      { id: "near", lat: 51.2, lng: 71.5 },
    ];
    const sorted = sortByNearest(items, ASTANA);
    expect(sorted.map((i) => i.id)).toEqual(["near", "noCoords"]);
  });

  it("should not mutate the input array", () => {
    const items = [
      { id: "far", lat: ALMATY.lat, lng: ALMATY.lng },
      { id: "near", lat: 51.2, lng: 71.5 },
    ];
    const before = items.map((i) => i.id);
    sortByNearest(items, ASTANA);
    expect(items.map((i) => i.id)).toEqual(before);
  });
});

describe("formatDistance", () => {
  it("should render sub-kilometre distances in metres", () => {
    expect(formatDistance(0.42)).toBe("420 м");
  });

  it("should render kilometre distances with one decimal", () => {
    expect(formatDistance(2.42)).toBe("2.4 км");
  });

  it("should drop the decimal for round, larger distances", () => {
    expect(formatDistance(12.0)).toBe("12 км");
  });

  it("should return an empty string for null", () => {
    expect(formatDistance(null)).toBe("");
  });
});
