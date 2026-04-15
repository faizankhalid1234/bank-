import { Link } from "react-router-dom";

export function LandingPage() {
  return (
    <div className="landing-stack">
      <section className="landing-hero" id="landing-hero" aria-label="Introduction">
        <div className="landing-hero-grid">
          <div className="landing-hero-copy">
            <p className="landing-eyebrow">React + Django</p>
            <h1 className="landing-hero-title">
              Banking that feels calm, clear, and in your control.
            </h1>
            <p className="landing-hero-lead">
              <strong>AlyBank</strong> is a portfolio playground: IBAN transfers, activity history,
              and a polished glass UI — fork it, run locally, and experiment.{" "}
              <strong>Not a licensed institution; no real money.</strong>
            </p>
            <ul className="landing-tags" aria-label="Stack">
              <li>Open source</li>
              <li>Django</li>
              <li>SQLite</li>
              <li>React</li>
              <li>REST API</li>
            </ul>
            <div className="landing-hero-cta">
              <Link className="landing-btn landing-btn--primary" to="/register">
                Get started free
              </Link>
              <Link className="landing-btn landing-btn--outline" to="/login">
                I already have an account
              </Link>
            </div>
            <div className="landing-hero-foot">
              <a
                href="https://github.com/faizankhalid1234"
                target="_blank"
                rel="noopener noreferrer"
              >
                Star &amp; fork on GitHub ↗
              </a>
              <a
                href="https://portfolio-faizan-topaz.vercel.app/"
                target="_blank"
                rel="noopener noreferrer"
              >
                Live portfolio →
              </a>
            </div>
          </div>
          <div className="landing-hero-visual">
            <div className="landing-wallet" aria-hidden="true">
              <div className="landing-wallet-glow" />
              <div className="landing-wallet-inner">
                <div className="landing-wallet-head">
                  <span className="landing-wallet-brand">AlyBank wallet</span>
                  <span className="landing-wallet-grid-ico">▦</span>
                </div>
                <p className="landing-wallet-bal">PKR ●●●●●●●●</p>
                <p className="landing-wallet-hint">Sign in to see your demo balance.</p>
                <div className="landing-wallet-card">
                  <div className="landing-wallet-card-top">
                    <span>Virtual card</span>
                    <span className="landing-wallet-active">Active</span>
                  </div>
                  <p className="landing-wallet-pan">●●●● ●●●● ●●●● 4242</p>
                  <p className="landing-wallet-card-foot">Demo pay — all in the app</p>
                </div>
                <div className="landing-wallet-pills">
                  <span>REST</span>
                  <span>IBAN</span>
                  <span>CSV-ready</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="feature-band" id="product">
        <div className="feature-band-inner">
          <h2 className="feature-band-title">Why it feels lovely</h2>
          <p className="feature-band-lead">
            Soft gradients, glass surfaces, and motion that respects your eyes — built to feel like
            a real product, not a tutorial page.
          </p>
          <div className="feature-grid">
            <article className="feature-card">
              <h3>Glass &amp; glow</h3>
              <p>Layered surfaces with subtle depth so screens feel tactile, not flat.</p>
            </article>
            <article className="feature-card">
              <h3>Dark-first comfort</h3>
              <p>Toggle light/dark anytime; typography stays crisp in both themes.</p>
            </article>
            <article className="feature-card">
              <h3>Real flows</h3>
              <p>
                Pay, receipts, activity — wired to Django sessions and SQLite. Ledger credits/debits
                are staff-only in admin.
              </p>
            </article>
          </div>
        </div>
      </section>
    </div>
  );
}
