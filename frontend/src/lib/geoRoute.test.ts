import { describe, expect, it, vi } from "vitest";

import { geoRouteHandler } from "./geoRoute";

function fakeEvent() {
  return { preventDefault: vi.fn(), stopPropagation: vi.fn() } as unknown as
    React.MouseEvent<HTMLAnchorElement>;
}

const build = (c: { lat: number; lng: number } | null) =>
  c ? `route?from=${c.lat},${c.lng}` : "route?dest-only";

describe("geoRouteHandler", () => {
  it("should open the destination immediately and upgrade after location is granted", async () => {
    const fakeWin = { closed: false, location: { href: "" } };
    const openSpy = vi.spyOn(window, "open").mockReturnValue(fakeWin as unknown as Window);
    const onRequestLocation = vi.fn().mockResolvedValue({ lat: 51.2, lng: 71.5 });
    const e = fakeEvent();

    geoRouteHandler(build, null, onRequestLocation)(e);

    expect(e.preventDefault).toHaveBeenCalled();
    expect(openSpy).toHaveBeenCalledWith("route?dest-only", "_blank");
    await vi.waitFor(() => expect(fakeWin.location.href).toBe("route?from=51.2,71.5"));
    openSpy.mockRestore();
  });

  it("should leave the link to open normally when coords are already known", () => {
    const onRequestLocation = vi.fn();
    const e = fakeEvent();

    geoRouteHandler(build, { lat: 51.2, lng: 71.5 }, onRequestLocation)(e);

    expect(e.stopPropagation).toHaveBeenCalled();
    expect(e.preventDefault).not.toHaveBeenCalled();
    expect(onRequestLocation).not.toHaveBeenCalled();
  });

  it("should not intercept when no location requester is provided", () => {
    const e = fakeEvent();
    geoRouteHandler(build, null, undefined)(e);
    expect(e.preventDefault).not.toHaveBeenCalled();
  });
});
