import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useAuth, type AuthState } from "@/lib/useAuth";
import { RequireAdmin, RequireAuth } from "./RouteGuards";

vi.mock("@/lib/useAuth", () => ({ useAuth: vi.fn() }));

const setAuth = (s: Partial<AuthState>) =>
  vi.mocked(useAuth).mockReturnValue({
    user: null,
    isPending: false,
    isAuthenticated: false,
    isAdmin: false,
    ...s,
  });

function renderGuard(Guard: () => React.ReactElement) {
  return render(
    <MemoryRouter initialEntries={["/secret"]}>
      <Routes>
        <Route element={<Guard />}>
          <Route path="/secret" element={<div>SECRET</div>} />
        </Route>
        <Route path="/" element={<div>HOME</div>} />
        <Route path="/login" element={<div>LOGIN</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("RequireAdmin", () => {
  beforeEach(() => vi.clearAllMocks());

  it("should render the protected content for an admin", () => {
    setAuth({ isAuthenticated: true, isAdmin: true });
    renderGuard(RequireAdmin);
    expect(screen.getByText("SECRET")).toBeInTheDocument();
  });

  it("should redirect a logged-in non-admin away from admin routes", () => {
    setAuth({ isAuthenticated: true, isAdmin: false });
    renderGuard(RequireAdmin);
    expect(screen.queryByText("SECRET")).not.toBeInTheDocument();
    expect(screen.getByText("HOME")).toBeInTheDocument();
  });

  it("should redirect an anonymous visitor away from admin routes", () => {
    setAuth({ isAuthenticated: false, isAdmin: false });
    renderGuard(RequireAdmin);
    expect(screen.queryByText("SECRET")).not.toBeInTheDocument();
  });
});

describe("RequireAuth", () => {
  beforeEach(() => vi.clearAllMocks());

  it("should render content for an authenticated user", () => {
    setAuth({ isAuthenticated: true });
    renderGuard(RequireAuth);
    expect(screen.getByText("SECRET")).toBeInTheDocument();
  });

  it("should send an anonymous visitor to login", () => {
    setAuth({ isAuthenticated: false });
    renderGuard(RequireAuth);
    expect(screen.getByText("LOGIN")).toBeInTheDocument();
  });
});
