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
  const [emailOtpDestination, setEmailOtpDestination] = useState("");
  const [phoneMasked, setPhoneMasked] = useState("");
  const [demoEmailOtp, setDemoEmailOtp] = useState("");
  const [emailSent, setEmailSent] = useState(false);
  const [emailDemo, setEmailDemo] = useState(false);
  const [emailOtpInput, setEmailOtpInput] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function resetAll() {
    setPhase("details");
    setPendingId("");
    setVerifyHint("");
    setEmailOtpDestination("");
    setPhoneMasked("");
    setDemoEmailOtp("");
    setEmailSent(false);
    setEmailDemo(false);
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
      setPhoneMasked(typeof data.phone_masked === "string" ? data.phone_masked : "");
      setVerifyHint(
        typeof data.email_message === "string" && data.email_message.trim()
          ? data.email_message.trim()
          : ""
      );
      setEmailOtpDestination(
        typeof data.email_otp_sent_to === "string" && data.email_otp_sent_to
          ? data.email_otp_sent_to
          : (email || "").trim()
      );

      setEmailSent(!!data.email_sent);
      setEmailDemo(!!data.email_demo);
      const emailOtpStr = data.email_otp != null ? String(data.email_otp) : "";
      setDemoEmailOtp(emailDemo && emailOtpStr.length === 6 ? emailOtpStr : "");

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
      await registerConfirm({ pendingId, emailOtp: emailOtpInput });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(err.message || "Verification failed.");
    } finally {
      setBusy(false);
    }
  }

  const showDemoEmailStrip = phase === "verify" && demoEmailOtp;

  return (
    <div className="register-page-wrap">
      <div className="auth-shell">
        <div className="auth-card">
          <p className="auth-eyebrow">Start in seconds</p>
          <h1 className="auth-title">Open your AlyBank account</h1>
          <p className="auth-sub">
            {phase === "details"
              ? "Mobile number profile ke liye — verification code sirf email par jayega."
              : emailSent
                ? `6 digit code ${emailOtpDestination ? `${emailOtpDestination} ke inbox` : "aapki email"} mein bheja gaya (Spam / Promotions bhi dekhein).`
                : showDemoEmailStrip
                  ? "Neeche demo email code sirf tab dikhta hai jab server DEBUG + email demo mode mein ho."
                  : verifyHint || "Email OTP inbox check karein."}
          </p>

          {phase === "verify" && emailSent ? (
            <div className="alert alert--ok" role="status" style={{ marginBottom: "1rem" }}>
              <strong>Email bhej di gayi.</strong>{" "}
              {phoneMasked
                ? `Mobile profile ke liye save: ${phoneMasked}.`
                : "Mobile profile ke liye save ho jayega."}
            </div>
          ) : null}

          {phase === "verify" && !emailSent && verifyHint ? (
            <div className="alert alert--info" role="status">
              {verifyHint}
            </div>
          ) : null}

          {showDemoEmailStrip ? (
            <div className="otp-strip-outer" style={{ marginBottom: "1rem" }}>
              <div className="otp-strip otp-strip--demo" role="status" aria-live="polite">
                <p className="otp-strip-label">Email (demo / fallback only)</p>
                <div className="otp-strip-digits" aria-label="Email demo code">
                  {demoEmailOtp.split("").map((ch, i) => (
                    <span key={i} className="otp-digit">
                      {ch}
                    </span>
                  ))}
                </div>
                <p className="otp-strip-note">
                  Production inbox ke liye BREVO_SMTP_LOGIN + BREVO_SMTP_KEY + verified sender set karein.
                </p>
              </div>
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
                <span>Email (OTP isi inbox par jayega)</span>
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
                <span>Mobile number (profile)</span>
                <input
                  className="input"
                  type="tel"
                  autoComplete="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+923001234567"
                  required
                />
                <span
                  className="field-hint"
                  style={{ fontSize: "0.85rem", color: "var(--muted, #64748b)" }}
                >
                  Yeh number aapke account profile mein save hoga; SMS OTP nahi bheja jata.
                </span>
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
                {busy ? "Sending email…" : "Continue — email OTP bhejain"}
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
                <span>
                  Email verification code
                  {emailOtpDestination ? ` (${emailOtpDestination})` : ""}
                </span>
                <input
                  className="input otp-input"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={8}
                  placeholder="000000"
                  value={emailOtpInput}
                  onChange={(e) => setEmailOtpInput(e.target.value.replace(/\D/g, "").slice(0, 6))}
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
