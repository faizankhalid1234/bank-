const API_PREFIX = "/api";

const _fromEnv =
  typeof import.meta.env.VITE_DJANGO_URL === "string"
    ? import.meta.env.VITE_DJANGO_URL.trim().replace(/\/$/, "")
    : "";
if (!_fromEnv) {
  throw new Error(
    "VITE_DJANGO_URL is missing. Set it in frontend/.env, .env.development, or .env.production (see .env.example), or in Vercel → Environment Variables."
  );
}
const API_ORIGIN = _fromEnv;

/** Debug / errors — Django API origin (no trailing slash); same as VITE_DJANGO_URL at build time. */
export const RAILWAY_API_BASE = API_ORIGIN;

const TOKEN_KEY = "alybank_auth_token";

function errNetworkFailed(what, url) {
  return (
    `${what} — URL open nahi ho saki: ${url} | API base: ${API_ORIGIN}. ` +
    `Build/dev: .env mein VITE_DJANGO_URL (see .env.example). ` +
    `Vercel: Environment Variables → VITE_DJANGO_URL. ` +
    `Local Django: VITE_DJANGO_URL=http://127.0.0.1:8000`
  );
}

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
  const csrfUrl = `${API_ORIGIN}${API_PREFIX}/csrf/`;
  let r;
  try {
    r = await fetch(csrfUrl, { credentials: "include", mode: "cors" });
  } catch {
    throw new Error(errNetworkFailed("CSRF fetch fail", csrfUrl));
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
  const fullUrl = `${API_ORIGIN}${API_PREFIX}${path}`;
  try {
    r = await fetch(fullUrl, {
      ...options,
      credentials: "include",
      mode: "cors",
      headers,
    });
  } catch {
    throw new Error(errNetworkFailed("API request fail", fullUrl));
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
