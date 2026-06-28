import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "@/lib/useAuth";

function AuthLoading() {
  return (
    <div className="flex min-h-svh items-center justify-center text-sm text-muted-foreground">
      Загрузка…
    </div>
  );
}

/** Requires any signed-in user; anonymous visitors go to /login. */
export function RequireAuth() {
  const { isAuthenticated, isPending } = useAuth();
  if (isPending) return <AuthLoading />;
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

/** Admin-only. Non-admins (and anonymous) are bounced to the home page —
 *  even if they type the admin URL directly. */
export function RequireAdmin() {
  const { isAdmin, isPending } = useAuth();
  if (isPending) return <AuthLoading />;
  return isAdmin ? <Outlet /> : <Navigate to="/" replace />;
}
