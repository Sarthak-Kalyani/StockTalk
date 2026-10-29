/**
 * StockTalk client-side authentication.
 *
 * Authentication is handled by the Express.js backend using JWT (JSON Web Tokens).
 *
 * Flow:
 *   - signUp / signIn call POST /api/auth/register and POST /api/auth/login.
 *   - The backend returns an access_token which we store in memory and in
 *     localStorage so the session survives page reloads.
 *   - Every authenticated request sends the token as `Authorization: Bearer <token>`.
 *   - signOut clears the stored token.
 *   - onAuthStateChange reads the stored token on load and whenever it changes.
 */

const TOKEN_KEY = "stocktalk_token";

export interface AuthUser {
  id: number;
  email: string;
  role: string;
  status: string;
}

export interface SessionLike {
  access_token: string | null;
  user: AuthUser | null;
}

/** Read the stored JWT from localStorage. */
export function getStoredToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

/** Tell all modules to use this token for authenticated requests. */
export function setAuthToken(_t: string | null) {
  // Stored in-memory by consumers (api.ts keeps its own copy). Kept as a
  // no-op here so the API client remains the single source of truth.
}

/** Persist the JWT to localStorage and memory. */
export function setStoredToken(t: string | null) {
  if (typeof localStorage === "undefined") return;
  if (t) {
    localStorage.setItem(TOKEN_KEY, t);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

/** The current session, reconstructed from the stored token (no backend call). */
export function getSession(): SessionLike {
  const access_token = getStoredToken();
  let user: AuthUser | null = null;
  if (access_token) {
    try {
      const payload = JSON.parse(atob(access_token.split(".")[1]));
      user = {
        id: payload.userId,
        email: payload.email ?? "",
        role: payload.role ?? "shopkeeper",
        status: payload.status ?? "active",
      };
    } catch {
      // Malformed token — treat as no session
    }
  }
  return { access_token, user };
}

/** Is there an authenticated session? */
export function isAuthenticated(): boolean {
  return getStoredToken() != null;
}

/** Get the current authenticated user from the stored token, if any. */
export function getUser(): AuthUser | null {
  return getSession().user;
}

/** Listen to auth state changes. Calls the callback with the current session
 *  immediately and whenever the stored token changes (storage event or manual set). */
export function onAuthStateChange(
  callback: (session: SessionLike) => void
): { subscription: { unsubscribe: () => void } } {
  callback(getSession());

  let listening = true;

  const onStorage = (e: StorageEvent) => {
    if (!listening && e.key === TOKEN_KEY) {
      callback(getSession());
    }
  };

  // Poll fallback for tabs that don't dispatch storage events to themselves
  let lastToken = getStoredToken();
  const timer = setInterval(() => {
    if (!listening) return;
    const t = getStoredToken();
    if (t !== lastToken) {
      lastToken = t;
      callback(getSession());
    }
  }, 1000);

  window.addEventListener("storage", onStorage);

  return {
    subscription: {
      unsubscribe: () => {
        listening = false;
        window.removeEventListener("storage", onStorage);
        clearInterval(timer);
      },
    },
  };
}

/** Clear the stored token (client-side logout). */
export function signOut() {
  setStoredToken(null);
}
