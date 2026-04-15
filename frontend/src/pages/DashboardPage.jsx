import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export function DashboardPage() {
  const { user, account } = useAuth();
  const [revealed, setRevealed] = useState(false);
  const displayName = user?.first_name?.trim() || user?.username || "there";

  return (
    <div className="dash-page">
      <div className="dash-shell">
        <section className="dash-hero" aria-label="Welcome">
          <div className="dash-hero-copy">
            <p className="dash-hero-eyebrow">Signed in</p>
            <h1 className="dash-hero-title">
              Hello, {displayName} — banking that feels{" "}
              <span className="dash-hero-em">calm, clear, and in your control.</span>
            </h1>
            <p className="dash-hero-lead">
              This is a <strong>portfolio demo</strong>: send payments to other AlyBank accounts,
              view activity and receipts. Account top-ups and debits are done by{" "}
              <strong>staff in Django admin</strong> — not from here.
            </p>
            <ul className="dash-hero-tags" aria-label="Stack">
              <li>Django</li>
              <li>SQLite</li>
              <li>React</li>
              <li>Session auth</li>
              <li>PKR demo</li>
            </ul>
            <div className="dash-hero-cta">
              <Link className="dash-hero-btn dash-hero-btn--primary" to="/pay">
                Send payment
              </Link>
              <Link className="dash-hero-btn dash-hero-btn--outline" to="/history">
                View activity
              </Link>
            </div>
          </div>
          <div className="dash-hero-card-wrap">
            <button
              type="button"
              className="dash-wallet dash-wallet--hero"
              onClick={() => setRevealed((v) => !v)}
              aria-pressed={revealed}
              aria-label="Tap to show or hide balance"
            >
              <div className="dash-wallet-mesh" aria-hidden="true" />
              <div className="dash-wallet-shine" aria-hidden="true" />
              <div className="dash-wallet-inner dash-wallet-inner--hero">
                <div className="dash-hero-wallet-head">
                  <span className="dash-wallet-brand dash-wallet-brand--hero">AlyBank wallet</span>
                  <span className="dash-hero-wallet-grid" aria-hidden="true">
                    ▦
                  </span>
                </div>
                <div className="dash-hero-wallet-balance">
                  <p className="dash-hero-wallet-balance-label">Available</p>
                  <div className="dash-wallet-line dash-wallet-line--hero">
                    {revealed ? (
                      <span className="dash-wallet-amt dash-wallet-amt--hero">
                        <span className="dash-wallet-pkr--prefix">PKR</span> {account?.balance}
                      </span>
                    ) : (
                      <span className="dash-wallet-mask dash-wallet-mask--hero">
                        <span className="dash-wallet-pkr--prefix">PKR</span> ●●●●●●●●
                      </span>
                    )}
                  </div>
                  <p className="dash-hero-wallet-hint">
                    Tap the card to {revealed ? "hide" : "reveal"} your balance.
                  </p>
                </div>
                <div className="dash-wallet-inset">
                  <div className="dash-wallet-inset-top">
                    <span className="dash-wallet-inset-title">Virtual card</span>
                    <span className="dash-wallet-inset-badge">Active</span>
                  </div>
                  <p className="dash-wallet-inset-pan" aria-hidden="true">
                    ●●●● ●●●● ●●●● {account?.account_number?.slice(-4) || "••••"}
                  </p>
                  <p className="dash-wallet-inset-meta">Demo limits · freeze · pay</p>
                </div>
                <div className="dash-hero-wallet-pills" aria-hidden="true">
                  <span>REST</span>
                  <span>IBAN</span>
                  <span>Receipts</span>
                </div>
              </div>
            </button>
          </div>
        </section>

        <div className="dash-grid dash-grid--triple">
          <section className="dash-panel dash-panel--lift">
            <h2 className="dash-panel-title">Account</h2>
            <dl className="dash-dl">
              <div className="dash-dl-row">
                <dt>Account number</dt>
                <dd>{account?.account_number}</dd>
              </div>
              <div className="dash-dl-row">
                <dt>IBAN</dt>
                <dd className="mono">{account?.iban}</dd>
              </div>
              <div className="dash-dl-row">
                <dt>Balance</dt>
                <dd>
                  <strong>PKR {account?.balance}</strong>
                </dd>
              </div>
            </dl>
            <p className="dash-panel-lead" style={{ marginTop: "0.75rem" }}>
              Credits and debits on your balance are posted by administrators in Django admin —
              customers cannot add money to their own account from this app.
            </p>
          </section>

          <section className="dash-panel dash-panel--lift">
            <h2 className="dash-panel-title">Transfers</h2>
            <p className="dash-panel-lead">Send PKR to another AlyBank account or IBAN.</p>
            <div className="dash-actions">
              <Link className="dash-hero-btn dash-hero-btn--primary" to="/pay">
                Send payment
              </Link>
            </div>
          </section>

          <section className="dash-panel dash-panel--lift">
            <h2 className="dash-panel-title">Activity</h2>
            <p className="dash-panel-lead">Browse every movement, or filter saved receipts.</p>
            <div className="dash-actions">
              <Link className="dash-hero-btn dash-hero-btn--primary" to="/history">
                Open activity
              </Link>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
