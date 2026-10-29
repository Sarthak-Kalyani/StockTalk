/**
 * StockTalk API client.
 *
 * Points at the Express.js backend. In development this defaults to
 * http://localhost:8000; override with VITE_API_URL.
 *
 * Authentication is JWT-based: the client stores the access_token returned by
 * /api/auth/login or /api/auth/register and sends it as
 * `Authorization: Bearer <token>` on every authenticated request.
 */
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

let token: string | null = null;

export function setAuthToken(t: string | null) {
  token = t;
}

export function getAuthToken(): string | null {
  return token;
}

async function request(path: string, init?: RequestInit) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    headers,
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error?.message || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  health: () => request("/health"),

  register: (body: {
    email: string;
    password: string;
    role?: string;
    business_name: string;
    address?: string;
    phone?: string;
    gst_number?: string;
  }) => request("/api/auth/register", { method: "POST", body: JSON.stringify(body) }),

  login: (body: { email: string; password: string }) =>
    request("/api/auth/login", { method: "POST", body: JSON.stringify(body) }),

  logout: () => request("/api/auth/logout", { method: "POST" }),

  me: () => request("/api/auth/me"),

  getProfile: () => request("/api/auth/me/profile"),

  updateProfile: (body: {
    business_name?: string;
    address?: string;
    phone?: string;
    gst_number?: string;
  }) =>
    request("/api/auth/me/profile", {
      method: "PATCH",
      body: JSON.stringify(body),
    }),

  completeProfile: (body: { business_name: string }) =>
    request("/api/auth/me/profile/complete", {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
