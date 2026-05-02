const API_PREFIX = "/api";

/** Set VITE_DJANGO_URL at build time (e.g. Railway backend) so API calls work from any frontend host. */
const API_ORIGIN = (
  typeof import.meta.env.VITE_DJANGO_URL === "string"
    ? import.meta.env.VITE_DJANGO_URL.trim().replace(/\/$/, "")
    : ""
);

const TOKEN_KEY = "alybank_auth_token";

let csrfToken = null;

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function parseJsonSafe(text) {
  const t = (text || "").trim();
  if (!t) return null;
  try {
    return JSON.parse(t);
  } catch {
    return null;
  }
}

/** Prefer field errors (e.g. login password) over generic detail. */
function errorMessageFromResponse(data) {
  if (!data) return "Request failed";
  if (typeof data.detail === "string" && data.detail) {
    const errs = data.errors;
    if (errs && typeof errs === "object" && !Array.isArray(errs)) {
      const pick = (key) => {
        const v = errs[key];
        if (Array.isArray(v) && v.length && typeof v[0] === "string") return v[0];
        if (typeof v === "string") return v;
        return null;
      };
      for (const key of [
        "password",
        "identifier",
        "email",
        "username",
        "non_field_errors",
        "__all__",
      ]) {
        const m = pick(key);
        if (m) return m;
      }
      for (const key of Object.keys(errs)) {
        const m = pick(key);
        if (m) return m;
      }
    }
    return data.detail;
  }
  if (Array.isArray(data.detail) && data.detail[0]) return data.detail[0];
  if (typeof data.message === "string") return data.message;
  return "Request failed";
}

export async function ensureCsrf() {
  let r;
  try {
    r = await fetch(`${API_ORIGIN}${API_PREFIX}/csrf/`, { credentials: "include" });
  } catch {
    throw new Error(
      "Server tak pohnch nahi saka — backend (Railway) reachable hai? VITE_DJANGO_URL check karein; local Django ke liye .env mein http://127.0.0.1:8000 set karein."
    );
  }
  const text = await r.text();
  const j = parseJsonSafe(text);
  if (!r.ok) {
    const detail =
      (j && typeof j.detail === "string" && j.detail) ||
      (j && Array.isArray(j.detail) && j.detail[0]) ||
      text?.slice(0, 200) ||
      `HTTP ${r.status}`;
    throw new Error(detail);
  }
  if (!j || typeof j.csrfToken !== "string") {
    throw new Error(
      "CSRF token nahi mila — API ne JSON nahi bheja. Backend URL / CORS / cookies check karein (VITE_DJANGO_URL)."
    );
  }
  csrfToken = j.csrfToken;
  return csrfToken;
}

async function apiFetch(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const t = getAuthToken();
  if (t) {
    headers.Authorization = `Token ${t}`;
  }
  const method = (options.method || "GET").toUpperCase();
  if (method !== "GET" && method !== "HEAD") {
    const csrf = csrfToken || (await ensureCsrf());
    headers["X-CSRFToken"] = csrf;
  }
  let r;
  try {
    r = await fetch(`${API_ORIGIN}${API_PREFIX}${path}`, {
      ...options,
      credentials: "include",
      headers,
    });
  } catch {
    throw new Error(
      "Network error — API backend nahi mil raha. VITE_DJANGO_URL (Railway) sahi hai? Alag frontend domain par CORS backend par set karein."
    );
  }
  const text = await r.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text };
  }
  if (!r.ok) {
    const msg = errorMessageFromResponse(data);
    const err = new Error(msg);
    err.status = r.status;
    err.data = data;
    throw err;
  }
  return data;
}

export const api = {
  get(path) {
    return apiFetch(path, { method: "GET" });
  },
  post(path, body) {
    return apiFetch(path, {
      method: "POST",
      body: body !== undefined ? JSON.stringify(body) : "{}",
    });
  },
};
