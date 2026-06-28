import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GEO_CONSENT_KEY, useUserLocation } from "./useUserLocation";

type SuccessFn = (pos: { coords: { latitude: number; longitude: number } }) => void;
type ErrorFn = (err: { code: number; message: string }) => void;

function mockGeolocation(impl: (success: SuccessFn, error: ErrorFn) => void) {
  const getCurrentPosition = vi.fn(impl);
  Object.defineProperty(globalThis.navigator, "geolocation", {
    configurable: true,
    value: { getCurrentPosition },
  });
  return getCurrentPosition;
}

function removeGeolocation() {
  Object.defineProperty(globalThis.navigator, "geolocation", {
    configurable: true,
    value: undefined,
  });
}

const PERMISSION_DENIED = 1;

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("useUserLocation", () => {
  it("should request the position on first mount and expose coords on success", async () => {
    const get = mockGeolocation((success) =>
      success({ coords: { latitude: 43.2389, longitude: 76.8897 } }),
    );

    const { result } = renderHook(() => useUserLocation());

    await waitFor(() => expect(result.current.status).toBe("granted"));
    expect(result.current.coords).toEqual({ lat: 43.2389, lng: 76.8897 });
    expect(get).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem(GEO_CONSENT_KEY)).toBe("granted");
  });

  it("should mark status denied and store the decision when permission is refused", async () => {
    mockGeolocation((_success, error) =>
      error({ code: PERMISSION_DENIED, message: "denied" }),
    );

    const { result } = renderHook(() => useUserLocation());

    await waitFor(() => expect(result.current.status).toBe("denied"));
    expect(result.current.coords).toBeNull();
    expect(localStorage.getItem(GEO_CONSENT_KEY)).toBe("denied");
  });

  it("should not auto-prompt when a previous decision was denied", () => {
    localStorage.setItem(GEO_CONSENT_KEY, "denied");
    const get = mockGeolocation((success) =>
      success({ coords: { latitude: 1, longitude: 2 } }),
    );

    const { result } = renderHook(() => useUserLocation());

    expect(get).not.toHaveBeenCalled();
    expect(result.current.status).toBe("denied");
  });

  it("should re-prompt manually via request() even after a denial", async () => {
    localStorage.setItem(GEO_CONSENT_KEY, "denied");
    const get = mockGeolocation((success) =>
      success({ coords: { latitude: 51.16, longitude: 71.47 } }),
    );

    const { result } = renderHook(() => useUserLocation());
    expect(get).not.toHaveBeenCalled();

    act(() => result.current.request());

    await waitFor(() => expect(result.current.status).toBe("granted"));
    expect(result.current.coords).toEqual({ lat: 51.16, lng: 71.47 });
  });

  it("should report unavailable when the browser has no geolocation", () => {
    removeGeolocation();

    const { result } = renderHook(() => useUserLocation());

    expect(result.current.status).toBe("unavailable");
    expect(result.current.coords).toBeNull();
  });
});
