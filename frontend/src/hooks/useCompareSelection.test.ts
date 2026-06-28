import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MAX_COMPARE, useCompareSelection } from "./useCompareSelection";

describe("useCompareSelection", () => {
  it("should toggle a clinic in and out of the selection", () => {
    const { result } = renderHook(() => useCompareSelection(1));

    act(() => result.current.toggle(10));
    expect(result.current.selected).toEqual([10]);
    expect(result.current.isSelected(10)).toBe(true);

    act(() => result.current.toggle(10));
    expect(result.current.selected).toEqual([]);
  });

  it("should not add more than MAX_COMPARE clinics", () => {
    const { result } = renderHook(() => useCompareSelection(1));

    act(() => {
      result.current.toggle(1);
      result.current.toggle(2);
      result.current.toggle(3);
      result.current.toggle(4);
    });

    expect(result.current.selected).toHaveLength(MAX_COMPARE);
    expect(result.current.isFull).toBe(true);
    expect(result.current.selected).not.toContain(4);
  });

  it("should clear the selection when the service changes", () => {
    const { result, rerender } = renderHook(
      ({ serviceId }) => useCompareSelection(serviceId),
      { initialProps: { serviceId: 1 } },
    );

    act(() => result.current.toggle(10));
    expect(result.current.selected).toEqual([10]);

    rerender({ serviceId: 2 });
    expect(result.current.selected).toEqual([]);
  });

  it("should clear all selections via clear()", () => {
    const { result } = renderHook(() => useCompareSelection(1));

    act(() => {
      result.current.toggle(1);
      result.current.toggle(2);
    });
    act(() => result.current.clear());

    expect(result.current.selected).toEqual([]);
  });
});
