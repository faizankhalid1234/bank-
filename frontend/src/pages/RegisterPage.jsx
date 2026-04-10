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
  if (e.phone) parts.push(`Mobile: ${e.phone.join?.(" ") || e.phone}`);
  if (e.non_field_errors) parts.push(e.non_field_errors.join(" "));
  return parts.filter(Boolean).join(" · ") || data.detail || "Registration failed.";
}

export function RegisterPage() {
  const { registerRequest, registerConfirm } = useAuth();
  const navigate = useNavigate();
  const [phase, setPhase] = useState("details");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password1, setPassword1] = useState("");
  const [password2, setPassword2] = useState("");
  const [pendingId, setPendingId] = useState("");
  const [verifyHint, setVerifyHint] = useState("");
  const [demoOtp, setDemoOtp] = useState("");
  const [demoEmailOtp, setDemoEmailOtp] = useState("");
  const [otpInput, setOtpInput] = useState("");
  const [emailOtpInput, setEmailOtpInput] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function resetAll() {
    setPhase("details");
    setPendingId("");
    setVerifyHint("");
    setDemoOtp("");
    setDemoEmailOtp("");
    setOtpInput("");
    setEmailOtpInput("");
    setError("");
  }

  async function onSubmitDetails(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await registerRequest({ username, email, phone, password1, password2 });
      setPendingId(data.pending_id);
      setVerifyHint(
        [data.message, data.email_message].filter(Boolean).join(" ") || ""
      );
      setDemoOtp(data.otp && String(data.otp).length === 6 ? String(data.otp) : "");
      setDemoEmailOtp(
        data.email_otp && String(data.email_otp).length === 6 ? String(data.email_otp) : ""
      );
      setOtpInput("");
      setEmailOtpInput("");
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
      await registerConfirm({ pendingId, otp: otpInput, emailOtp: emailOtpInput });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Verification failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="register-page-wrap">
      {phase === "verify" && (demoOtp || demoEmailOtp) ? (
        <div className="otp-strip-outer">
          {demoOtp ? (
            <div className="otp-strip otp-strip--demo" role="status" aria-live="polite">
              <p className="otp-strip-label">SMS (demo) — yahin se code copy karein</p>
              <div className="otp-strip-digits" aria-label="SMS verification code">
                {demoOtp.split("").map((ch, i) => (
                  <span key={i} className="otp-digit">
                    {ch}
                  </span>
                ))}
              </div>
              <p className="otp-strip-note">
                Real SMS: Twilio par number verify + limit check. Demo tab dikhta hai jab SMS fail ho (trial/limit).
              </p>
            </div>
          ) : null}
          {demoEmailOtp ? (
            <div
              className="otp-strip otp-strip--demo"
              style={{ marginTop: demoOtp ? "0.75rem" : 0 }}
              role="status"
              aria-live="polite"
            >
              <p className="otp-strip-label">Email (demo) — yahin se code copy karein</p>
              <div className="otp-strip-digits" aria-label="Email verification code">
                {demoEmailOtp.split("").map((ch, i) => (
                  <span key={i} className="otp-digit">
                    {ch}
                  </span>
                ))}
              </div>
              <p className="otp-strip-note">
                Real email: SMTP .env mein set karo — warna development par terminal/console par OTP dikhta hai.
              </p>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="auth-shell">
        <div className="auth-card">
          <p className="auth-eyebrow">Start in seconds</p>
          <h1 className="auth-title">Open your demo account</h1>
          <p className="auth-sub">
            {phase === "details"
              ? "Apna asli email aur mobile likho — SMS aur email dono par alag codes aayenge; dono ke baghair account nahi banega."
              : demoOtp || demoEmailOtp
                ? "Neeche demo boxes mein codes — dono fields mein likhein."
                : "SMS wala code mobile par, email wala Gmail / inbox mein — dono yahan likhein."}
          </p>

          {phase === "verify" && verifyHint ? (
            <div className="alert alert--info" role="status">
              {verifyHint}
            </div>
          ) : null}

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
                  required
                />
              </label>
              <label className="field">
                <span>Mobile number</span>
                <input
                  className="input"
                  type="tel"
                  autoComplete="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+923001234567"
                  required
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
                <span>SMS verification code</span>
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
              <label className="field">
                <span>Email verification code</span>
                <input
                  className="input otp-input"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={8}
                  placeholder="000000"
                  value={emailOtpInput}
                  onChange={(e) =>
                    setEmailOtpInput(e.target.value.replace(/\D/g, "").slice(0, 6))
                  }
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
