import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";

function formatRegisterErrors(data) {
  if (!data?.errors) return null;
  const e = data.errors;
  const parts = [];
  if (e.username) parts.push(`Username: ${e.username.join?.(" ") || e.username}`);
  if (e.password1) parts.push(`Password: ${e.password1.join?.(" ") || e.password1}`);
  if (e.password2) parts.push(`Confirm: ${e.password2.join?.(" ") || e.password2}`);
  if (e.email) parts.push(`Email: ${e.email.join?.(" ") || e.email}`);
  if (e.non_field_errors) parts.push(e.non_field_errors.join(" "));
  return parts.filter(Boolean).join(" · ") || data.detail || "Registration failed.";
}

export function RegisterPage() {
  const { registerRequest, registerConfirm } = useAuth();
  const navigate = useNavigate();
  const [phase, setPhase] = useState("details");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password1, setPassword1] = useState("");
  const [password2, setPassword2] = useState("");
  const [pendingId, setPendingId] = useState("");
  const [displayOtp, setDisplayOtp] = useState("");
  const [otpInput, setOtpInput] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function resetAll() {
    setPhase("details");
    setPendingId("");
    setDisplayOtp("");
    setOtpInput("");
    setError("");
  }

  async function onSubmitDetails(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await registerRequest({ username, email, password1, password2 });
      setPendingId(data.pending_id);
      setDisplayOtp(data.otp);
      setOtpInput("");
      setPhase("verify");
    } catch (err) {
      setError(formatRegisterErrors(err.data) || err.message);
    } finally {
      setBusy(false);
    }
  }

  async function onSubmitOtp(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await registerConfirm({ pendingId, otp: otpInput });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Verification failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="register-page-wrap">
      {phase === "verify" && displayOtp ? (
        <div className="otp-strip-outer">
          <div className="otp-strip" role="status" aria-live="polite">
            <p className="otp-strip-label">Your verification code — check here and type it below</p>
            <div className="otp-strip-digits" aria-label="Verification code">
              {displayOtp.split("").map((ch, i) => (
                <span key={i} className="otp-digit">
                  {ch}
                </span>
              ))}
            </div>
            <p className="otp-strip-note">Demo: code is shown on screen instead of SMS/email.</p>
          </div>
        </div>
      ) : null}

      <div className="auth-shell">
        <div className="auth-card">
          <p className="auth-eyebrow">Start in seconds</p>
          <h1 className="auth-title">Open your demo account</h1>
          <p className="auth-sub">
            {phase === "details"
              ? "Enter your details. We will ask for a one-time code next — you will see it at the top of this page."
              : "Enter the 6-digit code shown in the green bar above, then confirm."}
          </p>

          {phase === "details" ? (
            <form className="auth-form" onSubmit={onSubmitDetails}>
              {error ? (
                <div className="alert alert--error" role="alert">
                  {error}
                </div>
              ) : null}
              <label className="field">
                <span>Username</span>
                <input
                  className="input"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </label>
              <label className="field">
                <span>Email</span>
                <input
                  className="input"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                />
              </label>
              <label className="field">
                <span>Password</span>
                <input
                  className="input"
                  type="password"
                  autoComplete="new-password"
                  value={password1}
                  onChange={(e) => setPassword1(e.target.value)}
                  required
                />
              </label>
              <label className="field">
                <span>Confirm password</span>
                <input
                  className="input"
                  type="password"
                  autoComplete="new-password"
                  value={password2}
                  onChange={(e) => setPassword2(e.target.value)}
                  required
                />
              </label>
              <button className="btn btn--primary btn--block" type="submit" disabled={busy}>
                {busy ? "Sending code…" : "Continue — get verification code"}
              </button>
            </form>
          ) : (
            <form className="auth-form" onSubmit={onSubmitOtp}>
              {error ? (
                <div className="alert alert--error" role="alert">
                  {error}
                </div>
              ) : null}
              <label className="field">
                <span>Verification code</span>
                <input
                  className="input otp-input"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={8}
                  placeholder="000000"
                  value={otpInput}
                  onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  required
                />
              </label>
              <button className="btn btn--primary btn--block" type="submit" disabled={busy}>
                {busy ? "Creating account…" : "Verify & create account"}
              </button>
              <button
                type="button"
                className="btn btn--ghost btn--block"
                onClick={resetAll}
                disabled={busy}
              >
                Start over
              </button>
            </form>
          )}

          <p className="auth-foot">
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
