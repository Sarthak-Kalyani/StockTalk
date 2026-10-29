/**
 * Sign-up form. Creates an account via the Express.js backend (email + password
 * + optional profile metadata). The backend hashes the password with bcrypt and
 * issues a JWT access_token on success.
 */
import { useState } from "react";
import { FormField } from "./FormField";
import { api } from "../services/api";
import { setAuthToken, setStoredToken } from "../auth";

interface SignUpFormProps {
  onSwitchToSignIn: () => void;
}

export default function SignUpForm({ onSwitchToSignIn }: SignUpFormProps) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  // Password strength rules
  const passwordRules = {
    length: password.length >= 8,
    lower: /[a-z]/.test(password),
    upper: /[A-Z]/.test(password),
    digit: /[0-9]/.test(password),
  };
  const passwordStrong =
    passwordRules.length &&
    passwordRules.lower &&
    passwordRules.upper &&
    passwordRules.digit;

  const validate = (): boolean => {
    const next: Record<string, string> = {};
    if (!fullName.trim()) next.fullName = "Full name is required";
    if (!email.trim()) next.email = "Email address is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
      next.email = "Please enter a valid email address";
    if (!password) next.password = "Password is required";
    else if (!passwordStrong)
      next.password =
        "Use 8+ characters with uppercase, lowercase, and a number";
    if (password !== confirmPassword) next.confirmPassword = "Passwords do not match";
    if (!businessName.trim()) next.businessName = "Business name is required";
    setFieldErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!validate()) return;

    setLoading(true);
    try {
      const data = await api.register({
        email: email.trim(),
        password,
        role: "shopkeeper",
        business_name: businessName.trim(),
      });

      const token = data.access_token as string;

      setStoredToken(token);
      setAuthToken(token);

      setError(null);
      onSwitchToSignIn();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Sign up failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <h2 className="text-2xl font-bold text-slate-900 text-balance">
          Create an account
        </h2>
        <p className="mt-2 text-sm text-slate-600">
          Join StockTalk to manage inventory and collaborate with suppliers.
        </p>
      </div>

      <FormField
        id="fullName"
        label="Full name"
        value={fullName}
        onChange={setFullName}
        placeholder="Jane Doe"
        required
        error={fieldErrors.fullName}
      />
      <FormField
        id="email"
        label="Email address"
        type="email"
        value={email}
        onChange={setEmail}
        placeholder="you@company.com"
        required
        error={fieldErrors.email}
      />
      <FormField
        id="businessName"
        label="Business name"
        value={businessName}
        onChange={setBusinessName}
        placeholder="Acme Traders"
        required
        error={fieldErrors.businessName}
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
        error={fieldErrors.password || undefined}
      />
      {/* Password strength guidance (inline, non-blocking) */}
      {password && (
        <div className="mt-1 space-y-1">
          <span className="text-xs font-medium text-slate-600">Password strength</span>
          <div className="flex gap-1">
            {[passwordRules.length, passwordRules.lower, passwordRules.upper, passwordRules.digit].map(
              (pass, i) => (
                <span
                  key={i}
                  className={`text-[10px] rounded px-1.5 py-0.5 ${
                    pass
                      ? "bg-green-100 text-green-700"
                      : "bg-slate-200 text-slate-500"
                  }`}
                >
                  {["8+ chars", "lowercase", "uppercase", "number"][i]}
                </span>
              ),
            )}
          </div>
        </div>
      )}
      <FormField
        id="confirmPassword"
        label="Confirm password"
        type="password"
        value={confirmPassword}
        onChange={setConfirmPassword}
        placeholder="••••••••"
        required
        showPasswordToggle
        error={fieldErrors.confirmPassword}
      />

      <button
        type="submit"
        disabled={loading}
        className="flex w-full justify-center py-3 px-4 rounded-md border border-transparent shadow-sm text-sm font-semibold text-white bg-primary hover:bg-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-60 disabled:cursor-not-allowed transition-all"
      >
        {loading ? "Creating account…" : "Create account"}
      </button>

      {error && (
        <div className="rounded-md border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive" role="alert">
          {error}
        </div>
      )}

      <p className="mt-4 text-center text-sm text-slate-600">
        Already have an account?{" "}
        <button
          type="button"
          onClick={onSwitchToSignIn}
          className="font-medium text-primary hover:text-primary-hover focus:outline-none focus:underline"
        >
          Sign in
        </button>
      </p>
    </form>
  );
}
