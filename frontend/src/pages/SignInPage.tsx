/**
 * StockTalk Sign In Page.
 *
 * Dedicated sign-in page (separate from the split-screen AuthPage).
 * Users sign in with email + password. On success the backend issues a JWT
 * access_token which is stored and used for all authenticated requests.
 */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../services/api";
import { setAuthToken, setStoredToken } from "../auth";
import { FormField } from "../components/FormField";

export default function SignInPage({
  onAuthenticated,
}: {
  onAuthenticated: () => void;
}) {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await api.login({ email, password });

      const token = data.access_token as string;

      setStoredToken(token);
      setAuthToken(token);

      onAuthenticated();
      navigate("/");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Sign in failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-12">
      <div className="max-w-md w-full bg-white rounded-xl shadow-sm border border-slate-200 p-8">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary flex items-center justify-center shadow-md">
              <svg
                className="w-6 h-6 text-white"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <span className="text-2xl font-bold tracking-tight text-slate-900">
              StockTalk
            </span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Sign in</h2>
          <p className="text-sm text-slate-600">
            Welcome back to StockTalk. Enter your credentials to continue.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <FormField
            id="email"
            label="Email address"
            type="email"
            value={email}
            onChange={setEmail}
            placeholder="you@company.com"
            required
          />
          <FormField
            id="password"
            label="Password"
            type="password"
            value={password}
            onChange={setPassword}
            placeholder="••••••••"
            required
            showPasswordToggle
          />

          <div className="flex items-center justify-between">
            <button
              type="submit"
              disabled={loading}
              className="flex w-full justify-center py-3 px-4 rounded-md border border-transparent shadow-sm text-sm font-semibold text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-60 disabled:cursor-not-allowed transition-all"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </div>

          {error && (
            <div className="rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive" role="alert">
              {error}
            </div>
          )}
        </form>

        <p className="mt-6 text-center text-sm text-slate-600">
          Don&rsquo;t have an account?{" "}
          <Link
            to="/register"
            className="font-medium text-primary hover:text-primary-hover focus:underline"
          >
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
