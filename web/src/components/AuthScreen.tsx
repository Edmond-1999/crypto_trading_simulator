import type { FormEvent } from "react";
import { RefreshCw, ShieldCheck, Zap } from "lucide-react";
import type { AuthMode } from "../types";

type Props = {
  mode: AuthMode;
  email: string;
  password: string;
  loading: boolean;
  error: string;
  onEmailChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onModeChange: (mode: AuthMode) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
};

export default function AuthScreen({
  mode,
  email,
  password,
  loading,
  error,
  onEmailChange,
  onPasswordChange,
  onModeChange,
  onSubmit,
}: Props) {
  const isLogin = mode === "login";

  return (
    <main className="auth-screen">
      <form className="auth-card" onSubmit={onSubmit}>
        <div className="brand auth-brand">
          <span className="brand-mark">
            <Zap size={22} fill="currentColor" />
          </span>
          <span className="brand-name">
            NEXA<span>TRADE</span>
          </span>
        </div>

        <div className="auth-intro">
          <span className="eyebrow">CRYPTO SPOT SIMULATOR</span>
          <h1>{isLogin ? "Welcome back" : "Create your account"}</h1>
          <p>
            {isLogin
              ? "Sign in to manage your demo portfolio and simulated trades."
              : "Create an account to get started with your demo wallet."}
          </p>
        </div>

        {error && (
          <div className="error-banner" role="alert">
            {error}
          </div>
        )}

        <label className="field-label" htmlFor="auth-email">
          Email address
        </label>
        <input
          id="auth-email"
          className="form-input"
          type="email"
          autoComplete="email"
          placeholder="you@example.com"
          value={email}
          onChange={(event) => onEmailChange(event.target.value)}
          required
        />

        <label className="field-label" htmlFor="auth-password">
          Password
        </label>
        <input
          id="auth-password"
          className="form-input"
          type="password"
          autoComplete={isLogin ? "current-password" : "new-password"}
          placeholder={isLogin ? "Enter your password" : "At least 12 characters"}
          value={password}
          onChange={(event) => onPasswordChange(event.target.value)}
          minLength={isLogin ? undefined : 12}
          required
        />

        <button className="primary-button auth-submit" type="submit" disabled={loading}>
          {loading && <RefreshCw size={16} className="spin" />}
          {loading ? "Please wait…" : isLogin ? "Sign in" : "Create account"}
        </button>

        <div className="auth-switch">
          <span>{isLogin ? "Don't have an account?" : "Already registered?"}</span>
          <button
            type="button"
            className="text-button"
            onClick={() => onModeChange(isLogin ? "register" : "login")}
          >
            {isLogin ? "Create one" : "Sign in"}
          </button>
        </div>

        <p className="auth-security">
          <ShieldCheck size={15} />
          Your account is protected by token-based authentication.
        </p>
      </form>
    </main>
  );
}
