/**
 * Reusable form field with label, input, validation message, and show/hide
 * password support. Accessible by construction (label + input association,
 * aria-describedby for errors).
 */
import { useState } from "react";

interface FormFieldProps {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  placeholder?: string;
  required?: boolean;
  showPasswordToggle?: boolean;
}

export function FormField({
  id,
  label,
  type = "text",
  value,
  onChange,
  error,
  placeholder,
  required = false,
  showPasswordToggle = false,
}: FormFieldProps) {
  const [showPassword, setShowPassword] = useState(false);
  const inputId = id;
  const errorId = `${id}-error`;
  const isPassword = type === "password";
  const effectiveType = showPassword && isPassword ? "text" : isPassword ? "password" : type;

  return (
    <div className="space-y-2">
      <label
        htmlFor={inputId}
        className="block text-sm font-medium text-slate-700"
      >
        {label}{required ? <span className="text-destructive ml-0.5">*</span> : null}
      </label>
      <div className="relative">
        <input
          id={inputId}
          type={effectiveType}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          required={required}
          aria-invalid={error ? "true" : "false"}
          aria-describedby={error ? errorId : undefined}
          className={`flex w-full appearance-none rounded-md border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-primary focus:ring-2 focus:ring-primary/20 focus:outline-none disabled:cursor-not-allowed disabled:opacity-70 disabled:bg-slate-50 transition-all ${
            error ? "border-destructive focus:ring-destructive/20" : ""
          }`}
        />
        {showPasswordToggle && isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            aria-label={showPassword ? "Hide password" : "Show password"}
            className="absolute inset-y-0 right-0 mr-2 flex items-center px-2 text-slate-500 hover:text-slate-700"
          >
            {showPassword ? "🙈" : "👁️"}
          </button>
        )}
      </div>
      {error && (
        <p id={errorId} className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
