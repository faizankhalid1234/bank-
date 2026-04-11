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
  const [phoneMasked, setPhoneMasked] = useState("");
  /** Only when API explicitly in demo mode — not when real SMS/email sent */
  const [demoSmsOtp, setDemoSmsOtp] = useState("");
  const [demoEmailOtp, setDemoEmailOtp] = useState("");
  const [delivery, setDelivery] = useState({
    smsSent: false,
    emailSent: false,
    smsDemo: false,
    emailDemo: false,
    smsFailed: false,
    smsTrialUnverified: false,
    smsToFixedVerified: false,
  });
  const [otpInput, setOtpInput] = useState("");
  const [emailOtpInput, setEmailOtpInput] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function resetAll() {
    setPhase("details");
    setPendingId("");
    setVerifyHint("");
    setPhoneMasked("");
    setDemoSmsOtp("");
    setDemoEmailOtp("");
    setDelivery({
      smsSent: false,
      emailSent: false,
      smsDemo: false,
      emailDemo: false,
      smsFailed: false,
      smsTrialUnverified: false,
      smsToFixedVerified: false,
    });
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
      setPhoneMasked(typeof data.phone_masked === "string" ? data.phone_masked : "");
      setVerifyHint([data.message, data.email_message].filter(Boolean).join(" ") || "");

      const smsDemo = !!data.sms_demo;
      const emailDemo = !!data.email_demo;
      const otpStr = data.otp != null ? String(data.otp) : "";
      const emailOtpStr = data.email_otp != null ? String(data.email_otp) : "";

      setDemoSmsOtp(smsDemo && otpStr.length === 6 ? otpStr : "");
      setDemoEmailOtp(emailDemo && emailOtpStr.length === 6 ? emailOtpStr : "");

      setDelivery({
        smsSent: !!data.sms_sent,
        emailSent: !!data.email_sent,
        smsDemo,
        emailDemo,
        smsFailed: !!data.sms_failed,
        smsTrialUnverified: !!data.sms_trial_unverified,
        smsToFixedVerified: !!data.sms_to_fixed_verified,
      });

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

  const bothReal = delivery.smsSent && delivery.emailSent;
  const showDemoPanel = phase === "verify" && (demoSmsOtp || demoEmailOtp);

  return (
    <div className="register-page-wrap">
      <div className="auth-shell">
        <div className="auth-card">
          <p className="auth-eyebrow">Start in seconds</p>
          <h1 className="auth-title">Open your AlyBank account</h1>
          <p className="auth-sub">
            {phase === "details"
              ? "Apna sahi mobile number aur Gmail likho — SMS par ek code, email par alag code aayega."
              : bothReal
                ? "Dono codes real tarah se bheje gaye: mobile SMS + Gmail inbox (Spam/Promotions bhi dekhein)."
                : showDemoPanel
                  ? "Neeche demo codes sirf tab dikhte hain jab server SMS/email demo mode mein ho — production mein yeh boxes nahi aate."
                  : "Jo code SMS par aaya ho aur jo Gmail par, dono yahan likhein."}
          </p>

          {phase === "verify" && bothReal ? (
            <div className="alert alert--ok" role="status" style={{ marginBottom: "1rem" }}>
              <strong>Codes bhej diye gaye.</strong>{" "}
              {delivery.smsToFixedVerified
                ? `SMS Twilio verified number par gaya${phoneMasked ? ` (${phoneMasked})` : ""} — wahi inbox check karein. Email OTP Gmail par.`
                : "SMS aapke mobile par aur email OTP Gmail inbox mein aana chahiye — thori der wait karke SMS + Gmail check karein (Spam / Promotions folder bhi)."}
            </div>
          ) : null}

          {phase === "verify" && !bothReal && verifyHint ? (
            <div className="alert alert--info" role="status">
              {verifyHint}
            </div>
          ) : null}

          {showDemoPanel ? (
            <div className="otp-strip-outer" style={{ marginBottom: "1rem" }}>
              {demoSmsOtp ? (
                <div className="otp-strip otp-strip--demo" role="status" aria-live="polite">
                  <p className="otp-strip-label">SMS (demo / fallback only)</p>
                  <div className="otp-strip-digits" aria-label="SMS demo code">
                    {demoSmsOtp.split("").map((ch, i) => (
                      <span key={i} className="otp-digit">
                        {ch}
                      </span>
                    ))}
                  </div>
                  <p className="otp-strip-note">
                    Asli mobile par SMS ke liye Twilio sahi ho aur DEBUG par Twilio fail na ho. Trial par number
                    verify karein.
                  </p>
                </div>
              ) : null}
              {demoEmailOtp ? (
                <div
                  className="otp-strip otp-strip--demo"
                  style={{ marginTop: demoSmsOtp ? "0.75rem" : 0 }}
                  role="status"
                  aria-live="polite"
                >
                  <p className="otp-strip-label">Email (demo / fallback only)</p>
                  <div className="otp-strip-digits" aria-label="Email demo code">
                    {demoEmailOtp.split("").map((ch, i) => (
                      <span key={i} className="otp-digit">
                        {ch}
                      </span>
                    ))}
                  </div>
                  <p className="otp-strip-note">
                    Gmail par asli mail ke liye .env mein BREVO_SMTP_LOGIN + BREVO_SMTP_KEY + verified sender.
                  </p>
                </div>
              ) : null}
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
                <span>Email (Gmail OTP yahan aayega)</span>
                <input
                  className="input"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@gmail.com"
                  required
                />
              </label>
              <label className="field">
                <span>Mobile number (profile / identity)</span>
                <input
                  className="input"
                  type="tel"
                  autoComplete="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+923001234567"
                  required
                />
                <span className="field-hint" style={{ fontSize: "0.85rem", color: "var(--muted, #64748b)" }}>
                  Twilio trial: SMS OTP server par set Twilio-verified number par jata hai; yahan woh number likho jo
                  account profile mein save hona chahiye.
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
                {busy ? "Sending codes…" : "Continue — get verification codes"}
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
                <span>SMS code (mobile par jo aaya)</span>
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
                <span>Email code (Gmail / inbox)</span>
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
