import type { ReactNode } from "react";
import { act, renderHook } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { useSearchState } from "./useSearchState";

function wrapper(initial: string) {
  return ({ children }: { children: ReactNode }) => (
    <MemoryRouter initialEntries={[initial]}>{children}</MemoryRouter>
  );
}

describe("useSearchState (router integration)", () => {
  it("should hydrate state from the initial URL (proves reload restores results)", () => {
    const { result } = renderHook(() => useSearchState(), {
      wrapper: wrapper("/search?q=%D0%9E%D0%90%D0%9A&sort=cheapest&stale=1"),
    });
    expect(result.current.state.q).toBe("ОАК");
    expect(result.current.state.sort).toBe("cheapest");
    expect(result.current.state.includeStale).toBe(true);
  });

  it("should write a patch back into the URL query string", () => {
    const { result } = renderHook(
      () => ({ search: useSearchState(), loc: useLocation() }),
      { wrapper: wrapper("/search?q=%D0%9E%D0%90%D0%9A") },
    );
    act(() => result.current.search.update({ city: "Алматы", sort: "newest" }));
    expect(result.current.search.state.city).toBe("Алматы");
    expect(result.current.loc.search).toContain("city=");
    expect(result.current.loc.search).toContain("sort=newest");
  });
});
