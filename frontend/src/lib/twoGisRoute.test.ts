import { describe, expect, it } from "vitest";

import { twoGisRouteUrl, twoGisSearchUrl } from "./twoGisRoute";

const DEST = { lat: 43.204289, lng: 76.899534 };
const ORIGIN = { lat: 43.21, lng: 76.91 };

describe("twoGisRouteUrl", () => {
  it("should build a directions link with origin and destination as lng,lat points joined by |", () => {
    const url = twoGisRouteUrl({ dest: DEST, origin: ORIGIN, city: "Алматы" });
    expect(url).toBe(
      "https://2gis.kz/almaty/directions/points/76.91,43.21|76.899534,43.204289",
    );
  });

  it("should build a destination-only directions link with an empty origin and centred map", () => {
    const url = twoGisRouteUrl({ dest: DEST, city: "Алматы" });
    expect(url).toBe(
      "https://2gis.kz/almaty/directions/points/|76.899534,43.204289?m=76.899534,43.204289/16",
    );
  });

  it("should map the city to its 2GIS slug", () => {
    const url = twoGisRouteUrl({ dest: DEST, city: "Караганда" });
    expect(url.startsWith("https://2gis.kz/karaganda/")).toBe(true);
  });

  it("should fall back to the default slug for an unknown city", () => {
    const url = twoGisRouteUrl({ dest: DEST, city: "Нью-Йорк" });
    expect(url.startsWith("https://2gis.kz/astana/")).toBe(true);
  });

  it("should fall back to the default slug when city is null", () => {
    const url = twoGisRouteUrl({ dest: DEST, city: null });
    expect(url.startsWith("https://2gis.kz/astana/")).toBe(true);
  });
});

describe("twoGisSearchUrl", () => {
  it("should build a 2GIS search link for the city", () => {
    const url = twoGisSearchUrl({ query: "KDL Olymp, Тұран 43", city: "Астана" });
    expect(url).toBe(
      `https://2gis.kz/astana/search/${encodeURIComponent("KDL Olymp, Тұран 43")}`,
    );
  });

  it("should fall back to the default slug for an unknown city", () => {
    const url = twoGisSearchUrl({ query: "Клиника", city: null });
    expect(url.startsWith("https://2gis.kz/astana/search/")).toBe(true);
  });
});
