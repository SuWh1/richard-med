import { describe, expect, it } from "vitest";

import type { MapPin } from "@/types";
import { clinicPoints } from "./clinicPoints";

function pin(branchId: number, clinicId: number, lat: number, lng: number): MapPin {
  return {
    price_id: 1,
    clinic_id: clinicId,
    clinic_name: "C",
    branch_id: branchId,
    city: "Алматы",
    address: `addr ${branchId}`,
    lat,
    lng,
    price_kzt: 5000,
    parsed_at: "2026-06-27T00:00:00Z",
    age_days: 1,
    freshness: "fresh",
    source_url: "x",
    is_cheapest: true,
  };
}

const PINS: MapPin[] = [
  pin(1, 10, 43.20, 76.90),
  pin(2, 10, 43.30, 76.95),
  pin(3, 20, 43.25, 76.92), // different clinic
];

describe("clinicPoints", () => {
  it("should return only the requested clinic's points", () => {
    const points = clinicPoints(PINS, 10, null);
    expect(points.map((p) => p.branchId).sort()).toEqual([1, 2]);
  });

  it("should sort points by distance to the user when coords are known", () => {
    const near = { lat: 43.205, lng: 76.901 };
    const points = clinicPoints(PINS, 10, near);
    expect(points[0].branchId).toBe(1);
    expect(points[0].distanceKm).not.toBeNull();
    expect(points[0].distanceKm! <= points[1].distanceKm!).toBe(true);
  });

  it("should keep null distances when coords are unknown", () => {
    const points = clinicPoints(PINS, 10, null);
    expect(points.every((p) => p.distanceKm === null)).toBe(true);
  });

  it("should return an empty list for a clinic with no pins", () => {
    expect(clinicPoints(PINS, 999, null)).toEqual([]);
  });
});
