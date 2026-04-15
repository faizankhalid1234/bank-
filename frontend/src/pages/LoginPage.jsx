import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login({ identifier, password });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Sign in failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <p className="auth-eyebrow">Welcome back</p>
        <h1 className="auth-title">Sign in</h1>
        <p className="auth-sub">
          Apna <strong>username</strong> ya <strong>email</strong> ek hi box mein likho, phir
          password — is se autofill wala masla nahi aata.
        </p>
        <form className="auth-form" onSubmit={onSubmit}>
          {error ? (
            <div className="alert alert--error" role="alert">
              {error}
            </div>
          ) : null}
          <label className="field">
            <span>Username ya email</span>
            <input
              className="input"
              type="text"
              autoComplete="username"
              placeholder="username ya you@example.com"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
            />
          </label>
          <label className="field">
            <span>Password</span>
            <input
              className="input"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <button className="btn btn--primary btn--block" type="submit" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="auth-foot">
          New here? <Link to="/register">Open an account</Link>
        </p>
      </div>
    </div>
  );
}
