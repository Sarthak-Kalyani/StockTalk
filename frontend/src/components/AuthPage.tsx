/**
 * StockTalk authentication page.
 *
 * Split-screen layout on desktop: brand story on the left, sign-in/sign-up
 * card on the right. Single-column on mobile.
 *
 * Authentication is handled by Supabase Auth (email/password). The raw JWT is
 * never shown to the user.
 */
import { useState } from "react";
import SignInForm from "./SignInForm";
import SignUpForm from "./SignUpForm";

type AuthMode = "signin" | "signup";

interface AuthPageProps {
  onAuthenticated: (user: { id: number; email: string; role: string }) => void;
}

export default function AuthPage({ onAuthenticated }: AuthPageProps) {
  const [mode, setMode] = useState<AuthMode>("signin");

  const handleAuthenticated = (
    user: { id: number; email: string; role: string },
  ) => {
    onAuthenticated(user);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Desktop: split screen */}
      <div className="hidden lg:flex h-screen w-full overflow-hidden">
        {/* Left: brand + benefits */}
        <div className="flex h-full w-1/2 flex-col justify-center px-12 lg:px-16 bg-white border-r border-slate-200">
          <div className="flex items-center gap-2 mb-10">
            <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center shadow-md">
              <svg
                className="w-5 h-5 text-white"
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

          <h1 className="text-3xl lg:text-4xl font-bold text-slate-900 text-balance leading-tight mb-6">
            Manage inventory. Strengthen supplier relationships.
          </h1>

          <p className="text-lg text-slate-600 leading-relaxed mb-10 max-w-lg">
            StockTalk is the B2B inventory and supplier communication platform
            for growing businesses. Track stock, share catalogues, place orders,
            and settle invoices — all in one place.
          </p>

          <div className="space-y-6">
            {[
              {
                title: "Real-time inventory visibility",
                desc: "Know exactly what&rsquo;s in stock, where it is, and when to reorder.",
              },
              {
                title: "Supplier collaboration",
                desc: "Share product catalogues, receive orders, and chat with suppliers.",
              },
              {
                title: "Business operations in one place",
                desc: "Bills, payments, and purchasing — no more jumping between tools.",
              },
            ].map((benefit, i) => (
              <div key={i} className="flex items-start gap-4">
                <div className="mt-0.5 flex shrink-0 items-center justify-center w-7 h-7 rounded-md bg-primary/10 text-primary">
                  <span className="text-sm">{i + 1}</span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">
                    {benefit.title}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">{benefit.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: auth card */}
        <div className="flex h-full w-1/2 flex-col items-center justify-center bg-white px-8 lg:px-0">
          <div className="w-full max-w-md">
            {mode === "signin" ? (
              <SignInForm onAuthenticated={handleAuthenticated} />
            ) : (
              <SignUpForm onSwitchToSignIn={() => setMode("signin")} />
            )}
          </div>
        </div>
      </div>

      {/* Mobile: single column */}
      <div className="lg:hidden min-h-screen flex flex-col bg-slate-50">
        <div className="flex-1 flex flex-col justify-center px-6 py-12">
          <div className="flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shadow-md">
              <svg
                className="w-4 h-4 text-white"
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
            <span className="text-xl font-bold tracking-tight text-slate-900">
              StockTalk
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 text-center mb-2">
            Manage inventory. Strengthen supplier relationships.
          </h1>
          <p className="text-sm text-slate-600 text-center mb-10 max-w-md mx-auto">
            StockTalk is the B2B inventory and supplier communication platform
            for growing businesses.
          </p>

          <div className="w-full max-w-md mx-auto">
            {mode === "signin" ? (
              <SignInForm onAuthenticated={handleAuthenticated} />
            ) : (
              <SignUpForm onSwitchToSignIn={() => setMode("signin")} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
