/**
 * Sign-in form. Email + password, submitted to the Express.js backend.
 * On success the backend returns a JWT access_token which the client stores
 * and sends as `Authorization: Bearer <token>` on authenticated requests.
 * Never displays or asks the user to paste a JWT.
 */
import { useState } from "react";
import { FormField } from "./FormField";
import { api } from "../services/api";
import { setAuthToken, setStoredToken } from "../auth";

interface SignInFormProps {
  onAuthenticated: (user: { id: number; email: string; role: string }) => void;
}

export default function SignInForm({ onAuthenticated }: SignInFormProps) {
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

      const user = data.user as { id: number; email: string; role: string };
      const token = data.access_token as string;

      // Persist the token and tell the API client to use it
      setStoredToken(token);
      setAuthToken(token);

      onAuthenticated(user);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Sign in failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 text-balance">Sign in</h2>
        <p className="mt-2 text-sm text-slate-600">
          Welcome back to StockTalk. Enter your credentials to continue.
        </p>
      </div>

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

      <p className="mt-4 text-center text-sm text-slate-600">
        Don&rsquo;t have an account?{" "}
        <button
          type="button"
          className="font-medium text-primary hover:text-primary-hover focus:outline-none focus:underline"
        >
          Create an account
        </button>
      </p>
    </form>
  );
}
