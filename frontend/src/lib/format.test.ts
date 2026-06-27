import { describe, expect, it } from "vitest";

import { formatPrice, freshnessLabel, sourceLabel } from "./format";

// ru-RU grouping uses a non-breaking space; normalize so the assertion checks
// grouping + currency, not the exact Unicode whitespace character.
const norm = (s: string) => s.replace(/\s/g, " ");

describe("formatPrice", () => {
  it("should format an integer as KZT with a thousands separator", () => {
    expect(norm(formatPrice(1880))).toBe("1 880 ₸");
  });

  it("should format large prices", () => {
    expect(norm(formatPrice(115000))).toBe("115 000 ₸");
  });
});

describe("freshnessLabel", () => {
  it("should warn when a price is stale", () => {
    expect(freshnessLabel("stale", 45)).toBe("Цена требует обновления");
  });

  it("should say today for a zero-day-old fresh price", () => {
    expect(freshnessLabel("fresh", 0)).toBe("Обновлено сегодня");
  });

  it("should say yesterday for a one-day-old price", () => {
    expect(freshnessLabel("recent", 1)).toBe("Обновлено вчера");
  });

  it("should report the age in days otherwise", () => {
    expect(freshnessLabel("recent", 5)).toBe("Обновлено 5 дн. назад");
  });
});

describe("sourceLabel", () => {
  it("should map known source slugs to display names", () => {
    expect(sourceLabel("kdl_olymp")).toBe("KDL Olymp");
  });

  it("should fall back to the raw slug for unknown sources", () => {
    expect(sourceLabel("unknown_src")).toBe("unknown_src");
  });
});
