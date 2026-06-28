// Native email/password auth against our FastAPI backend (/api/v1/auth).
const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8001/api/v1";
const TOKEN_KEY = "auth_token";

export interface AuthUser {
  id: number;
  email: string;
  name: string | null;
  role: string;
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/** Bearer header for backend admin endpoints. */
export function authHeader(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function postAuth(
  path: string,
  body: unknown,
): Promise<{ token: string; user: AuthUser }> {
  const res = await fetch(`${BASE}/auth${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? "Не удалось выполнить запрос");
  localStorage.setItem(TOKEN_KEY, data.token);
  return data;
}

export function signup(
  email: string,
  password: string,
  name?: string,
): Promise<{ user: AuthUser }> {
  return postAuth("/signup", { email, password, name });
}

export function login(email: string, password: string): Promise<{ user: AuthUser }> {
  return postAuth("/login", { email, password });
}

export function logout(): void {
  clearToken();
}

export async function fetchMe(): Promise<AuthUser | null> {
  if (!getToken()) return null;
  const res = await fetch(`${BASE}/auth/me`, { headers: authHeader() });
  if (!res.ok) {
    clearToken();
    return null;
  }
  return res.json();
}
