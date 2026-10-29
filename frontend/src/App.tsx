import { useState, useEffect, useCallback } from "react";
import { BrowserRouter, Routes, Route, Navigate, Link } from "react-router-dom";
import { api } from "./services/api";
import {
  getSession,
  setAuthToken,
  onAuthStateChange,
  signOut,
  type SessionLike,
} from "./auth";
import RegisterPage from "./pages/RegisterPage";
import SignInPage from "./pages/SignInPage";

function App() {
  const [session, setSession] = useState<SessionLike | null>(null);
  const [health, setHealth] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state from stored token on mount
  useEffect(() => {
    const initial = getSession();
    setSession(initial);
    setAuthToken(initial.access_token);

    const { subscription } = onAuthStateChange((next) => {
      setSession(next);
      setAuthToken(next.access_token);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Fetch health when an authenticated session exists
  useEffect(() => {
    if (!session?.access_token) {
      setHealth(null);
      setError(null);
      setLoading(false);
      return;
    }

    api.health()
      .then((data) => {
        setHealth(data);
        setError(null);
      })
      .catch((err) => {
        setError(err.message);
        setHealth(null);
      })
      .finally(() => setLoading(false));
  }, [session?.access_token]);

  const handleAuthenticated = useCallback(() => {
    api.health()
      .then((data) => {
        setHealth(data);
        setError(null);
      })
      .catch((err) => {
        setError(err.message);
        setHealth(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleSignOut = () => {
    signOut();
    setSession(null);
    setAuthToken(null);
    setHealth(null);
    setError(null);
    setLoading(true);
  };

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-white text-gray-800">
        {session?.access_token ? (
          <div className="p-6 md:p-12">
            <header className="mb-12 flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 tracking-tight">StockTalk</h1>
                <p className="mt-2 text-gray-600">
                  B2B Inventory and Supplier Communication Platform
                </p>
              </div>
              <nav className="flex items-center gap-3">
                <Link
                  to="/"
                  className="px-3 py-2 rounded-md bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
                >
                  Dashboard
                </Link>
                <button
                  onClick={handleSignOut}
                  className="px-3 py-2 rounded-md bg-red-600 text-white text-sm font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 transition-colors"
                >
                  Sign out
                </button>
              </nav>
            </header>

            <section className="max-w-2xl">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Backend connection</h2>
              <div className="rounded-lg border p-4 bg-gray-50">
                <p className="text-sm font-mono text-gray-700 mb-2">
                  GET <span className="text-indigo-600">/api/v1/health</span>
                </p>
                {loading ? (
                  <p className="text-sm text-gray-500 italic">Connecting…</p>
                ) : error ? (
                  <p className="text-sm text-red-600">
                    Unable to reach backend: {error}
                  </p>
                ) : (
                  <div className="flex items-center gap-2">
                    <span className="inline-flex items-center gap-1.5">
                      <span className="w-2 h-2 rounded-full bg-green-500" />
                      <span className="text-sm font-medium text-green-700">Backend reachable</span>
                    </span>
                    <pre className="ml-4 text-xs text-gray-500 bg-white p-2 rounded border border-gray-100">
                      {JSON.stringify(health, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </section>

            <footer className="mt-12 pt-6 border-t border-gray-200 text-xs text-gray-500">
              StockTalk · Group GC_2026_018 · JWT authentication with Express backend
            </footer>
          </div>
        ) : (
          <div className="p-6 md:p-12">
            <Routes>
              <Route
                path="/signin"
                element={<SignInPage onAuthenticated={handleAuthenticated} />}
              />
              <Route
                path="/register"
                element={<RegisterPage onAuthenticated={handleAuthenticated} />}
              />
              <Route path="/" element={<Navigate to="/signin" replace />} />
            </Routes>
          </div>
        )}
      </div>
    </BrowserRouter>
  );
}

export default App;
