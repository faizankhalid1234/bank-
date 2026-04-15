import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login({ username, email, password });
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
          Username <strong>ya</strong> email — <strong>ek hi</strong> bharo (dono bharo to dono same account ke hon). Galat
          autofill email khali karke dubara try karein agar password sahi ho ke bhi error aaye.
        </p>
        <form className="auth-form" onSubmit={onSubmit}>
          {error ? (
            <div className="alert alert--error" role="alert">
              {error}
            </div>
          ) : null}
          <label className="field">
            <span>Username</span>
            <input
              className="input"
              type="text"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </label>
          <label className="field">
            <span>Email</span>
            <input
              className="input"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <p className="field-hint">Username or email — fill at least one.</p>
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
