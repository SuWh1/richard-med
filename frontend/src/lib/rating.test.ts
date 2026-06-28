import { describe, expect, it } from "vitest";

import { formatRating, formatReviewCount, reviewWord } from "./rating";

describe("formatRating", () => {
  it("should render one decimal place", () => {
    expect(formatRating(4.9)).toBe("4.9");
    expect(formatRating(5)).toBe("5.0");
  });
});

describe("formatReviewCount", () => {
  it("should render small counts as-is", () => {
    expect(formatReviewCount(155)).toBe("155");
  });

  it("should compact thousands", () => {
    expect(formatReviewCount(5414)).toBe("5,4 тыс.");
    expect(formatReviewCount(22811)).toBe("22,8 тыс.");
  });
});

describe("reviewWord", () => {
  it("should pluralize отзыв for Russian", () => {
    expect(reviewWord(1)).toBe("отзыв");
    expect(reviewWord(2)).toBe("отзыва");
    expect(reviewWord(5)).toBe("отзывов");
    expect(reviewWord(11)).toBe("отзывов");
    expect(reviewWord(21)).toBe("отзыв");
  });
});
