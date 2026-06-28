import { describe, expect, it } from "vitest";

import { buildSearchParams, parseSearchState, searchHref } from "./useSearchState";

describe("parseSearchState", () => {
  it("should default city and sort when params are absent", () => {
    const s = parseSearchState(new URLSearchParams(""));
    expect(s).toEqual({
      q: "",
      city: "Астана",
      sort: "best_value",
      priceMin: "",
      priceMax: "",
      includeStale: false,
    });
  });

  it("should read every param from the query string", () => {
    const s = parseSearchState(
      new URLSearchParams("q=ОАК&city=Алматы&sort=cheapest&price_min=1000&price_max=5000&stale=1"),
    );
    expect(s.q).toBe("ОАК");
    expect(s.city).toBe("Алматы");
    expect(s.sort).toBe("cheapest");
    expect(s.priceMin).toBe("1000");
    expect(s.priceMax).toBe("5000");
    expect(s.includeStale).toBe(true);
  });

  it("should ignore an invalid sort value", () => {
    expect(parseSearchState(new URLSearchParams("sort=bogus")).sort).toBe("best_value");
  });

  it("should accept the nearest sort value", () => {
    expect(parseSearchState(new URLSearchParams("sort=nearest")).sort).toBe("nearest");
  });
});

describe("buildSearchParams", () => {
  it("should omit defaults to keep the URL clean", () => {
    const sp = buildSearchParams(parseSearchState(new URLSearchParams("q=ОАК")));
    expect(sp.toString()).toBe("q=%D0%9E%D0%90%D0%9A");
  });

  it("should round-trip with parseSearchState", () => {
    const original = new URLSearchParams("q=УЗИ&city=Алматы&sort=newest&price_min=500&stale=1");
    const rebuilt = buildSearchParams(parseSearchState(original));
    expect(parseSearchState(rebuilt)).toEqual(parseSearchState(original));
  });
});

describe("searchHref", () => {
  it("should build a /search url from a bare query", () => {
    expect(searchHref({ q: "ОАК" })).toBe("/search?q=%D0%9E%D0%90%D0%9A");
  });

  it("should include a non-default city", () => {
    expect(searchHref({ q: "ОАК", city: "Алматы" })).toContain("city=");
  });
});
