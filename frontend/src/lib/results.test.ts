import { describe, expect, it } from "vitest";

import type { MapPin, PriceCard } from "@/types";
import {
  dedupePinsByLocation,
  discountPct,
  medianPrice,
  savingsVsMedian,
  topCheapestClinicIds,
} from "@/lib/results";

function pin(partial: Partial<MapPin>): MapPin {
  return {
    price_id: 0,
    clinic_id: 1,
    clinic_name: "Clinic",
    branch_id: 0,
    city: "Астана",
    address: null,
    lat: 51,
    lng: 71,
    price_kzt: 1000,
    parsed_at: "2026-06-24T00:00:00Z",
    age_days: 1,
    freshness: "fresh",
    source_url: "https://example.com",
    is_cheapest: false,
    ...partial,
  };
}

function card(partial: Partial<PriceCard>): PriceCard {
  return {
    price_id: 0,
    service_id: 1,
    service_name: "ОАК",
    clinic_id: 0,
    clinic_name: "Clinic",
    doctor_name: null,
    branch_id: null,
    city: "Астана",
    address: null,
    lat: null,
    lng: null,
    price_kzt: 1000,
    duration_min: null,
    duration_max: null,
    parsed_at: "2026-06-24T00:00:00Z",
    age_days: 1,
    freshness: "fresh",
    source_url: "https://example.com",
    service_name_raw: null,
    content_hash: null,
    match_confidence: 1,
    match_method: "exact",
    ...partial,
  };
}

describe("medianPrice", () => {
  it("should return null for an empty list", () => {
    expect(medianPrice([])).toBeNull();
  });

  it("should return the middle value for an odd count", () => {
    expect(medianPrice([1880, 2200, 9000])).toBe(2200);
  });

  it("should average the two middle values for an even count", () => {
    expect(medianPrice([1880, 2200, 2750, 3100])).toBe(2475);
  });

  it("should be order-independent", () => {
    expect(medianPrice([9000, 1880, 2200])).toBe(2200);
  });
});

describe("savingsVsMedian", () => {
  it("should be positive when the price is below the median", () => {
    expect(savingsVsMedian(1880, 2700)).toBe(820);
  });

  it("should be zero or negative when the price is at or above the median", () => {
    expect(savingsVsMedian(2700, 2700)).toBe(0);
    expect(savingsVsMedian(3100, 2700)).toBe(-400);
  });
});

describe("discountPct", () => {
  it("should return a negative percent for a below-median price", () => {
    expect(discountPct(1890, 2700)).toBe(-30);
  });

  it("should return a positive percent for an above-median price", () => {
    expect(discountPct(3510, 2700)).toBe(30);
  });

  it("should return 0 when median is missing or zero", () => {
    expect(discountPct(1880, null)).toBe(0);
    expect(discountPct(1880, 0)).toBe(0);
  });
});

describe("topCheapestClinicIds", () => {
  it("should return the cheapest n distinct clinic ids in price order", () => {
    const cards = [
      card({ clinic_id: 1, price_kzt: 9000 }),
      card({ clinic_id: 2, price_kzt: 1880 }),
      card({ clinic_id: 3, price_kzt: 2200 }),
      card({ clinic_id: 4, price_kzt: 3100 }),
    ];
    expect(topCheapestClinicIds(cards, 3)).toEqual([2, 3, 4]);
  });

  it("should keep only the cheapest price per clinic", () => {
    const cards = [
      card({ clinic_id: 1, price_kzt: 5000 }),
      card({ clinic_id: 1, price_kzt: 1880 }),
      card({ clinic_id: 2, price_kzt: 2200 }),
    ];
    expect(topCheapestClinicIds(cards, 3)).toEqual([1, 2]);
  });

  it("should return an empty list when there are no cards", () => {
    expect(topCheapestClinicIds([], 3)).toEqual([]);
  });
});

describe("dedupePinsByLocation", () => {
  it("should keep every distinct branch location", () => {
    const pins = [
      pin({ clinic_id: 1, branch_id: 10, lat: 51.1, lng: 71.4, price_kzt: 6600 }),
      pin({ clinic_id: 1, branch_id: 11, lat: 51.2, lng: 71.5, price_kzt: 6600 }),
      pin({ clinic_id: 2, branch_id: 20, lat: 51.3, lng: 71.6, price_kzt: 2200 }),
    ];
    expect(dedupePinsByLocation(pins)).toHaveLength(3);
  });

  it("should collapse duplicate rows of one clinic at the same coordinates to the cheapest", () => {
    const pins = [
      pin({ clinic_id: 1, branch_id: 10, lat: 51.1, lng: 71.4, price_kzt: 6600 }),
      pin({ clinic_id: 1, branch_id: 10, lat: 51.1, lng: 71.4, price_kzt: 5000 }),
    ];
    const result = dedupePinsByLocation(pins);
    expect(result).toHaveLength(1);
    expect(result[0].price_kzt).toBe(5000);
  });

  it("should keep two different clinics that share the same coordinates", () => {
    const pins = [
      pin({ clinic_id: 1, lat: 51.1, lng: 71.4, price_kzt: 6600 }),
      pin({ clinic_id: 2, lat: 51.1, lng: 71.4, price_kzt: 2200 }),
    ];
    expect(dedupePinsByLocation(pins)).toHaveLength(2);
  });

  it("should return an empty list when there are no pins", () => {
    expect(dedupePinsByLocation([])).toEqual([]);
  });
});
