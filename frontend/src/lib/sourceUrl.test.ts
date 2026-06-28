import { describe, expect, it } from "vitest";

import { sourceViewUrl } from "./sourceUrl";

describe("sourceViewUrl", () => {
  it("should build a KDL pricelist search URL for the row's city", () => {
    const url = sourceViewUrl(
      "https://kdlolymp.kz/analysis/indeks-fibroza-pecheni-fib-4",
      "Шымкент",
      "ОАК 5 классов",
    );
    const u = new URL(url);
    expect(u.hostname).toBe("kdlolymp.kz");
    expect(u.pathname).toBe("/pricelist/shymkent");
    expect(u.searchParams.get("search")).toBe("ОАК 5 классов");
  });

  it("should default the KDL city slug to astana when city is unknown", () => {
    const url = sourceViewUrl("https://kdlolymp.kz/analysis/x", null, "ОАК");
    expect(new URL(url).pathname).toBe("/pricelist/astana");
  });

  it("should send Invitro to the for-doctors price page", () => {
    const url = sourceViewUrl("https://invitro.kz", "Астана", "ОАК");
    expect(url).toBe("https://invitro.kz/analizes/for-doctors/");
  });

  it("should leave an unknown source URL unchanged", () => {
    const original = "https://doq.kz/doctors/astana/terapevt";
    expect(sourceViewUrl(original, "Астана", "Приём терапевта")).toBe(original);
  });

  it("should return the input unchanged when it is not a valid URL", () => {
    expect(sourceViewUrl("not-a-url", "Астана", "ОАК")).toBe("not-a-url");
  });
});
