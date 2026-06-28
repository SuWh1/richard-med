import { useQuery } from "@tanstack/react-query";

import { type AuthUser, fetchMe, getToken } from "./auth-client";

export interface AuthState {
  user: AuthUser | null;
  isPending: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

/** Single source of truth for auth in the UI: fetches /auth/me from the stored token. */
export function useAuth(): AuthState {
  const token = getToken();
  const { data, isPending } = useQuery({
    queryKey: ["me", token],
    queryFn: fetchMe,
    enabled: token !== null,
    retry: false,
    staleTime: 60_000,
  });

  const user = token !== null ? (data ?? null) : null;
  return {
    user,
    isPending: token !== null && isPending,
    isAuthenticated: user !== null,
    isAdmin: user?.role === "admin",
  };
}
