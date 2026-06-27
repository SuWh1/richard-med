import { describe, expect, it } from "vitest";

import { buildCompareHref, parseClinicIds } from "./compare";

describe("buildCompareHref", () => {
  it("should build a compare URL with service and clinic ids", () => {
    expect(buildCompareHref(10, [1, 2, 3])).toBe(
      "/compare?service_id=10&clinic_ids=1%2C2%2C3",
    );
  });
});

describe("parseClinicIds", () => {
  it("should parse a comma-separated id list", () => {
    expect(parseClinicIds("1,2,3")).toEqual([1, 2, 3]);
  });

  it("should drop invalid and non-positive ids", () => {
    expect(parseClinicIds("1,x,-2,0,4")).toEqual([1, 4]);
  });

  it("should return an empty array for null", () => {
    expect(parseClinicIds(null)).toEqual([]);
  });
});
