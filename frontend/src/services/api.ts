/**
 * StockTalk API client.
 *
 * Points at the FastAPI backend. In development this defaults to
 * http://localhost:8000; override with VITE_API_URL.
 */
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path: string, init?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json();
}

export const api = {
  health: () => request("/health"),
};
