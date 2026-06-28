import { createAuthClient } from "better-auth/react";
import { adminClient, emailOTPClient, jwtClient } from "better-auth/client/plugins";

// The Better Auth server (Vercel function in prod, local auth server in dev).
// Same-origin /api/auth by default; override with VITE_AUTH_URL in dev. Better Auth
// needs an absolute URL, so resolve the relative path against the current origin.
const origin = typeof window !== "undefined" ? window.location.origin : "http://localhost";
const baseURL = import.meta.env.VITE_AUTH_URL || `${origin}/api/auth`;

export const authClient = createAuthClient({
  baseURL,
  plugins: [adminClient(), emailOTPClient(), jwtClient()],
});

/** Bearer header with the Better Auth JWT for the FastAPI backend (admin endpoints). */
export async function authHeader(): Promise<Record<string, string>> {
  try {
    const { data } = await authClient.token();
    return data?.token ? { Authorization: `Bearer ${data.token}` } : {};
  } catch {
    return {};
  }
}

export const { signIn, signUp, signOut, useSession, emailOtp } = authClient;
