import { authClient } from "./auth-client";

export interface AuthUser {
  id: string;
  email: string;
  name?: string | null;
  role?: string | null;
}

export interface AuthState {
  user: AuthUser | null;
  isPending: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

/** Single source of truth for auth in the UI. Wraps Better Auth's session so the
 *  rest of the app depends on a small, mockable shape (role-based admin check). */
export function useAuth(): AuthState {
  const { data, isPending } = authClient.useSession();

  // Local-dev escape hatch: with VITE_DEV_ADMIN=true you get an admin session without
  // running the auth server. Dead code in production builds (import.meta.env.DEV=false).
  if (import.meta.env.DEV && import.meta.env.VITE_DEV_ADMIN === "true") {
    return {
      user: { id: "dev", email: "dev@local", name: "Dev Admin", role: "admin" },
      isPending: false,
      isAuthenticated: true,
      isAdmin: true,
    };
  }

  const user = (data?.user as AuthUser | undefined) ?? null;
  return {
    user,
    isPending,
    isAuthenticated: user !== null,
    isAdmin: user?.role === "admin",
  };
}
