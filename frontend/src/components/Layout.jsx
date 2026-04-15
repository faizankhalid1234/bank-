import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth.jsx";

export function Layout() {
  const { isAuthenticated, logout } = useAuth();
  const [theme, setTheme] = useState(() => {
    const t = localStorage.getItem("alybank-theme");
    if (t === "dark" || t === "light") return t;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("alybank-theme", theme);
  }, [theme]);

  // PWA / iOS / tab: install + home screen icon (public/pwa-*.png)
  useEffect(() => {
    const base = import.meta.env.BASE_URL || "/";
    const href = `${base.replace(/\/?$/, "/")}pwa-192.png`;

    let apple = document.querySelector('link[rel="apple-touch-icon"]');
    if (!apple) {
      apple = document.createElement("link");
      apple.rel = "apple-touch-icon";
      apple.sizes = "192x192";
      document.head.appendChild(apple);
    }
    apple.href = href;

    let fav = document.querySelector('link[rel="icon"][data-alybank-icon="1"]');
    if (!fav) {
      fav = document.createElement("link");
      fav.rel = "icon";
      fav.type = "image/png";
      fav.setAttribute("data-alybank-icon", "1");
      document.head.appendChild(fav);
    }
    fav.href = href;
  }, []);

  const location = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [location.pathname]);

  return (
    <div className="page-root">
      <div className="shell shell--stretch">
        <header className="topbar">
          <Link to="/" className="brand">
            <span className="brand-mark" aria-hidden="true">
              A
            </span>
            <span>AlyBank</span>
          </Link>
          <nav className="nav" aria-label="Main">
            {isAuthenticated ? (
              <>
                <NavLink
                  to="/dashboard"
                  className={({ isActive }) => (isActive ? "active" : undefined)}
                >
                  Dashboard
                </NavLink>
                <NavLink to="/pay" className={({ isActive }) => (isActive ? "active" : undefined)}>
                  Pay
                </NavLink>
                <NavLink
                  to="/history"
                  className={({ isActive }) => (isActive ? "active" : undefined)}
                >
                  Activity
                </NavLink>
                <button type="button" className="link" onClick={() => logout()}>
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link to="/login">Sign in</Link>
                <Link to="/register" className="nav-open-account">
                  Open account
                </Link>
              </>
            )}
            <button
              type="button"
              className="theme-toggle"
              aria-label="Toggle color theme"
              onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
            >
              <span aria-hidden="true">{theme === "dark" ? "☾" : "☀"}</span>
              <span>{theme === "dark" ? "Dark" : "Light"}</span>
            </button>
          </nav>
        </header>

        <main className="main-area">
          <Outlet />
        </main>
      </div>

      <footer className="site-footer">
        <div className="site-footer-inner">
          <div className="site-footer-brand">
            <Link to="/" className="site-footer-logo">
              <span className="brand-mark" aria-hidden="true">
                A
              </span>
              <span>AlyBank</span>
            </Link>
            <p className="site-footer-tagline">Banking that feels effortless</p>
            <p className="site-footer-disclaimer">
              Demo banking UI — not a real financial institution.
            </p>
          </div>
          <div className="site-footer-col">
            <h3 className="site-footer-heading">Product</h3>
            <ul className="site-footer-links">
              <li>
                <Link to="/">Home</Link>
              </li>
              <li>
                <a href="/#product">Features</a>
              </li>
              <li>
                <Link to="/register">Open account</Link>
              </li>
              <li>
                <Link to="/login">Log in</Link>
              </li>
              {isAuthenticated && (
                <>
                  <li>
                    <Link to="/dashboard">Dashboard</Link>
                  </li>
                  <li>
                    <Link to="/pay">Payments</Link>
                  </li>
                </>
              )}
            </ul>
          </div>
          <div className="site-footer-col">
            <h3 className="site-footer-heading">Contact</h3>
            <ul className="site-footer-contact">
              <li>
                <span className="site-footer-contact-label">Name</span> Faizan Khalid
              </li>
              <li>
                <span className="site-footer-contact-label">Email</span>{" "}
                <a href="mailto:fk5095129@gmail.com">fk5095129@gmail.com</a>
              </li>
              <li>
                <span className="site-footer-contact-label">Phone</span>{" "}
                <a href="tel:+923029655325">+92 302 9655325</a>
              </li>
            </ul>
          </div>
          <div className="site-footer-col">
            <h3 className="site-footer-heading">Connect</h3>
            <ul className="site-footer-links site-footer-links--social">
              <li>
                <a
                  href="https://github.com/faizankhalid1234"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  GitHub
                </a>
              </li>
              <li>
                <a
                  href="https://portfolio-faizan-topaz.vercel.app/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Portfolio
                </a>
              </li>
              <li>
                <a
                  href="https://www.linkedin.com/in/faizan-khalid-developerp/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  LinkedIn
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="site-footer-bar">
          <span>© {new Date().getFullYear()} AlyBank · Built for portfolio demo</span>
        </div>
      </footer>
    </div>
  );
}
